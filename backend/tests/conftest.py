import os
import sys
from pathlib import Path

# Point the app at an in-memory SQLite DB before db.database is imported, so
# tests never touch Postgres or the fallback file.
os.environ["DATABASE_URL"] = "sqlite://"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.events import AlarmStateEvent, ArmingEvent


@pytest.fixture
def session_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Only the event tables — the settings tables use Postgres-only JSONB.
    for model in (ArmingEvent, AlarmStateEvent):
        model.__table__.create(engine)
    yield sessionmaker(bind=engine, autoflush=False, autocommit=False)
    engine.dispose()
