import logging
from datetime import datetime
from typing import Generator

from sqlmodel import select, insert
from .schema import Request, Queue
from .db import DatabaseEngine

logger = logging.getLogger('openalex.shared.crud')


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
