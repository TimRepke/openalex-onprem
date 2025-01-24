import json
import logging
import subprocess
import tempfile

import typer
from sqlmodel import select

from meta_cache.handlers.schema import Record
from meta_cache.scripts.config import db_engine_cache, settings

logger = logging.getLogger('copy')


def main(batch_size: int = 100):
    with db_engine_cache.engine.connect() as connection:
        stmt = select(Record).where(Record.openalex_id != None,
                                    Record.abstract != None,
                                    Record.title != None)
        with connection.execution_options(yield_per=batch_size).execute(stmt) as result:
            for pi, partition in enumerate(result.partitions(batch_size)):
                logger.debug(f'Received partition {pi} from nacsos.')
                with tempfile.NamedTemporaryFile(mode='w', delete_on_close=False) as fp:
                    logger.debug(f'Writing partition data to {fp.name}')
                    for record in partition:
                        rec = {
                            'id': record.openalex_id,
                            'title': record.title,
                            'abstract': record.abstract,
                            'title_abstract': f'{record.title} {record.abstract}',
                        }
                        if record.doi:
                            rec['doi'] = f'https://https://doi.org/{record.doi}'
                        fp.write(json.dumps(rec) + '\n')
                    fp.flush()

                    res = subprocess.run([
                        'curl',
                        '-X', 'POST',
                        (f'{settings.OA_SOLR_HOST}'
                         f'/api/collections/{settings.OA_SOLR_COLLECTION}/update/json?commit=true'),
                        '-H', 'Content-type:application/json',
                        # '--silent',
                        '-T', str(fp.name)])
                    logging.info(f'Partition posted to solr via {res}')


if __name__ == "__main__":
    typer.run(main)
