import logging
from datetime import datetime
from itertools import batched
from pathlib import Path
from typing import Annotated, Iterable

import typer
from nacsos_data.db import DatabaseEngine
from nacsos_data.util.academic.apis import APIEnum
from sqlalchemy import text

from openalex_ingest.shared.models import OnConflict, SourcePriority
from openalex_ingest.shared.schema import Request, Queue
from openalex_ingest.shared.solr import write_cache_records_to_solr, get_entries_with_missing_abstracts
from openalex_ingest.shared.util import prepare_runner, parse_sources

app = typer.Typer()


@app.command('transfer', short_help='Write abstract from cache to solr')
def transfer_abstracts(
    config: Annotated[Path, typer.Option(help='Path to config file')],
    batch_size: Annotated[int, typer.Option(help='Batch size')] = 200,
    force_overwrite: Annotated[bool, typer.Option(help="Use this flag to overwrite existing abstracts in solr, otherwise we'll check first")] = False,
    created_after: Annotated[datetime | None, typer.Option(help='Filter queue to entries added after this date')] = None,
    created_before: Annotated[datetime | None, typer.Option(help='Filter queue to entries added before this date')] = None,
    loglevel: Annotated[str, typer.Option(help='Log level')] = 'INFO',
) -> None:
    """This method iterates through all entries in the meta-cache that have an abstract and are not yet written to solr to do just that.

    1) Fetch records from `request` table that have an abstract where `solarized = False`
    2) Construct update query (abstract_source, abstract_date, abstract)
    3) Submit to solr
    4) Update solarized flag on success
    """
    logger, settings, db_engine = prepare_runner(config=config, loglevel=loglevel, logger_name='abstract-transfer', run_log_init=True)

    creation_filter = ''
    if created_before is not None:
        creation_filter += ' AND time_created <= :created_before'
    if created_after is not None:
        creation_filter += ' AND time_created >= :created_after'

    logger.info(f'Will use solr collection at: {settings.OPENALEX.solr_url}')
    with db_engine.session() as session:
        while True:
            partition = (
                session.execute(
                    text(
                        f"""
                    SELECT DISTINCT ON (openalex_id) openalex_id, upper(wrapper) as abstract_source, abstract, title
                    FROM request
                    WHERE (solarized = FALSE OR solarized IS NULL)
                      AND abstract IS NOT NULL
                      AND openalex_id IS NOT NULL {creation_filter}
                    ORDER BY openalex_id, time_created DESC
                    LIMIT :batch_size;
                    """,
                    ),
                    params={'created_before': created_before, 'created_after': created_after, 'batch_size': batch_size},
                )
                .mappings()
                .all()
            )

            if len(partition) == 0:
                logger.info('No more un-solarised entries with abstract found in meta-cache')
                break

            # Prepare minimal `Request` info
            records = [Request(openalex_id=r['openalex_id'], wrapper=r['abstract_source'], title=r['title'], abstract=r['abstract']) for r in partition]
            logger.info(f'Fetched {len(records):,} records to transfer to solr')

            # Submit to solr (this handles setting the correct fields and skipping existing abstracts if in non-force mode)
            write_cache_records_to_solr(config=settings.OPENALEX, records=records, batch_size=batch_size, force=force_overwrite, logger_=logger)

            # Set solarized flag for all records with the openalex_ids we just processed
            # Note, we don't limit this to the request.record_id that we processed on purpose.
            #       Otherwise, we'd process the next older record next time the method is called.
            session.execute(
                text('UPDATE request SET solarized = TRUE WHERE openalex_id = ANY(:ids)'),
                {'ids': [row['openalex_id'] for row in partition]},
            )
            session.commit()


