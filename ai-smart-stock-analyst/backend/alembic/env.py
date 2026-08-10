"""
Alembic environment script — async-aware (the app uses `asyncpg` + async
SQLAlchemy sessions everywhere else, so migrations use the same driver
instead of silently requiring a second, sync-only `psycopg2` install).

The DB URL is NOT read from alembic.ini. It's read from the same
app.core.config.get_settings() the rest of the app uses, so `.env` remains
the single source of truth for DATABASE_URL (spec §31/49: no secrets
duplicated across config files).
"""
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# --- make `app.*` importable when alembic is run from the project root ---
from app.core.config import get_settings
from app.db.session import Base

# Import every model module here so they register on Base.metadata before
# autogenerate compares "what's in the DB" against "what the models say".
from app.db import models  # noqa: F401  (import for side effect only)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)


def run_migrations_offline() -> None:
    """Emit SQL to stdout without a live DB connection (`alembic upgrade --sql`)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
