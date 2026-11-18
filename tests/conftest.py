import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("LLM_PROVIDER", "fake")

import pytest
from fastapi.testclient import TestClient

from app.data.db import Base, SessionLocal, engine
from app.data.seed import init_db
from app.main import app


@pytest.fixture(autouse=True)
def _fresh_db():
    Base.metadata.drop_all(engine)
    init_db()
    yield


@pytest.fixture
def db():
    with SessionLocal() as s:
        yield s


@pytest.fixture
def client():
    return TestClient(app)
