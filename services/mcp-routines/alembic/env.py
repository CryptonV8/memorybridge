import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Alembic Config object
config = context.config

# Set up logging from the ini file
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

import sys
from os.path import abspath, dirname
sys.path.insert(0, dirname(dirname(abspath(__file__))))

from src.database import Base
import src.models
target_metadata = Base.metadata


def _get_migration_url() -> str:
    """
    Return the database URL to use for migrations.

    Priority:
      1. MIGRATION_DATABASE_URL — Neon direct/unpooled connection string.
         Use when DATABASE_URL is a pooled (PgBouncer) connection that is
         incompatible with Alembic's DDL-heavy migration sessions.
      2. DATABASE_URL — runtime pooled URL, used as fallback.
      3. alembic.ini sqlalchemy.url — last resort placeholder (dev only).

    Connection strings are never printed or logged.
    """
    migration_url = os.environ.get("MIGRATION_DATABASE_URL")
    if migration_url:
        return migration_url

    runtime_url = os.environ.get("DATABASE_URL")
    if runtime_url:
        return runtime_url

    # Last resort: fall through to the ini value (dev placeholder only)
    ini_url = config.get_main_option("sqlalchemy.url", "")
    return ini_url


def run_migrations_offline() -> None:
    """Run migrations in offline mode (emit SQL to stdout)."""
    url = _get_migration_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in online mode (connect and apply)."""
    url = _get_migration_url()
    config.set_main_option("sqlalchemy.url", url)
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
