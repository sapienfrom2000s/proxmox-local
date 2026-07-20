from flask import current_app
from redis import ConnectionPool, Redis


def init_redis(app):
    pool = ConnectionPool.from_url(
        app.config["REDIS_URL"],
        decode_responses=True,
    )
    app.extensions["redis"] = Redis(connection_pool=pool)


def get_redis() -> Redis:
    return current_app.extensions["redis"]