def _queue_missing_abstracts(
    data: Iterable[tuple[str, str, str | None]],
    db_engine: DatabaseEngine,
    logger: logging.Logger,
    batch_size: int = 200,
    sources: list[tuple[APIEnum, SourcePriority]] | None = None,
    limit: int = 1000,
) -> None:
    if limit > 100000:
        raise ValueError(f'Limit must be <= 100000, but got {limit}')

    n_seen = 0
    n_queued = 0
    with db_engine.session() as session:
        for batch in batched(data, batch_size, strict=False):
            # We are only checking for OpenAlex ID on purpose (TODO: is this smart?)
            # Motivation is, that we might have the DOI in the queue already, but not linked to the OA-ID
            ids_missing: set[str] = {openalex_id for openalex_id, _doi, _pmid in batch}
            n_seen += len(ids_missing)

            ids_known: set[str] = set(
                session.execute(
                    text(
                        """
                        SELECT openalex_id
                        FROM request
                        WHERE openalex_id = ANY (:ids)
                          AND abstract IS NOT NULL
                        -----------------------------
                        UNION
                        -----------------------------
                        SELECT openalex_id
                        FROM queue
                        WHERE openalex_id = ANY (:ids);
                        """,
                    ),
                    {'ids': list(ids_missing)},
                )
                .scalars()
                .all(),
            )
            n_queued += len(ids_missing - ids_known)

            session.add_all(
                [
                    Queue(openalex_id=openalex_id, doi=doi, pubmed_id=pmid, on_conflict=OnConflict.DO_NOTHING, sources=sources)
                    for openalex_id, doi, pmid in batch
                    if openalex_id not in ids_known
                ],
            )
            session.commit()
            logger.debug(f'Queued {len(ids_missing - ids_known):,} entries for {len(ids_missing):,} entries')
        logger.info(f'{n_queued:,} queued for {n_seen:,} entries')


@app.command('queue-file', short_help='Use IDs in file to queue records with missing abstract')
def queue_from_file(
    config: Annotated[Path, typer.Option(help='Path to config file')],
    source: Annotated[Path, typer.Option(help='Source file containing ids to queue')],
    batch_size: Annotated[int, typer.Option(help='')] = 200,
    sources: Annotated[list[str] | None, typer.Option(callback=parse_sources, help='e.g. --sources OPENALEX,FORCE --sources SCOPUS,TRY')] = None,
    limit: Annotated[int, typer.Option(help='Failsafe so we do not accidentally queue millions')] = 1000,
    loglevel: Annotated[str, typer.Option(help='')] = 'INFO',
):
    import pandas as pd

    logger, settings, db_engine = prepare_runner(config=config, loglevel=loglevel, logger_name='abstract-queueing', run_log_init=True)
    df = pd.read_csv(source)
    if 'pmid' not in df.columns:
        df['pmid'] = None
    logger.info(f'Queueing {len(df)} records')
    _queue_missing_abstracts(df.values.tolist(), db_engine=db_engine, batch_size=batch_size, sources=sources, logger=logger, limit=limit)
    logger.info(f'Queued {len(df)} records')


@app.command('queue', short_help='Check solr and queue records with missing abstract')
def queue_missing_abstracts(
    config: Annotated[Path, typer.Option(help='Path to config file')],
    created_since: Annotated[datetime, typer.Option(help='Works w/o abstract created/updated on or after (will be clipped to beginning of day)')],
    created_until: Annotated[datetime | None, typer.Option(help='Works w/o abstract created/updated until then (will be clipped to end of day)')] = None,
    batch_size: Annotated[int, typer.Option(help='')] = 200,
    sources: Annotated[list[str] | None, typer.Option(callback=parse_sources, help='e.g. --sources OPENALEX,FORCE --sources SCOPUS,TRY')] = None,
    limit: Annotated[int, typer.Option(help='Failsafe so we do not accidentally queue millions')] = 1000,
    loglevel: Annotated[str, typer.Option(help='')] = 'INFO',
) -> None:
    """This method iterates all entries in solr that in a time frame that are missing an abstract.

    Qualifiers:
      - no abstract
      - date_created or date_updated within the time frame
      - openalex_id not in `queue` nor `request`
    """
    logger, settings, db_engine = prepare_runner(config=config, loglevel=loglevel, logger_name='abstract-queueing', run_log_init=True)
    logger.info('Queueing records with missing abstract')
    _queue_missing_abstracts(
        get_entries_with_missing_abstracts(
            config=settings.OPENALEX,
            created_since=created_since,
            created_until=created_until or datetime.now(),
            limit=limit,
        ),
        logger=logger,
        db_engine=db_engine,
        batch_size=batch_size,
        sources=sources,
        limit=limit,
    )
    logger.info('Done.')


if __name__ == '__main__':
    app()
