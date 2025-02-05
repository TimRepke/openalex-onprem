import logging

import typer
from tqdm import tqdm
from sqlmodel import select

from meta_cache.handlers.schema import Record
from meta_cache.handlers.util import post2solr
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
                n_updated, n_skipped = post2solr(records=list(partition),
                                                 solr_host=settings.OA_SOLR_HOST,
                                                 collection=settings.OA_SOLR_COLLECTION)
                logger.debug(f'Updated {n_updated} and skipped {n_skipped} records.')


if __name__ == "__main__":
    typer.run(main)
