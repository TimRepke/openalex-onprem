import logging

from rq import Queue
from redis import Redis

from meta_cache.handlers.wrapper import WrapperEnum
from meta_cache.server.db import db_engine

logger = logging.getLogger('server.queues')
redis_conn = Redis()

queues = {
    w: Queue(name=WrapperEnum.queue_name(w), connection=redis_conn, default_timeout=900)
    for w in WrapperEnum.list()
}


def run(func, references, auth_key):
    func(db_engine=db_engine,
         references=references,
         auth_key=auth_key)
