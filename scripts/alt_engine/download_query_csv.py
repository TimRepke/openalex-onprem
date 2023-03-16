import csv
import logging
import requests
from time import time
from pathlib import Path
from datetime import timedelta

q = """
(
     household OR
     households OR
     householding OR
     householder OR
     householders OR
     residential OR
     building OR
     dormitory OR
     dormitories OR
     individual OR
     consumer OR
     consumers OR
     participant OR
     participants OR
     customer OR
     customers OR
     domestic OR
     homeowners OR
     homeowner OR
     homeownership
   ) AND
   (
     feedback OR
     price OR
     prices OR
     pricing OR
     priced OR
     pricelist
     "time-of-use" OR
     "time-of-day" OR
     "real time" OR
     "real-time" OR
     "peak" OR
     "dynamic pricing" OR
     "smart meter" OR
     "smart meters" OR
     "smart metering" OR
     "smart grid" OR
     "smart grids" OR
     "behavioral economic" OR
     "behavioral economics" OR
     "behavioral economical" OR
     "behavioral intervention" OR
     "behavioral interventions" OR
     "behavioral interventional" OR
     "behavioral guideline" OR
     "behavioral guidelines" OR
     "behaviorally economic" OR
     "behaviorally economics" OR
     "behaviorally economical" OR
     "behaviorally intervention" OR
     "behaviorally interventions" OR
     "behaviorally interventional" OR
     "behaviorally guideline" OR
     "behaviorally guidelines" OR
     "behavioural economic" OR
     "behavioural economics" OR
     "behavioural economical" OR
     "behavioural intervention" OR
     "behavioural interventions" OR
     "behavioural interventional" OR
     "behavioural guideline" OR
     "behavioural guidelines" OR
     "behaviourally economic" OR
     "behaviourally economics" OR
     "behaviourally economical" OR
     "behaviourally intervention" OR
     "behaviourally interventions" OR
     "behaviourally interventional" OR
     "behaviourally guideline" OR
     "behaviourally guidelines" OR
     nudge OR
     nudges OR
     "choice architecture" OR
     norm OR
     norms OR
     "normative" OR
     "social influence" OR
     "block leader" OR
     "public commitment" OR
     "social comparison" OR
     "social learning" OR
     "social modeling" OR
     "peer comparison" OR
     "peer information" OR
     salience OR
     "commitment device" OR
     "commitment devices" OR
     "pre-commitment" OR
     "precommitment" OR
     pledge OR
     "behavioral contract" OR
     "behavioural contract" OR
     "commitment contract" OR
     "commitment approach" OR
     "commitment approaches" OR
     "personal commitment" OR
     audit OR
     rebate OR
     reward OR
     incentives OR
     "goal setting" OR
     "home energy report" OR
     "in-home display" OR
     "information provision"~3 OR
     "information strategies"~3 OR
     "information acquisition"~3 OR
     "information system"~3 OR
     "information systems"~3 OR
     "information campaign"~3 OR
     "information campaigns"~3 OR
     "information campaigning"~3 OR
     "information campaigner"~3 OR
     "information campaigners"~3 OR
     "information intervention"~3 OR
     "information interventions"~3 OR
     "information interventional"~3 OR
     "foot-in-the-door" OR
     "minimal justification" OR
     "applied game" OR
     "applied games" OR
     "applied gamer" OR
     "applied gamers" OR
     "applied gameplay" OR
     "serious game" OR
     "serious games" OR
     "serious gamer" OR
     "serious gamers" OR
     "serious gameplay" OR
     gamif* OR
     "dissonance" OR
     tariff OR
     "time-varying pricing"
   ) AND
   (
     {!surround v="
         (
           energy OR
           electric OR
           electrical OR
           electricity OR
           electrically OR
           electrician OR
           electronic OR
           electronics OR
           gas
         ) 15W
         (
           consumption OR
           conservation OR
           efficiency OR
           use OR
           demand OR
           usage
         )
     "} OR
     "price responsiveness"
   )
"""

logging.basicConfig(format='%(asctime)s [%(levelname)s] %(name)s: %(message)s', level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

export_fields = [
    'id', 'title', 'abstract', 'mag',
    'publication_year', 'cited_by_count', 'type', 'doi'
]

BATCH_SIZE = 10000
TARGET_FILE = Path('/home/tim/workspace/nacsos-academic-search/data/lsr.csv')
TARGET_FILE.parent.mkdir(exist_ok=True, parents=True)

url = 'http://10.10.13.46:8983/solr/openalex/select'
data = {
    'q': q,
    'df': 'ta',
    'sort': 'id desc',
    'fl': ','.join(export_fields),
    'rows': BATCH_SIZE,
    'cursorMark': '*'
}

logger.info(f'Querying endpoint with batch_size={BATCH_SIZE:,}: {url}')
logger.info(f'Writing results to: {TARGET_FILE}')

with open(TARGET_FILE, 'w', newline='') as f_out:
    writer = csv.DictWriter(f_out, fieldnames=export_fields, quoting=csv.QUOTE_ALL, dialect='unix')
    writer.writeheader()

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
        writer.writerows(batch_docs)

        logger.debug(f'Done with batch {batch_i} in {timedelta(seconds=time() - t1)}h; '
                     f'{timedelta(seconds=time() - t0)}h passed overall')
