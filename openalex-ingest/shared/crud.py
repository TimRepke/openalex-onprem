import logging
from datetime import datetime
from typing import Generator

from sqlmodel import select, insert, text
from sqlalchemy.sql._typing import _ColumnExpressionArgument

from .schema import Request, Queue, QueueRequests
from .db import DatabaseEngine

logger = logging.getLogger('openalex.shared.crud')


def get_ors(reference: Request) -> list[_ColumnExpressionArgument[bool]]:
    return [getattr(Request, field) == value for field, value in Request.ids(reference)]


def read_complete_records(
    db_engine: DatabaseEngine,
    batch_size: int = 200,
    from_time: datetime | None = None,
) -> Generator[Request, None, None]:
    with db_engine.engine.connect() as connection:
        stmt = (
            select(Request)
            .distinct(Request.openalex_id)
            .where(
                Request.openalex_id != None,  # noqa: E711
                Request.abstract != None,  # noqa: E711
                Request.title != None,  # noqa: E711
            )
        )
        if from_time is not None:
            stmt = stmt.where(Request.time_created >= from_time)

        with connection.execution_options(yield_per=batch_size).execute(stmt) as result:
            for pi, partition in enumerate(result.partitions(batch_size)):
                logger.debug(f'Received partition {pi} from meta-cache.')
                yield from partition


def queue_requests(db_engine: DatabaseEngine, entries: list[Queue]):
    with db_engine.engine.connect() as connection:
        connection.execute(insert(Queue), [entry.model_dump(exclude={'queue_id'}) for entry in entries])
        connection.commit()


def update_default_sources(db_engine: DatabaseEngine):
    with db_engine.engine.connect() as connection:
        connection.execute(
            text(
                """
                UPDATE queue
                -- sources: list[tuple[APIEnum, SourcePriority]]
                -- SourcePriority.TRY = 2
                SET sources = '[["DIMENSIONS", 2], ["SCOPUS", 2], ["WOS", 2]]'
                WHERE sources IS NULL;
                """,
            ),
        )


def get_queued_for_source(
    db_engine: DatabaseEngine,
    source: str,  # APIEnum,
    limit: int = 25,
) -> Generator[Queue, None, None]:
    with db_engine.engine.connect() as connection:
        yield from (
            connection.execute(
                text(
                    """
                    SELECT queue_id,
                           doi,
                           openalex_id,
                           pubmed_id,
                           s2_id,
                           scopus_id,
                           wos_id,
                           dimensions_id,
                           nacsos_id,
                           sources,
                           on_conflict,
                           time_created
                    FROM queue
                    WHERE sources IS NOT NULL
                      AND sources[0] ->> 0 = :source
                    LIMIT :limit;
                    """,
                ),
                parameters={'limit': limit, 'source': source},
            )
            .scalars()
            .all()
        )


def get_queued_requested_for_source(
    db_engine: DatabaseEngine,
    source: str,  # APIEnum,
    limit: int = 25,
) -> Generator[QueueRequests, None, None]:
    with db_engine.engine.connect() as connection:
        yield from (
            connection.execute(
                text(
                    """
                    SELECT q.sources[0] ->> 0                                                       AS source,
                           q.sources[0] ->> 1                                                       AS priority,
                           count(1) FILTER ( WHERE r.record_id IS NOT NULL)                         AS num_has_request,
                           count(1) FILTER ( WHERE r.abstract IS NOT NULL)                          AS num_has_abstract,
                           count(1) FILTER ( WHERE r.title IS NOT NULL)                             AS num_has_title,
                           count(1) FILTER ( WHERE r.raw IS NOT NULL)                               AS num_has_raw,
                           count(1) FILTER ( WHERE r.record_id IS NOT NULL AND r.wrapper = :source) AS num_has_source_request,
                           count(1) FILTER ( WHERE r.abstract IS NOT NULL AND r.wrapper = :source)  AS num_has_source_abstract,
                           count(1) FILTER ( WHERE r.title IS NOT NULL AND r.wrapper = :source)     AS num_has_source_title,
                           count(1) FILTER ( WHERE r.raw IS NOT NULL AND r.wrapper = :source)       AS num_has_source_raw,
                           q.queue_id,
                           q.doi,
                           q.openalex_id,
                           q.pubmed_id,
                           q.s2_id,
                           q.scopus_id,
                           q.wos_id,
                           q.dimensions_id,
                           q.nacsos_id,
                           q.sources,
                           q.on_conflict,
                           q.time_created
                    FROM queue q
                         LEFT OUTER JOIN request r ON
                        (q.doi IS NOT NULL AND q.doi = r.doi)
                            OR (q.openalex_id IS NOT NULL AND q.openalex_id = r.openalex_id)
                            OR (q.pubmed_id IS NOT NULL AND q.pubmed_id = r.pubmed_id)
                            OR (q.s2_id IS NOT NULL AND q.s2_id = q.s2_id)
                            OR (q.scopus_id IS NOT NULL AND q.scopus_id = r.scopus_id)
                            OR (q.wos_id IS NOT NULL AND q.wos_id = r.wos_id)
                            OR (q.dimensions_id IS NOT NULL AND q.dimensions_id = r.dimensions_id)
                            OR (q.nacsos_id IS NOT NULL AND q.nacsos_id = r.nacsos_id)
                    WHERE sources IS NOT NULL
                      AND sources[0] ->> 0 = :source
                    GROUP BY source, priority, q.queue_id, q.doi, q.openalex_id, q.pubmed_id, q.s2_id, q.scopus_id, q.wos_id,
                             q.dimensions_id, q.nacsos_id, q.sources, q.on_conflict, q.time_created
                    LIMIT :limit;
                    """,
                ),
                parameters={'limit': limit, 'source': source},
            )
            .scalars()
            .all()
        )


def drop_source_from_queued(
    db_engine: DatabaseEngine,
    source: str,  # APIEnum,
    queue_ids: list[int],
) -> None:
    with db_engine.engine.connect() as connection:
        connection.execute(
            text(
                """UPDATE queue
                   SET sources = jsonb_path_query_array(sources, '$ ? (@[0] != "' || :source || '")')
                   WHERE sources IS NOT NULL
                     AND queue_id = ANY (:ids);""",
            ),
            parameters={'source': source, 'ids': queue_ids},
        )


def drop_unforced_sources_from_queued(
    db_engine: DatabaseEngine,
    queue_ids: list[int],
) -> None:
    with db_engine.engine.connect() as connection:
        connection.execute(
            text(
                """UPDATE queue
                   SET sources = jsonb_path_query_array(sources, '$ ? (@[1] > 1 )')
                   WHERE sources IS NOT NULL
                     AND queue_id = ANY (:ids);""",
            ),
            parameters={'ids': queue_ids},
        )


def drop_finished_from_queue(
    db_engine: DatabaseEngine,
) -> None:
    with db_engine.engine.connect() as connection:
        connection.execute(text("DELETE FROM queue WHERE sources = '[]'::jsonb;"))


def drop_queued(
    db_engine: DatabaseEngine,
    queue_ids: list[int],
) -> None:
    with db_engine.engine.connect() as connection:
        connection.execute(text('DELETE FROM queue WHERE queue_id = ANY (:ids);'), parameters={'ids': queue_ids})
