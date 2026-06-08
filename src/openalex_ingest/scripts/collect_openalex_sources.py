import requests
import time
import json
import os
from typing import Optional, Dict, Any, List

BASE = "https://api.openalex.org/sources"
SELECT_FIELDS = ",".join([
    "ids",
    "display_name",
    "host_organization",
    "host_organization_name",
    "host_organization_lineage",
])
PER_PAGE = 200  # OpenAlex max
# assumes script will be executed on project root, adjust if not
OUTPUT_DIR = "data/openalex_sources"
CHUNK_SIZE = 1000
MAX_RETRIES = 5
BACKOFF_FACTOR = 1.5
API_KEY = os.getenv("NACSOS_OPENALEX__API_KEY") 
STATE_FILE = os.path.join(OUTPUT_DIR, "state.json")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_state() -> Dict[str, Any]:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_cursor": None, "chunk_index": 0, "fetched": 0}

def save_state(state: Dict[str, Any]) -> None:
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f)
    os.replace(tmp, STATE_FILE)

def build_params(cursor: Optional[str]) -> Dict[str, str]:
    params = {
        "select": SELECT_FIELDS,
        "per-page": str(PER_PAGE),
    }
    if cursor:
        params["cursor"] = cursor
    return params

def request_page(cursor: Optional[str]) -> Dict[str, Any]:
    headers = {}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    params = build_params(cursor)
    attempt = 0
    while True:
        try:
            start = time.perf_counter()
            resp = requests.get(BASE, params=params, headers=headers, timeout=30)
            elapsed = time.perf_counter() - start
            if resp.status_code >= 500:
                raise requests.HTTPError(f"Server error: {resp.status_code}")
            resp.raise_for_status()
            print(f"Request time: {elapsed:.2f}s (cursor: {cursor})")
            return resp.json()
        except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
            attempt += 1
            if attempt > MAX_RETRIES:
                raise
            backoff = (BACKOFF_FACTOR ** attempt)
            print(f"Request failed (attempt {attempt}): {e}. Backing off {backoff:.1f}s")
            time.sleep(backoff)

def write_chunk(chunk_records: List[Dict[str, Any]], chunk_index: int) -> None:
    path = os.path.join(OUTPUT_DIR, f"chunk_{chunk_index:05d}.jsonl")
    tmp = path + ".tmp"
    with open(tmp, "a", encoding="utf-8") as f:
        for r in chunk_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, path)

def main():
    total_start = time.perf_counter()
    state = load_state()
    cursor = state.get("last_cursor")
    chunk_index = state.get("chunk_index", 0)
    fetched = state.get("fetched", 0)
    buffer: List[Dict] = []

    if not cursor:
        j = request_page("*")
        meta = j.get("meta", {})
        total = meta.get("total_results")
        if total is not None:
            print(f"Total sources (approx): {total}")
        results = j.get("results", [])
        buffer.extend(results)
        next_cursor = meta.get("next_cursor")
        cursor = next_cursor
        fetched += len(results)
        print(f"Fetched initial page: {len(results)} (total fetched: {fetched})")

    while True:
        if len(buffer) >= CHUNK_SIZE:
            chunk_start = time.perf_counter()
            write_chunk(buffer[:CHUNK_SIZE], chunk_index)
            chunk_elapsed = time.perf_counter() - chunk_start
            buffer = buffer[CHUNK_SIZE:]
            chunk_index += 1
            state.update({"last_cursor": cursor, "chunk_index": chunk_index, "fetched": fetched})
            save_state(state)
            print(f"Wrote chunk {chunk_index-1} ({CHUNK_SIZE} records) in {chunk_elapsed:.2f}s — total fetched: {fetched}")

        if not cursor:
            break

        try:
            page_start = time.perf_counter()
            j = request_page(cursor)
            page_elapsed = time.perf_counter() - page_start
        except Exception as e:
            state.update({"last_cursor": cursor, "chunk_index": chunk_index, "fetched": fetched})
            save_state(state)
            print(f"Error after fetching {fetched} records. State saved. Cursor: {cursor}")
            raise

        results = j.get("results", [])
        meta = j.get("meta", {})
        next_cursor = meta.get("next_cursor")

        buffer.extend(results)
        fetched += len(results)
        cursor = next_cursor
        print(f"Fetched page: {len(results)} records in {page_elapsed:.2f}s (total fetched: {fetched}), next_cursor: {bool(cursor)}")

        if not cursor:
            while len(buffer) >= CHUNK_SIZE:
                cstart = time.perf_counter()
                write_chunk(buffer[:CHUNK_SIZE], chunk_index)
                celapsed = time.perf_counter() - cstart
                buffer = buffer[CHUNK_SIZE:]
                chunk_index += 1
                state.update({"last_cursor": cursor, "chunk_index": chunk_index, "fetched": fetched})
                save_state(state)
                print(f"Wrote chunk {chunk_index-1} ({CHUNK_SIZE} records) in {celapsed:.2f}s")
            if buffer:
                cstart = time.perf_counter()
                write_chunk(buffer, chunk_index)
                celapsed = time.perf_counter() - cstart
                chunk_index += 1
                buffer = []
                print(f"Wrote final chunk {chunk_index-1} ({len(buffer)} records) in {celapsed:.2f}s")
            state.update({"last_cursor": None, "chunk_index": chunk_index, "fetched": fetched})
            save_state(state)
            total_elapsed = time.perf_counter() - total_start
            print(f"Completed. Total fetched: {fetched}. Final chunk index: {chunk_index}. Total elapsed: {total_elapsed:.2f}s")
            #       Completed. Total fetched: 283281.    Final chunk index: 284.           Total elapsed: 928.23s
            break

    print("Done.")

if __name__ == "__main__":
    main()
