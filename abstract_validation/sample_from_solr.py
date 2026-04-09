# reservoir_sample_solr.py
import requests
import random
import json
from pathlib import Path
from time import time
import logging

logger = logging.getLogger(__name__)

# ---------------- CONFIG ----------------
SOLR_URL = "http://localhost:8983/solr/openalex/select"  # Replace with your Solr URL
ROWS = 1000000       # Number of rows per batch (adjust for memory/performance)
K = 1000000        # Number of random IDs to sample
FIELDS = "id"      # Field to retrieve
QUERY = "*:*"      # Base query
#QUERY = 'title:"carbon dioxide removal"'
SEED = 123456
OUT_PATH = "/mnt/bulk/openalex/random_ids.txt"
# ----------------------------------------

def main():
    logging.basicConfig(filename="abstract_validation/solr_sample.log")

    start_time = time()
    reservoir = []
    cursor_mark = "*"
    total_processed = 0

    random.seed(SEED)

    while True:
        payload = {
            "q": QUERY,
            "fl": FIELDS,
            "rows": ROWS,
            "cursorMark": cursor_mark,
            "sort": "id asc"
        }

        response = requests.post(
            SOLR_URL,
            data=payload
        )
        response.raise_for_status()
        data = response.json()
        docs = data["response"]["docs"]
        next_cursor = data.get("nextCursorMark")

        if not docs:
            break
    
        for doc in docs:
            total_processed += 1
            doc_id = doc["id"]

            if len(reservoir) < K:
                reservoir.append(doc_id)
            else:
                s = random.randint(1, total_processed)
                if s <=K:
                    replace_index = random.randint(0, K - 1)
                    reservoir[replace_index] = doc_id

        logger.info(
            f"processed {total_processed} documents"
            f" {time() - start_time} seconds elapsed"
        )
        
        if next_cursor == cursor_mark:
            break
        cursor_mark = next_cursor

    with Path(OUT_PATH).open("w") as f:
        for id_ in reservoir:
            f.write(f"{id_}\n")
    


if __name__ == "__main__":
    main()
