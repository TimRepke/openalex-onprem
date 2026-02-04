from datetime import datetime
from itertools import batched
from pathlib import Path
from typing import Annotated

import typer
from nacsos_data.util.academic.apis import APIEnum
from sqlalchemy import text

from shared.config import load_settings
from shared.db import get_engine
from shared.models import OnConflict, SourcePriority
from shared.schema import Request, Queue
from shared.solr import write_cache_records_to_solr, get_entries_with_missing_abstracts
from shared.util import get_logger

app = typer.Typer()


@app.command('transfer', short_help='Write abstract from cache to solr')
def transfer_abstracts(
    config: Annotated[Path, typer.Option(help='Path to config file')],
    batch_size: int = 200,
    force_overwrite: bool = False,
    loglevel: str = 'INFO',
) -> None:
    """This method iterates through all entries in the meta-cache that have an abstract and are not yet written to solr to do just that.

    1) Fetch records from `request` table that have an abstract where `solarized = False`
    2) Construct update query (abstract_source, abstract_date, abstract)
    3) Submit to solr
    4) Update solarized flag on success
    """
    logger = get_logger('abstract-transfer', loglevel=loglevel, run_init=True)
    logger.info(f'Loading config from {config.resolve()}...')
    if not config.exists():
        raise AssertionError(f'Config file does not exist at {config.resolve()}!')
    settings = load_settings(config)

    logger.info('Connecting to database...')
    db_engine = get_engine(settings=settings.CACHE_DB)

    logger.info(f'Will use solr collection at: {settings.OPENALEX.solr_url}')
    with db_engine.session() as session:
        for partition in (
            session.execute(
                text(
                    """
                SELECT DISTINCT ON (openalex_id) openalex_id, upper(wrapper) as abstract_source, abstract, title
                FROM request
                WHERE (solarized = False OR solarized IS NULL)
                  AND abstract IS NOT NULL
                  AND openalex_id IS NOT NULL
                ORDER BY openalex_id, time_created DESC;
                """,
                ),
                execution_options={'yield_per': batch_size},
            )
            .mappings()
            .partitions(batch_size)
        ):
            # Prepare minimal `Request` info
            records = [Request(openalex_id=r['openalex_id'], wrapper=r['abstract_source'], title=r['title'], abstract=r['abstract']) for r in partition]

            # Submit to solr (this handles setting the correct fields and skipping existing abstracts if in non-force mode)
            write_cache_records_to_solr(config=settings.OPENALEX, records=records, batch_size=batch_size, force=force_overwrite)

            # Set solarized flag for all records with the openalex_ids we just processed
            # Note, we don't limit this to the request.record_id that we processed on purpose.
            #       Otherwise, we'd process the next older record next time the method is called.
            session.execute(
                text('UPDATE request SET solarized = TRUE WHERE openalex_id = ANY(:ids)'),
                {'ids': [row['openalex_id'] for row in partition]},
            )


@app.command('queue', short_help='Check solr and queue records with missing abstract')
def queue_missing_abstracts(
    config: Annotated[Path, typer.Option(help='Path to config file')],
    created_since: Annotated[datetime, typer.Option(help='Works w/o abstract created/updated on or after (will be clipped to beginning of day)')],
    created_until: Annotated[datetime | None, typer.Option(help='Works w/o abstract created/updated until then (will be clipped to end of day)')] = None,
    batch_size: Annotated[int, typer.Option(help='')] = 200,
    sources: list[tuple[APIEnum, SourcePriority]] | None = None,
    limit: Annotated[int, typer.Option(help='Failsafe so we do not accidentally queue millions')] = 1000,
    loglevel: Annotated[str, typer.Option(help='')] = 'INFO',
) -> None:
    """This method iterates all entries in solr that in a time frame that are missing an abstract.

    Qualifiers:
      - no abstract
      - date_created or date_updated within the time frame
      - openalex_id not in `queue` nor `request`
    """
    if limit > 100000:
        raise ValueError(f'Limit must be <= 100000, but got {limit}')

    logger = get_logger('abstract-queueing', loglevel=loglevel, run_init=True)
    logger.info(f'Loading config from {config.resolve()}...')
    if not config.exists():
        raise AssertionError(f'Config file does not exist at {config.resolve()}!')
    settings = load_settings(config)

    logger.info('Connecting to database...')
    db_engine = get_engine(settings=settings.CACHE_DB)

    logger.info(f'Will use solr collection at: {settings.OPENALEX.solr_url}')
    with db_engine.session() as session:
        for batch in batched(
            get_entries_with_missing_abstracts(
                config=settings.OPENALEX,
                created_since=created_since,
                created_until=created_until or datetime.now(),
                limit=limit,
            ),
            batch_size,
            strict=False,
        ):
            # We are only checking for OpenAlex ID on purpose (TODO: is this smart?)
            # Motivation is, that we might have the DOI in the queue already, but not linked to the OA-ID
            ids_missing: set[str] = {openalex_id for openalex_id, _doi, _pmid in batch}
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
            session.add_all(
                [
                    Queue(openalex_id=openalex_id, doi=doi, pubmed_id=pmid, on_conflict=OnConflict.DO_NOTHING, sources=sources)
                    for openalex_id, doi, pmid in batch
                    if openalex_id not in ids_known
                ],
            )
            session.commit()


if __name__ == '__main__':
    app()
