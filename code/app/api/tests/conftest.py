import pytest
import fakeredis
from app import create_app


@pytest.fixture
def app():
    fake_redis = fakeredis.FakeRedis(decode_responses=True)
    app = create_app({"TESTING": True})
    app.extensions["redis"] = fake_redis
    yield app
    fake_redis.flushall()


@pytest.fixture
def client(app):
    return app.test_client()
