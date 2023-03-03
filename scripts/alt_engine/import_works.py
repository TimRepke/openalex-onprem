import csv
import json
import time
import datetime
import logging
import subprocess

logging.basicConfig(format='%(asctime)s [%(levelname)s] %(name)s: %(message)s', level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

SOURCE_DIR = '/usr/local/apsis/slowhome/rept'
COLLECTION = 'openalex'


def get_chunks():
    with open(f'{SOURCE_DIR}/works.csv') as csvfile:
        csvreader = csv.DictReader(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        docs = []
        for i, row in enumerate(csvreader):
            row['ta'] = f"{row['title']} {row['abstract']}"
            docs.append(row)
            if (i % 1000000) == 0 and i > 0:
                yield docs
                docs = []
        yield docs


def write_chunk(chunk, docs):
    tf = f'{SOURCE_DIR}/chunks/works_{chunk:04}.json'
    logger.info(f'Writing chunk file to {tf}')
    with open(tf, 'w') as fout:
        json.dump(docs, fout)
    logger.debug('Wrote chunk.')
    return tf


if __name__ == '__main__':
    logger.info(f'Importing works table (batched) from `works.csv` in {SOURCE_DIR}')

    t0 = time.time()
    for ci, data in enumerate(get_chunks()):
        t1 = time.time()
        chunk_file = write_chunk(ci, data)
        logger.info('POST chunk to solr')
        t2 = time.time()
        cmd = f'solr/bin/post -c {COLLECTION} {chunk_file}'
        process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()
        logger.debug(output)
        logger.error(error)
        logger.info(f'  POST took {datetime.timedelta(seconds=time.time() - t2)}h '
                    f'| chunk overall: {datetime.timedelta(seconds=time.time() - t1)}h '
                    f'| total runtime: {datetime.timedelta(seconds=time.time() - t0)}h ')


# {!surround} ((climate 3n (mitigation OR change)) AND policy) 5N "threat varies"
# 5N(AND(3N(climate, OR(mitigation, change)), policy), "threat varies")
# {!surround} 5N(3N(climate, OR(mitigation, change)), "threat varies")
# {!surround} abstract:(climate 3N (mitigation OR change)) 5N "threat varies"
# title:{!surround} 2W(OR(climate, OR (change, mitigation)), OR("developing countries", "Mitigation Policies"))
# (climate AND (mitigation OR change)) 5W ("developing countries" OR "Mitigation Policies")
# {!surround} (climate 2W (mitigation OR change)) 5W  "developing countries" OR "Mitigation Policies"
