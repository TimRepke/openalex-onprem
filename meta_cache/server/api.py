import logging
from fastapi import APIRouter, Header, Depends

from meta_cache.handlers.models import CacheRequest, CacheResponse
from meta_cache.handlers.crud import CacheResponseHandler
from meta_cache.handlers.wrappers import get_wrapper
from meta_cache.handlers.schema import AuthKey
from meta_cache.handlers.wrapper import WrapperEnum

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
