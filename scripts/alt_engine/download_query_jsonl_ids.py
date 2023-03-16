import json
import logging
import requests
from time import time
from pathlib import Path
from datetime import timedelta

q = """
({!surround v="(carbon OR emission? OR CO2 OR GHG) 2N (price? OR pricing OR tax OR taxes OR taxation OR trading OR trade OR tradable OR levy OR levies OR allowance? OR market)"}
OR cap-and-trade OR climate-change-levy)
AND NOT
({!surround v="(carbon OR emission? OR CO2 OR GHG) 2N (price? OR pricing OR tax OR taxes OR taxation OR trading OR trade OR tradable OR levy OR levies OR allowance? OR market)"}
OR "cap-and-trade" OR "climate-change-levy")
"""

logging.basicConfig(format='%(asctime)s [%(levelname)s] %(name)s: %(message)s', level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

export_fields = [
    'id'
]

BATCH_SIZE = 10000
TARGET_FILE = Path('/home/tim/workspace/nacsos-academic-search/data/niklas_ids.jsonl')
TARGET_FILE.parent.mkdir(exist_ok=True, parents=True)

url = 'http://10.10.13.46:8983/solr/openalex/select'
data = {
    'q': q,
    'q.op': 'AND',
    'df': 'ta',
    'sort': 'id desc',
    'fl': ','.join(export_fields),
    'rows': BATCH_SIZE,
    'cursorMark': '*'
}

logger.info(f'Querying endpoint with batch_size={BATCH_SIZE:,}: {url}')
logger.info(f'Writing results to: {TARGET_FILE}')

with open(TARGET_FILE, 'w') as f_out:
    t0 = time()

    batch_i = 0
    num_docs_cum = 0
    while True:
        t1 = time()
        batch_i += 1
        logger.info(f'Running query for batch {batch_i} with cursor "{data["cursorMark"]}"')
        t2 = time()
        res = requests.post(url, data=data).json()
        data['cursorMark'] = res['nextCursorMark']
        n_docs_total = res['response']['numFound']
        batch_docs = res['response']['docs']
        n_docs_batch = len(batch_docs)
        num_docs_cum += n_docs_batch

        logger.debug(f'Query took {timedelta(seconds=time() - t2)}h and yielded {n_docs_batch:,} docs')
        logger.debug(f'Current progress: {num_docs_cum:,}/{n_docs_total:,}={num_docs_cum / n_docs_total:.2%} docs')

        if len(batch_docs) == 0:
            logger.info('No documents in this batch, assuming to be done!')
            break

        logger.debug('Writing documents to file...')
        [f_out.write(json.dumps(doc) + '\n') for doc in batch_docs]

        logger.debug(f'Done with batch {batch_i} in {timedelta(seconds=time() - t1)}h; '
                     f'{timedelta(seconds=time() - t0)}h passed overall')
