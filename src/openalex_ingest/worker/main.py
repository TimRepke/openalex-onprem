import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Annotated

import typer

from nacsos_data.util.academic.apis import APIEnum

from openalex_ingest.shared.apis import APIWrapper
from openalex_ingest.shared.crud import (
    update_default_sources,
    get_queued_requested_for_source,
    drop_finished_from_queue,
    drop_unforced_sources_from_queued,
    drop_source_from_queued,
)
from openalex_ingest.shared.db import DatabaseEngine
from openalex_ingest.shared.models import OnConflict, SourcePriority
from openalex_ingest.shared.util import prepare_runner


class MaxRuntimeException(Exception):
    pass


def source_worker(
    db_engine: DatabaseEngine,
    source: APIEnum | str,
    batch_size: int,
    min_abstract_len: int,
    auth_key: str,
    logger: logging.Logger,
    oldest_first: bool,
    created_before: datetime | None = None,
    created_after: datetime | None = None,
) -> int:
    logger.info(f'Attempting to fetch {batch_size} entries in the queue for source {source}...')
    queued = list(
        get_queued_requested_for_source(
            db_engine=db_engine,
            source=source,
            limit=batch_size,
            oldest_first=oldest_first,
            created_after=created_after,
            created_before=created_before,
        ),
    )
    logger.info(f'Working on {len(queued)} queued requests for source {source}')
    filtered_queue = [
        entry
        for entry in queued
        if (
            # force run for this source
            (entry.priority == SourcePriority.FORCE)
            # don't check existing results, just work the queue entry (again) and add another request row
            or (entry.on_conflict == OnConflict.FORCE)
            # when we already asked for this DOI but have no abstract -> retry
            or (entry.on_conflict == OnConflict.RETRY_ABSTRACT and entry.num_has_abstract == 0)
            # when we already asked for this DOI but have no raw payload -> retry
            or (entry.on_conflict == OnConflict.RETRY_RAW and entry.num_has_source_raw == 0)
            # when we already asked for this DOI anywhere, don't try again
            or (entry.on_conflict == OnConflict.DO_NOTHING and entry.num_has_source_request == 0)
        )
    ]
    # on_conflict=<OnConflict.DO_NOTHING: 2> priority=<SourcePriority.TRY: 2> num_has_request=1 num_has_abstract=0 num_has_title=1 num_has_raw=1 num_has_source_request=1 num_has_source_abstract=0 num_has_source_title=1 num_has_source_raw=1
    logger.info(f'Filtered queue down to {len(filtered_queue)} entries')

    ids_found_abstract = set()

    if len(filtered_queue) > 0:
        # 1) Query API wrapper
        # 2) Insert into request table
        # 3) append queue_id in one of the two lists
        logger.info(f'First eligible entry was queued on {queued[0].time_created}')
        wrapper = APIWrapper(wrapper=source, db_engine=db_engine, auth_key=auth_key, logger=logger)

        with db_engine.session() as session:
            for request in wrapper.fetch(queries=filtered_queue):
                if len(request.abstract or '') < min_abstract_len:
                    request.abstract = None
                if request.abstract is not None and request.queue_id is not None:
                    ids_found_abstract.add(request.queue_id)
                session.add(request)
            session.commit()

    ids_missing_abstract = list({q.queue_id for q in queued} - ids_found_abstract)
    ids_found_abstract = list(ids_found_abstract)

    logger.info(f'Dropping all unforced sources from current queue entries where we found an abstract: {ids_found_abstract}')
    drop_unforced_sources_from_queued(db_engine=db_engine, queue_ids=ids_found_abstract)

    logger.info(f'Dropping {source} from current queue entries where we did not find an abstract: {ids_missing_abstract}')
    drop_source_from_queued(db_engine=db_engine, source=source, queue_ids=ids_missing_abstract)

    logger.info('Dropping finished queue entries...')
    drop_finished_from_queue(db_engine=db_engine)
    return len(queued)


def main(
    config: Annotated[Path, typer.Option(help='Path to config file')],
    max_runtime: Annotated[int, typer.Option(help='Number of seconds for this script to run before stopping')] = 5 * 60,
    sources: Annotated[list[str] | None, typer.Option(help='Sources to include')] = None,
    batch_size: Annotated[int, typer.Option(help='Number of queue entries per source per loop')] = 25,
    min_abstract_len: Annotated[int, typer.Option(help='Minimum length before we accept something to be an abstract')] = 25,
    oldest_first: Annotated[bool, typer.Option('--oldest-first/--latest-first', help='Decide which way to order the queue')] = False,
    created_after: Annotated[datetime | None, typer.Option(help='Filter queue to entries added after this date')] = None,
    created_before: Annotated[datetime | None, typer.Option(help='Filter queue to entries added before this date')] = None,
    loglevel: Annotated[str, typer.Option(help='Log verbosity')] = 'INFO',
):
    logger, settings, db_engine = prepare_runner(config=config, loglevel=loglevel, logger_name='queue-runner', run_log_init=True)
    start_time = datetime.now()
    delta = timedelta(seconds=max_runtime)
    end_time = start_time + delta
    if sources is None or len(sources) == 0:
        sources = [APIEnum.DIMENSIONS.value, APIEnum.SCOPUS.value, APIEnum.PUBMED.value, APIEnum.WOS.value]

    logger.info('Replace empty source fields with default order...')
    update_default_sources(db_engine=db_engine)
    n_loops = 0
    n_processed = 1
    while n_processed > 0 and end_time > datetime.now():
        n_loops += 1
        n_processed = 0

        for source in sources:
            logger.info(f'Processing source {source} in loop {n_loops}; will run until {end_time} (now: {datetime.now()})')
            if end_time < datetime.now():
                logger.info(f'  -> Reached maximum runtime of {delta}!')
                break

            try:
                n_processed += source_worker(
                    db_engine=db_engine,
                    source=source,
                    batch_size=batch_size,
                    logger=logger,
                    min_abstract_len=min_abstract_len,
                    auth_key=settings.CACHE_AUTH_KEY,
                    oldest_first=oldest_first,
                    created_after=created_after,
                    created_before=created_before,
                )
            except Exception as e:
                logger.error(e)
                logger.exception(e)

    logger.info(f'Finished work after processing for {max_runtime} with {n_processed} processed in the last loop!')


if __name__ == '__main__':
    typer.run(main)
