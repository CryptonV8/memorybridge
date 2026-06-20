import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Get database URL for testing
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL") or os.environ.get(
    "DATABASE_URL"
)


@pytest.fixture(scope="session")
def db_engine():
    # Enforce PostgreSQL for database integration tests. No SQLite fallback.
    if not TEST_DATABASE_URL:
        pytest.fail(
            "Integration tests requested but no PostgreSQL configuration was found. "
            "Please set TEST_DATABASE_URL or DATABASE_URL environment variable to a valid PostgreSQL URL."
        )
    if not (
        TEST_DATABASE_URL.startswith("postgresql://")
        or TEST_DATABASE_URL.startswith("postgres://")
    ):
        pytest.fail(
            f"Integration tests require a PostgreSQL database, but found: '{TEST_DATABASE_URL}'. "
            "Do not silently fall back to SQLite."
        )

    engine = create_engine(TEST_DATABASE_URL)
    try:
        with engine.connect():
            pass
    except Exception as e:
        pytest.fail(
            f"Failed to connect to the PostgreSQL test database at '{TEST_DATABASE_URL}': {e}"
        )

    return engine


@pytest.fixture(scope="package")
def setup_db(db_engine):
    # Run Alembic migrations programmatically from an empty database
    from alembic.config import Config
    from alembic import command
    from src.database import Base

    # 1. Clean database completely (drop all existing tables to simulate empty database)
    Base.metadata.reflect(bind=db_engine)
    Base.metadata.drop_all(bind=db_engine)

    # 2. Locate alembic.ini relative to this conftest file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    alembic_ini_path = os.path.join(project_root, "alembic.ini")

    alembic_cfg = Config(alembic_ini_path)
    alembic_cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)

    # 3. Upgrade to head
    command.upgrade(alembic_cfg, "head")
    yield

    # 4. Clean up tables
    Base.metadata.reflect(bind=db_engine)
    Base.metadata.drop_all(bind=db_engine)


@pytest.fixture(scope="function")
def db_session(db_engine, setup_db):
    connection = db_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    yield session
    session.close()
    transaction.rollback()
    connection.close()
