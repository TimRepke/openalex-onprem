import logging
from fastapi import APIRouter, Header, Depends, Body
from sqlmodel import select, or_

from meta_cache.handlers.models import CacheRequest, CacheResponse, DehydratedRecord
from meta_cache.handlers.crud import CacheResponseHandler
from meta_cache.handlers.wrappers import get_wrapper
from meta_cache.handlers.schema import AuthKey, Record
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


@router.post('/lookup', response_model=CacheResponse)
async def lookup(request: CacheRequest, auth_key: AuthKey = Depends(is_valid_key)) -> CacheResponse:
    handler = CacheResponseHandler(request=request, db_engine=db_engine)
    handler.fetch()
    wrapper = get_wrapper(handler.request.wrapper)

    logger.debug('Queueing job')
    job = queues[wrapper.name].enqueue(run,
                                       func=wrapper.run,
                                       references=list(handler.queued),
                                       auth_key=auth_key.auth_key_id)
    handler.queued_job = job.id
    logger.debug(f'Job {job.id} @ {job.origin}')

    return handler.response


@router.post('/write')
async def write(reference: Record, auth_key: AuthKey = Depends(is_valid_key)) -> bool:
    ret = False
    if auth_key.write:
        logger.debug('Received new record')
        with db_engine.session() as session:
            for record in session.exec(select(Record).where(or_(*get_ors(reference)))):
                logger.debug(f'Found received record as {record.record_id}')
                ret = True
                record.sqlmodel_update(reference.model_dump(exclude_unset=True, exclude_none=True))
                session.add(record)
            if not ret:
                session.add(reference)
                ret = True
            session.commit()
    return ret


@router.post('/read', response_model=CacheResponse)
async def read(openalex_ids: list[str] = Body(), auth_key: AuthKey = Depends(is_valid_key)) -> DehydratedRecord:
    if auth_key.write:
        if len(openalex_ids) > 200:
            raise PermissionError('Requested too many openalex ids at once!')

        logger.debug(f'Requested {len(openalex_ids)} records')
        with db_engine.session() as session:
            return session.exec(select(Record).where(Record.openalex_id.in_(openalex_ids))).all()
