import logging
from datetime import datetime

from fastapi import APIRouter, Header, Depends, Body, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlmodel import select, or_
from fastapi.responses import JSONResponse

from meta_cache.handlers.models import CacheRequest, CacheResponse, DehydratedRecord
from meta_cache.handlers.crud import CacheResponseHandler
from meta_cache.handlers.schema import AuthKey, Request
from meta_cache.handlers.util import get_ors

from .db import db_engine
from .queue import queues, run

logger = logging.getLogger('server')
router = APIRouter()


def is_valid_key(x_auth_key: str = Header()) -> AuthKey:
    with db_engine.session() as session:
        key = session.get(AuthKey, x_auth_key)
        if key and key.active:
            logger.debug(f'Found valid auth key: {key}')
            return key
        raise PermissionError('Auth key does not exist or is not active.')


@router.get('/health-check')
async def health_check() -> JSONResponse:
    """
    Health check endpoint for the API.
    Returns:
        JSONResponse: Response indicating the API is healthy.
    """
    return JSONResponse(content={"status": "ok"}, status_code=status.HTTP_200_OK)


class StatsEntry(BaseModel):
    time_created: datetime | None = None
    n_total: int
    n_with_title: int
    n_with_abstract: int
    n_with_scopus: int
    n_with_dimensions: int


@router.get('/daily-stats', response_model=list[StatsEntry])
async def daily_stats(limit: int = 10):  # , auth_key: AuthKey = Depends(is_valid_key)
    stmt = text('''
        SELECT date_trunc('day', time_created) as time_created,
               count(1)                        as n_total,
               count(title)                    as n_with_title,
               count(abstract)                 as n_with_abstract,
               count(1) FILTER ( WHERE raw is not NULL and wrapper = 'scopus' )     as n_with_scopus,
               count(1) FILTER ( WHERE raw is not NULL and wrapper = 'dimensions' ) as n_with_dimensions
        FROM request
        GROUP BY date_trunc('day', time_created)
        ORDER BY date_trunc('day', time_created) DESC
        LIMIT :limit;
    ''')

    with db_engine.session() as session:
        res = session.execute(stmt, {'limit': limit})
        return res.mappings().all()


@router.get('/stats', response_model=list[StatsEntry])
async def stats():  # , auth_key: AuthKey = Depends(is_valid_key)
    stmt = text('''
        SELECT count(1)                        as n_total,
               count(title)                    as n_with_title,
               count(abstract)                 as n_with_abstract,
               count(1) FILTER ( WHERE raw is not NULL and wrapper = 'scopus' )     as n_with_scopus,
               count(1) FILTER ( WHERE raw is not NULL and wrapper = 'dimensions' ) as n_with_dimensions
        FROM request;
    ''')

    with db_engine.session() as session:
        res = session.execute(stmt)
        return res.mappings().all()


@router.post('/lookup', response_model=CacheResponse)
async def lookup(request: CacheRequest, auth_key: AuthKey = Depends(is_valid_key)) -> CacheResponse:
    handler = CacheResponseHandler(request=request, db_engine=db_engine)
    handler.fetch()

    for wrapper in request.wrappers():
        logger.debug('Queueing job')
        job = queues[wrapper.name].enqueue(run,
                                           func=wrapper.run,
                                           references=list(handler.queued),
                                           auth_key=auth_key.auth_key_id)
        handler.queued_job = job.id
        logger.debug(f'Job {job.id} @ {job.origin}')

    return handler.response


@router.post('/write')
async def write(reference: Request, auth_key: AuthKey = Depends(is_valid_key)) -> bool:
    ret = False
    if auth_key.write:
        logger.debug('Received new record')
        with db_engine.session() as session:
            for record in session.exec(select(Request).where(or_(*get_ors(reference)))):
                logger.debug(f'Found received record as {record.record_id}')
                ret = True
                record.sqlmodel_update(reference.model_dump(exclude_unset=True, exclude_none=True))
                session.add(record)
            if not ret:
                session.add(reference)
                ret = True
            session.commit()
    return ret


@router.post('/read', response_model=list[DehydratedRecord])
async def read(openalex_ids: list[str] = Body(), auth_key: AuthKey = Depends(is_valid_key)) -> list[Request]:
    if auth_key.write:
        if len(openalex_ids) > 200:
            raise PermissionError('Requested too many openalex ids at once!')

        logger.debug(f'Requested {len(openalex_ids)} records')
        with db_engine.session() as session:
            return session.exec(select(Request).where(Request.openalex_id.in_(openalex_ids))).all()

    raise PermissionError('Can\'t touch that!')
