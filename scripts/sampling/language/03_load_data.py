import re
from pathlib import Path
from engine import engine
from sqlalchemy import text
import logging

logging.basicConfig(format='%(asctime)s [%(levelname)s] %(name)s: %(message)s', level='DEBUG')
logger = logging.getLogger()

SOURCE = Path('../data/lang/langs.tsv')
SOURCE = SOURCE.resolve()

logger.info(f'Reading from directory {SOURCE}')

with open(SOURCE, 'r') as fin:
    with engine.connect() as conn:
        stmt = text('UPDATE openalex.works_all SET lang = :lang WHERE id = :wid;')
        cnt = 0
        for line in fin:
            s = line.split('\t')

            conn.execute(stmt, {'wid': s[0], 'lang': s[1]})
            cnt += 1

            if (cnt % 10000) == 0:
                logger.debug(f'Updated {cnt:,} records, committing!')
                conn.commit()

        logger.info('final commit')
        conn.commit()

# with open(SOURCE, 'r') as fin:
#     with engine.connect() as conn:
#         stmt = text('UPDATE openalex.works_all SET language = :lang WHERE id = :wid;')
#         batch_i = 0
#         batch = []
#         for line in fin:
#             if len(batch) > 10000:
#                 logger.debug(f'Uploading batch {batch_i}')
#                 conn.execute(stmt, batch)
#                 logger.debug(f'Uploaded batch {batch_i}')
#                 batch = []
#                 batch_i += 1
#             s = line.split('\t')
#             batch.append({'wid': s[0], 'lang': s[1]})
#
#         logger.debug(f'Uploading final batch')
#         conn.execute(stmt, batch)

logger.info('All done!')
