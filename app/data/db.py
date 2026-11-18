from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings


class Base(DeclarativeBase):
    pass


_url = get_settings().database_url
_kw = {}
if _url.startswith("sqlite"):
    _kw = dict(connect_args={"check_same_thread": False}, poolclass=StaticPool)
engine = create_engine(_url, pool_pre_ping=True, **_kw)
SessionLocal = sessionmaker(engine, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
