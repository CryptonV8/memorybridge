import os
import logging
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, declarative_base

logger = logging.getLogger(__name__)

# ── Database URL ──────────────────────────────────────────────────────────────
# In production, DATABASE_URL must be set in the environment and must point to
# the Neon pooled connection string (postgresql+psycopg2://...).
# In local development, falls back to SQLite for isolated unit tests.
# Connection strings are NEVER logged.
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./test.db")

_is_sqlite = DATABASE_URL.startswith("sqlite")

if _is_sqlite:
    # SQLite: simple config for local isolated testing
    connect_args = {"check_same_thread": False}
    engine = create_engine(DATABASE_URL, connect_args=connect_args)
else:
    # PostgreSQL / Neon: safe pool settings compatible with both
    # Neon pooled (PgBouncer) and direct connections.
    #
    # pool_pre_ping=True  — drops stale connections before use (important for
    #                       Neon which times out idle connections quickly).
    # pool_size=2         — small pool suitable for Cloud Run single-instance.
    # max_overflow=3      — allow short bursts above pool_size.
    # pool_recycle=1800   — recycle connections every 30 minutes.
    # pool_timeout=30     — raise after 30s if no connection available.
    #
    # Neon recommends sslmode=require. If the URL does not already include
    # ?sslmode=require, we append it here.
    _db_url = DATABASE_URL
    if "sslmode" not in _db_url and _db_url.startswith("postgresql"):
        _sep = "&" if "?" in _db_url else "?"
        _db_url = f"{_db_url}{_sep}sslmode=require"

    connect_args = {}
    engine = create_engine(
        _db_url,
        connect_args=connect_args,
        pool_pre_ping=True,
        pool_size=2,
        max_overflow=3,
        pool_recycle=1800,
        pool_timeout=30,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
