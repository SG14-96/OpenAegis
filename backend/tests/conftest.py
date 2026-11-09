import os
import sys
from pathlib import Path

# Point the app at an in-memory SQLite DB before db.database is imported, so
# tests never touch Postgres or the fallback file.
os.environ["DATABASE_URL"] = "sqlite://"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from db.database import Base
import models.models  # noqa: F401 — register every table on Base.metadata
import models.settings  # noqa: F401
import models.events  # noqa: F401


@compiles(JSONB, "sqlite")
def _jsonb_as_sqlite_json(_type, _compiler, **_kw):
    # The settings tables use Postgres JSONB; SQLite's JSON is close enough
    # for tests.
    return "JSON"


@pytest.fixture
def session_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, autoflush=False, autocommit=False)
    engine.dispose()
