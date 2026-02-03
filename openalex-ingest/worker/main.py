from datetime import datetime, timedelta
from pathlib import Path
from typing import Annotated

import typer

from nacsos_data.util.academic.apis import APIEnum

from shared.crud import (
    update_default_sources,
    get_queued_requested_for_source,
    drop_finished_from_queue,
    drop_unforced_sources_from_queued,
    drop_source_from_queued,
)
from shared.db import get_engine
from shared.models import OnConflict, SourcePriority
from shared.util import get_logger
from shared.config import load_settings


class MaxRuntimeException(Exception):
    pass


def main(
    config: Annotated[Path, typer.Option(help='Path to config file')],
    max_runtime: Annotated[int, typer.Option(help='Number of seconds for this script to run before stopping')] = 5 * 60,
    sources: Annotated[list[str] | None, typer.Option(help='Sources to include')] = None,
    batch_size: Annotated[int, typer.Option(help='Number of queue entries per source per loop')] = 25,
    loglevel: Annotated[str, typer.Option(help='Log verbosity')] = 'INFO',
):
    logger = get_logger('queue-worker', loglevel=loglevel, run_init=True)

    start_time = datetime.now()
    delta = timedelta(seconds=max_runtime)
    if sources is None or len(sources) == 0:
        sources = [APIEnum.DIMENSIONS.value, APIEnum.SCOPUS.value, APIEnum.PUBMED.value, APIEnum.WOS.value]

    logger.info(f'Loading config from {config.resolve()}...')
    if not config.exists():
        raise AssertionError(f'Config file does not exist at {config.resolve()}!')
    settings = load_settings(config)

    logger.info('Connecting to database...')
    db_engine = get_engine(settings=settings.CACHE_DB)

    logger.info('Replace empty source fields with default order...')
    update_default_sources(db_engine=db_engine)
    n_loops = 0
    try:
        while True:
            n_loops += 1
            try:
                for source in sources:
                    time_passed = datetime.now() - start_time
                    logger.info(f'Processing source {source}  in loop {n_loops}; runtime so far: {time_passed}')
                    if time_passed > delta:
                        logger.info(f'  -> Reached maximum runtime of {delta}!')
                        raise MaxRuntimeException()

                    queued = list(get_queued_requested_for_source(db_engine=db_engine, source=source, limit=batch_size))

                    ids_found_abstract = []
                    ids_missing_abstract = []
                    for entry in queued:
                        logger.debug(entry.info_str)
                        if (
                            # force run for this source
                            (entry.priority == SourcePriority.FORCE.value)
                            # don't check existing results, just work the queue entry (again) and add another request row
                            or (entry.on_conflict == OnConflict.FORCE.value)
                            # when we already asked for this DOI but have no abstract -> retry
                            or (entry.on_conflict == OnConflict.RETRY_ABSTRACT.value and entry.num_has_abstract == 0)
                            # when we already asked for this DOI but have no raw payload -> retry
                            or (entry.on_conflict == OnConflict.RETRY_RAW.value and entry.num_has_source_raw == 0)
                            # when we already asked for this DOI anywhere, don't try again
                            or (entry.on_conflict == OnConflict.DO_NOTHING.value and entry.num_has_source_request == 0)
                        ):
                            pass
                            # use wrapper to check for abstract
                            # insert into request table
                            # append queue_id in one of the two lists

                    logger.info('Dropping all unforced sources from current queue entries where we found an abstract...')
                    drop_unforced_sources_from_queued(db_engine=db_engine, queue_ids=ids_found_abstract)

                    logger.info(f'Dropping {source} from current queue entries where we did not find an abstract...')
                    drop_source_from_queued(db_engine=db_engine, source=source, queue_ids=ids_missing_abstract)

                    logger.info('Dropping finished queue entries...')
                    drop_finished_from_queue(db_engine=db_engine)

            except Exception as e:
                if type(e) is MaxRuntimeException:
                    raise e
                logger.error(e)
                logger.exception(e)

        logger.info('Finished work, nothing more to do!')
    except MaxRuntimeException:
        logger.info('Finished work after reaching maximum runtime!')


if __name__ == '__main__':
    typer.run(main)
