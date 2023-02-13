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
        stmt = text('UPDATE openalex.works_all SET lang = v.vlang '
                    'FROM ('
                    '  SELECT unnest(array[:wids]) as wid,'
                    '         unnest(array[:langs]) as vlang'
                    ') AS v '
                    'WHERE id = v.wid AND lang is null;')
        cnt = 0
        acc_wid = []
        acc_lang = []
        for line in fin:
            s = line.split('\t')
            acc_wid.append(s[0])
            acc_lang.append(s[1])

            cnt += 1

            if (cnt % 10000) == 0:
                logger.debug(f'Read {len(acc_wid):,} lines, pushing to DB!')
                conn.execute(stmt, {'wids': acc_wid, 'langs': acc_lang})
                conn.commit()
                logger.debug(f'Updated {cnt:,} records so far!')
                acc_wid = []
                acc_lang = []

        logger.info('final commit')
        logger.debug(f'Have {len(acc_wid):,} lines left, pushing to DB!')
        conn.execute(stmt, {'wids': acc_wid, 'langs': acc_lang})
        conn.commit()
        logger.debug(f'Updated {cnt:,} records so far!')

logger.info('All done!')
