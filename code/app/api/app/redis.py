from flask import g, current_app
from redis import ConnectionPool, Redis


def get_redis() -> Redis:
    if "redis" not in g:
        pool = ConnectionPool.from_url(
            current_app.config["REDIS_URL"],
            decode_responses=True,
        )
        g.redis = Redis(connection_pool=pool)
    return g.redis


def close_redis(e=None):
    redis_client = g.pop("redis", None)
    if redis_client is not None:
        redis_client.close()
