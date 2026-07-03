import requests
import time
import json
import os
import logging
import sys
import pandas as pd
from typing import Optional, Dict, Any, List
from pathlib import Path

logger = logging.getLogger('copy')
logger.setLevel(logging.DEBUG)

if not logger.handlers:  # avoid duplicate handlers on re-import
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

BASE = 'https://api.openalex.org/sources'
SELECT_FIELDS = ','.join(
    [
        'ids',
        'display_name',
        'host_organization',
        'host_organization_name',
        'host_organization_lineage',
    ]
)
PER_PAGE = 200  # OpenAlex max
# assumes script will be executed on project root, adjust if not
OUTPUT_DIR = Path('data/openalex_sources/tmp2')
CHUNK_SIZE = 5000
MAX_RETRIES = 5
BACKOFF_FACTOR = 1.5
API_KEY = os.getenv('NACSOS_OPENALEX__API_KEY')
STATE_FILE = OUTPUT_DIR / 'state.json'

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_state() -> Dict[str, Any]:
    if STATE_FILE.exists():
        with STATE_FILE.open('r', encoding='utf-8') as f:
            return json.load(f)
    return {'last_cursor': None, 'chunk_index': 0, 'fetched': 0}


def save_state(state: Dict[str, Any]) -> None:
    tmp = STATE_FILE.with_suffix(STATE_FILE.suffix + '.tmp')
    with tmp.open('w', encoding='utf-8') as f:
        json.dump(state, f)
    tmp.replace(STATE_FILE)


def build_params(cursor: Optional[str]) -> Dict[str, str]:
    params = {
        'select': SELECT_FIELDS,
        'per-page': str(PER_PAGE),
    }
    if cursor:
        params['cursor'] = cursor
    return params


def request_page(cursor: Optional[str]) -> Dict[str, Any]:
    headers = {}
    if API_KEY:
        headers['Authorization'] = f'Bearer {API_KEY}'
    params = build_params(cursor)
    attempt = 0
    while True:
        try:
            start = time.perf_counter()
            resp = requests.get(BASE, params=params, headers=headers, timeout=30)
            elapsed = time.perf_counter() - start
            if resp.status_code >= 500:
                raise requests.HTTPError(f'Server error: {resp.status_code}')
            resp.raise_for_status()
            logger.info(f'Request time: {elapsed:.2f}s (cursor: {cursor})')
            return resp.json()
        except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
            attempt += 1
            if attempt > MAX_RETRIES:
                raise
            backoff = BACKOFF_FACTOR**attempt
            logger.error(f'Request failed (attempt {attempt}): {e}. Backing off {backoff:.1f}s')
            time.sleep(backoff)


def write_chunk(chunk_records: List[Dict[str, Any]], chunk_index: int) -> None:
    path = OUTPUT_DIR / f'chunk_{chunk_index:05d}.jsonl'
    tmp = path.with_suffix(path.suffix + '.tmp')
    with tmp.open('a', encoding='utf-8') as f:
        for r in chunk_records:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    tmp.replace(path)


def clean_data(oa: pd.DataFrame) -> pd.DataFrame:
    # replace empty lists with None
    oa.id_issn = oa.id_issn.apply(lambda x: None if (x is None or len(x) == 0) else x)
    oa.host_organization_lineage = oa.host_organization_lineage.apply(lambda x: None if (x is None or len(x) == 0) else x)
    # remove rows that don't have ISSN, because that's how we match to citation indexes
    logger.info(f'OpenAlex sources df shape before removing sources without ISSNs: {oa.shape}')
    oa = oa.dropna(subset='id_issn_l')
    # deduplicate with keeping last row, which is also the most recent
    logger.info(f'OpenAlex sources df shape after removing sources without ISSNs & before deduplication: {oa.shape}')
    oa = oa.groupby('id_issn_l').last().reset_index()
    logger.info(f'OpenAlex sources df shape after deduplication: {oa.shape}')
    return oa


