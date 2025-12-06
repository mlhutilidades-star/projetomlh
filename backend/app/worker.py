import os
from rq import Worker, Queue
from redis import Redis

from app.core.config import get_settings
from app.tasks import jobs  # noqa: F401  ensures tasks imported

settings = get_settings()

listen = ['default']


if __name__ == '__main__':
    redis_url = settings.redis_url
    conn = Redis.from_url(redis_url)
    worker = Worker([Queue(name, connection=conn) for name in listen], connection=conn)
    worker.work()
