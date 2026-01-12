import logging
from datetime import datetime
from typing import Annotated

import typer

from meta_cache.handlers.db import get_engine
from meta_cache.handlers.util import update_solr_abstracts

logging.getLogger('httpcore').setLevel(logging.INFO)
logger = logging.getLogger('copy')


def main(solr_host: Annotated[str, typer.Option(help='Solr base url')],
         solr_collection: Annotated[str, typer.Option(help='Name of the Solr collection')],
         conf_file: Annotated[str, typer.Option(help='Path to configuration .env file')],
         created_since: Annotated[str | None, typer.Option(help='Get works created on or after')] = None,
         batch_size: int = 200,
         loglevel: str = 'INFO'):
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(name)s (%(process)d): %(message)s', level=loglevel)

    logging.info(f'Connecting to database.')
    db_engine = get_engine(conf_file=conf_file)

    logging.info(f'Starting backfill of abstracts.')
    update_solr_abstracts(
        db_engine=db_engine,
        solr_host=solr_host,
        solr_collection=solr_collection,
        from_time=datetime.strptime(created_since, '%Y-%m-%d') if created_since is not None else None,
        batch_size=batch_size,
    )

    # with db_engine_cache.engine.connect() as connection:
    #     stmt = select(Record).where(Record.openalex_id != None,
    #                                 Record.abstract != None,
    #                                 Record.title != None)
    #     with connection.execution_options(yield_per=batch_size).execute(stmt) as result:
    #         for pi, partition in tqdm(enumerate(result.partitions(batch_size))):
    #             logger.debug(f'Received partition {pi} from nacsos.')
    #             n_updated, n_skipped = post2solr(records=list(partition),
    #                                              solr_host=settings.OA_SOLR_HOST,
    #                                              collection=settings.OA_SOLR_COLLECTION)
    #             logger.debug(f'Updated {n_updated} and skipped {n_skipped} records.')


if __name__ == "__main__":
    typer.run(main)
