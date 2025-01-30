import json
import logging

import httpx
import typer
from tqdm import tqdm
from sqlmodel import select

from meta_cache.handlers.schema import Record
from meta_cache.scripts.config import db_engine_cache, settings

logging.getLogger('httpcore').setLevel(logging.INFO)
logger = logging.getLogger('copy')


def main(batch_size: int = 100):
    with db_engine_cache.engine.connect() as connection:
        stmt = select(Record).where(Record.openalex_id != None,
                                    Record.abstract != None,
                                    Record.title != None)
        with connection.execution_options(yield_per=batch_size).execute(stmt) as result:
            for pi, partition in tqdm(enumerate(result.partitions(batch_size))):
                logger.debug(f'Received partition {pi} from nacsos.')
                partition = list(partition)
                logging.debug(f'Asking solr for which IDs are missing abstracts...')
                res = httpx.get(f'{settings.OA_SOLR_HOST}'
                                f'/api/collections/{settings.OA_SOLR_COLLECTION}/select',
                                params={
                                    'q': '-abstract:*',  # -abstract:[* TO ""]
                                    'fq': f'id:({' OR '.join([record.openalex_id for record in partition])})',
                                    'fl': 'id',
                                    'q.op': 'AND',
                                    'rows': batch_size,
                                    'useParams': '',
                                    'defType': 'lucene'
                                }).json()

                needs_update = set([doc['id'] for doc in res['response']['docs']])
                logger.info(f'Partition with {len(partition):,} records '
                            f'has {len(needs_update):,} missing abstracts in solr')

                if len(needs_update) <= 0:
                    logging.info(f'Partition skipped, seems complete')
                    continue

                buffer = ''
                for record in partition:
                    if record.openalex_id not in needs_update:
                        continue

                    rec = {
                        'id': record.openalex_id,
                        'title': record.title,
                        'abstract': record.abstract,
                        'title_abstract': f'{record.title} {record.abstract}',
                        'external_abstract': True,
                    }
                    if record.doi:
                        rec['doi'] = f'https://https://doi.org/{record.doi}'
                    buffer += json.dumps(rec) + '\n'

                res = httpx.post((f'{settings.OA_SOLR_HOST}'
                                  f'/api/collections/{settings.OA_SOLR_COLLECTION}/update/json?commit=true'),
                                 headers={'Content-Type': 'application/json'},
                                 data=buffer)

                logging.info(f'Partition posted to solr via {res}')


if __name__ == "__main__":
    typer.run(main)
