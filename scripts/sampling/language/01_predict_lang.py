import re
from pathlib import Path
import fasttext
from engine import engine
from sqlalchemy import text
import logging

logging.basicConfig(format='%(asctime)s [%(levelname)s] %(name)s: %(message)s', level='DEBUG')
logger = logging.getLogger()

model = fasttext.load_model('sampling/language/lid.176.bin')

TARGET = Path('../data/lang/')
TARGET = TARGET.resolve()

logger.info(f'Writing to directory {TARGET}')
if TARGET.exists():
    raise RuntimeError('Directory already exists.')
TARGET.mkdir(parents=True, exist_ok=True)

BATCH = 100000
MAX = 220000000
BATCHES = int(MAX / BATCH)
rg = re.compile(r'\n')


def transform_prediction(p):
    return p[0][0][9:], p[1][0], p[0][-1][9:], p[1][-1]


def predict_lang_slow(records):
    langs = []
    errors = 0
    empty = 0
    for work in records:
        try:
            if work[1] is None:
                empty += 1
            else:
                langs.append((work[0],
                              transform_prediction(model.predict(rg.sub(' ', work[1]), k=2))))
        except Exception as e:
            print(f'  > Error on record {work}: {e}')
            errors += 1
    logger.debug(f'  > Slow batch processing saw {empty} titles and {errors} errors.')
    return langs


def predict_lang_fast(records):
    try:
        langs = [(work[0],
                  transform_prediction(model.predict(rg.sub(' ', work[1]), k=2)))
                 for work in records
                 if work[1] is not None]
        logger.debug(f'  > Batch had {len(records) - len(langs):,} empty titles; processed without errors.')
    except Exception:
        print(f'  > Error! looping one by one...')
        return predict_lang_slow(records)
    return langs


with open(TARGET / 'langs.tsv', 'w') as out:
    with engine.connect() as conn:
        logger.info('Submitting query and fetching cursor...')
        stmt = text('SELECT id, title FROM openalex.works_all;')
        with conn.execution_options(stream_results=True, max_row_buffer=BATCH).execute(stmt) as result:
            logger.debug(f'Received a cursor, proceeding to iterate...')
            batch_i = 0
            for partition in result.partitions(BATCH):
                logger.debug(f'[BATCH {batch_i}] Received batch (~{batch_i / BATCHES:.4%} done) ...')
                logger.debug(f'  > Predicting language on records by title...')
                langs = predict_lang_fast(partition)

                logger.debug(f'  > Dumping predictions to file...')
                [
                    out.write(f'{w[0]}\t{w[1][0]}\t{w[1][1]:.3f}\t{w[1][2]}\t{w[1][3]:.3f}\n')
                    for w in langs
                ]
                logger.info(f'  > Done!')
                batch_i += 1
