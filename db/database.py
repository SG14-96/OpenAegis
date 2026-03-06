import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Load environment variables from .env file if present
load_dotenv()

logger = logging.getLogger(__name__)


def _redact_url(url: str) -> str:
    try:
        if "@" in url:
            scheme, rest = url.split("://", 1)
            if "@" in rest:
                _, host = rest.split("@", 1)
                return f"{scheme}://REDACTED@{host}"
        return url
    except Exception:
        return "REDACTED"


# Use DATABASE_URL environment variable for Postgres in development.
# Example: postgresql+psycopg2://postgres:password@localhost:5432/openaegis_dev
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:password@localhost:5432/openaegis_dev",
)

# Try to create the engine and verify a connection. If that fails, fall back
# to a local SQLite file so the application can still run in development.
engine = None
try:
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
        engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    else:
        engine = create_engine(SQLALCHEMY_DATABASE_URL)

    # Quick connection test
    with engine.connect() as conn:
        pass
    logger.info("Database engine created and connection verified for %s", _redact_url(SQLALCHEMY_DATABASE_URL))
except Exception as exc:  # pragma: no cover - handles runtime environment issues
    logger.exception("Failed to create/connect to database %s: %s", _redact_url(SQLALCHEMY_DATABASE_URL), exc)
    # Fallback to local sqlite so development can continue
    fallback_url = "sqlite:///./fallback_sql_app.db"
    logger.warning("Falling back to SQLite database at ./fallback_sql_app.db")
    engine = create_engine(fallback_url, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
