import re
import logging
from datetime import datetime

import typer
import httpx
from typing_extensions import Annotated

from meta_cache.handlers.db import get_engine
from meta_cache.handlers.util import update_solr_abstracts
from processors.solr_daily.structs import FIELDS_TO_FETCH, WorkOut, Work
from processors.solr_daily.transform import transform_work
from shared.util import rate_limit

app = typer.Typer()


def date_check(value: str) -> str:
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', value):
        raise typer.BadParameter('Only Camila is allowed')
    return value


def request_meta_cache(url: str, meta_key: str, buffer: list[WorkOut], wrapper: str | None = None):
    orig_size = len(buffer)
    buffer = [
        work
        for work in buffer
        if (int(work.id is not None) + int(work.pmid is not None) + int(work.doi is not None)) > 1
    ]
    logging.info(f'Submitting {len(buffer)} of {orig_size} works with missing abstract to meta-cache')
    try:
        res = httpx.post(url,
                         headers={'x-auth-key': meta_key},
                         json={
                             'references': [{
                                 'openalex_id': work.id,
                                 'doi': work.doi[16:] if work.doi else None,
                                 'pubmed_id': str(work.pmid) if work.pmid else None,
                             }
                                 for work in buffer
                             ],
                             'limit': len(buffer) * 4,
                             'wrapper': wrapper,
                             'fetch_on_missing_abstract': True,
                             'fetch_on_missing_entry': True,
                             'update_links': True,
                             'empty_abstract_as_missing': True,
                         },
                         timeout=120)
        res.raise_for_status()
        info = res.json()
        logging.info(f'Hits: {info["n_hits"]}, updates: {info["n_updated"]}, '
                     f'queued: {info["n_queued"]}, missed: {info["n_missed"]}, added: {info["n_added"]}')
    except httpx.HTTPError as e:
        logging.error(f'Failed to submit {url}: {e}')
        logging.warning(e.response.text)
        logging.exception(e)


def commit_solr(url: str, buffer: list[str]):
    try:
        res = httpx.post(url=url,
                         timeout=120,
                         headers={'Content-Type': 'application/json'},
                         data='\n'.join(buffer))
        res.raise_for_status()
    except httpx.HTTPError as e:
        logging.error(f'Failed to submit {url}: {e}')
        logging.exception(e)


@app.command()
def update_solr(api_key: Annotated[str, typer.Option(help='OpenAlex premium API key')],
                meta_key: Annotated[str, typer.Option(help='meta-cache API key')],
                meta_host: Annotated[str, typer.Option(help='meta-cache base url')],
                solr_host: Annotated[str, typer.Option(help='Solr base url')],
                solr_collection: Annotated[str, typer.Option(help='Name of the Solr collection')],
                created_since: Annotated[str, typer.Option(callback=date_check, help='Get works created on or after')],
                oa_page_size: int = 200,
                solr_buffer_size: int = 200,
                meta_buffer_size: int = 25,
                wrapper: str = 'scopus',
                loglevel: str = 'INFO'):
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(name)s (%(process)d): %(message)s', level=loglevel)

    solr_url = f'{solr_host}/api/collections/{solr_collection}/update/json?commit=true'
    meta_url = f'{meta_host}/api/lookup'

    meta_cache_buffer = []
    solr_buffer = []

    cursor = '*'
    n_pages = 0
    n_works = 0
    n_cache_works = 0
    while cursor is not None:
        n_pages += 1
        with rate_limit(min_time_ms=100) as t:
            # https://docs.openalex.org/api-entities/works/filter-works#from_created_date
            # --> https://api.openalex.org/works?filter=from_created_date:2023-01-12&api_key=myapikey
            # from_updated_date
            # from_created_date
            # header api_key
            page = httpx.get(
                'https://api.openalex.org/works',
                timeout=120,
                params={
                    'filter': f'from_created_date:{created_since}',
                    'select': ','.join(FIELDS_TO_FETCH),
                    'cursor': cursor,
                    'per-page': oa_page_size
                },
                headers={'api_key': api_key},
            ).json()
            cursor = page['meta']['next_cursor']
            logging.info(f'Retrieved {n_works:,} / {page['meta']['count']:,} '
                         f'| currently on page {n_pages:,} '
                         f'| {n_cache_works:,} works sent to cache')

            for raw_work in page['results']:
                n_works += 1
                work = transform_work(Work.model_validate(raw_work))
                solr_buffer.append(work.model_dump_json(exclude_unset=True, exclude_none=True))

                if work.abstract is None:
                    meta_cache_buffer.append(work)

                if len(solr_buffer) >= solr_buffer_size:
                    logging.info(f'Committing buffer of {len(solr_buffer)} works to solr')
                    commit_solr(url=solr_url, buffer=solr_buffer)
                    solr_buffer = []

                if len(meta_cache_buffer) >= meta_buffer_size:
                    n_cache_works += len(meta_cache_buffer)
                    request_meta_cache(url=meta_url, meta_key=meta_key, buffer=meta_cache_buffer, wrapper=wrapper)
                    meta_cache_buffer = []

    if len(solr_buffer) > 0:
        logging.info(f'Committing buffer of {len(solr_buffer)} works to solr')
        commit_solr(url=solr_url, buffer=solr_buffer)

    if len(meta_cache_buffer) > 0:
        request_meta_cache(url=meta_url, meta_key=meta_key, buffer=meta_cache_buffer, wrapper=wrapper)

    logging.info('Solr collection is up to date.')


@app.command()
def backfill_abstracts(solr_host: Annotated[str, typer.Option(help='Solr base url')],
                       solr_collection: Annotated[str, typer.Option(help='Name of the Solr collection')],
                       conf_file: Annotated[str, typer.Option(help='Path to configuration .env file')],
                       created_since: Annotated[str, typer.Option(callback=date_check,
                                                                  help='Get works created on or after')],
                       batch_size: int = 200,
                       loglevel: str = 'INFO'):
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(name)s (%(process)d): %(message)s', level=loglevel)

    logging.info(f'Connecting to database.')
    db_engine = get_engine(conf_file=conf_file)

    logging.info(f'Starting backfill of abstracts.')
    update_solr_abstracts(
        db_engine=db_engine,
        solr_host=solr_host,
        solr_collection=solr_collection,
        from_time=datetime.strptime(created_since, '%Y-%m-%d'),
        batch_size=batch_size,
    )
    logging.info(f'Finished backfill of abstracts.')


if __name__ == '__main__':
    app()