def combine_chunks() -> None:
    output_dir = OUTPUT_DIR
    chunks = [fp for fp in output_dir.rglob('*') if fp.suffix == '.jsonl']
    df = pd.read_json(chunks[0], lines=True, orient='records')

    for chunk in chunks[1:]:
        tmp = pd.read_json(chunk, lines=True, orient='records')
        df = pd.concat([df, tmp], axis=0)

    df = clean_data(df)

    out_path = output_dir.parent / f'oa_sources_{time.strftime("%Y-%m-%d")}.json'
    df.to_json(out_path, index=False, orient='records')


def main():
    total_start = time.perf_counter()
    state = load_state()
    cursor = state.get('last_cursor')
    chunk_index = state.get('chunk_index', 0)
    fetched = state.get('fetched', 0)
    buffer: List[Dict] = []

    if not cursor:
        j = request_page('*')
        meta = j.get('meta', {})
        total = meta.get('total_results')
        if total is not None:
            logger.info(f'Total sources (approx): {total}')
        results = j.get('results', [])
        for r in results:
            ids = r.get('ids', {})
            for key, value in ids.items():
                r[f'id_{key}'] = value
            r.pop('ids', None)
        buffer.extend(results)
        next_cursor = meta.get('next_cursor')
        cursor = next_cursor
        fetched += len(results)
        logger.info(f'Fetched initial page: {len(results)} (total fetched: {fetched})')

    while True:
        if len(buffer) >= CHUNK_SIZE:
            chunk_start = time.perf_counter()
            write_chunk(buffer[:CHUNK_SIZE], chunk_index)
            chunk_elapsed = time.perf_counter() - chunk_start
            buffer = buffer[CHUNK_SIZE:]
            chunk_index += 1
            state.update({'last_cursor': cursor, 'chunk_index': chunk_index, 'fetched': fetched})
            save_state(state)
            logger.info(f'Wrote chunk {chunk_index - 1} ({CHUNK_SIZE} records) in {chunk_elapsed:.2f}s — total fetched: {fetched}')

        if not cursor:
            break

        try:
            page_start = time.perf_counter()
            j = request_page(cursor)
            page_elapsed = time.perf_counter() - page_start
        except Exception as e:
            state.update({'last_cursor': cursor, 'chunk_index': chunk_index, 'fetched': fetched})
            save_state(state)
            logger.error(f'Error after fetching {fetched} records. State saved. Cursor: {cursor}')
            raise

        results = j.get('results', [])
        for r in results:
            ids = r.get('ids', {})
            for key, value in ids.items():
                r[f'id_{key}'] = value
            r.pop('ids', None)
        meta = j.get('meta', {})
        next_cursor = meta.get('next_cursor')

        buffer.extend(results)
        fetched += len(results)
        cursor = next_cursor
        logger.info(f'Fetched page: {len(results)} records in {page_elapsed:.2f}s (total fetched: {fetched}), next_cursor: {bool(cursor)}')

        if not cursor:
            while len(buffer) >= CHUNK_SIZE:
                cstart = time.perf_counter()
                write_chunk(buffer[:CHUNK_SIZE], chunk_index)
                celapsed = time.perf_counter() - cstart
                buffer = buffer[CHUNK_SIZE:]
                chunk_index += 1
                state.update({'last_cursor': cursor, 'chunk_index': chunk_index, 'fetched': fetched})
                save_state(state)
                logger.info(f'Wrote chunk {chunk_index - 1} ({CHUNK_SIZE} records) in {celapsed:.2f}s')
            if buffer:
                cstart = time.perf_counter()
                write_chunk(buffer, chunk_index)
                celapsed = time.perf_counter() - cstart
                chunk_index += 1
                buffer = []
                logger.info(f'Wrote final chunk {chunk_index - 1} ({len(buffer)} records) in {celapsed:.2f}s')
            state.update({'last_cursor': None, 'chunk_index': chunk_index, 'fetched': fetched})
            save_state(state)
            total_elapsed = time.perf_counter() - total_start
            logger.info(f'Completed. Total fetched: {fetched}. Final chunk index: {chunk_index}. Total elapsed: {total_elapsed:.2f}s')
            #       Completed. Total fetched: 283522.    Final chunk index: 57.            Total elapsed: 977.71s
            break

    logger.info('API calls are done, rewriting into a single file...')
    combine_chunks()
    logger.info('Done')


if __name__ == '__main__':
    main()
