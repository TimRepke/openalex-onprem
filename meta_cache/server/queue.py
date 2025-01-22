from rq import Queue
from redis import Redis

from meta_cache.wrappers import Wrapper

redis_conn = Redis()

queues = {
    w: Queue(name=f'meta-cache-{w}', connection=redis_conn)
    for w in Wrapper.list()
}
