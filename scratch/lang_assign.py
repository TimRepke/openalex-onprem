import re
from collections import Counter
from pathlib import Path
import fasttext
from engine import smkr
from sqlalchemy import text

model = fasttext.load_model('lid.176.bin')
TARGET = Path('../data/languages.tsv')
TARGET = TARGET.resolve()
TARGET.parent.mkdir(parents=True, exist_ok=True)

if TARGET.exists():
    raise RuntimeError('File already exists.')

BATCH = 100000
MAX = 220000000
rg = re.compile(r'\n')
with smkr() as session, open(TARGET, 'w') as out:
    out.write('id\tlang_1\tscore_lang_1\tlang_2\tscore_lang_2\n')
    for b in range(0, MAX, BATCH):
        stmt = text('SELECT id, title FROM openalex.works_all OFFSET :start LIMIT :batch;')
        res = session.execute(stmt, {'start': b, 'batch': BATCH})
        works = res.mappings().all()
        stats = []
        empty = 0
        for work in works:
            try:
                if work['title'] is None:
                    out.write(f'{work["id"]}\ten\t1.0\ten\t1.0\n')
                    empty += 1
                else:
                    p = model.predict(rg.sub(' ', work['title']), k=2)
                    out.write(f'{work["id"]}\t{p[0][0][9:]}\t{p[1][0]}\t{p[0][-1][9:]}\t{p[1][-1]}\n')
                    stats.append(p[0][0][9:])
            except Exception as e:
                print(f'Error in batch {b} on record {work}')
                print(e)
        print(f'{b:,} (empty:{empty:,})', Counter(stats).most_common(4))

# language codes (ISO 639-3):
# https://en.wikipedia.org/wiki/Wikipedia:WikiProject_Languages/List_of_ISO_639-3_language_codes_(2019)
