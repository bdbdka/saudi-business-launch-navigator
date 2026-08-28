"""Alembic environment for the explicitly qualified navigator schema."""

import asyncio
from collections.abc import MutableMapping
from logging.config import fileConfig
from typing import Literal, cast

from alembic import context
from sqlalchemy import Connection, pool, text
from sqlalchemy.ext.asyncio import async_engine_from_config

from saudi_business_launch_navigator.core.config import get_settings
from saudi_business_launch_navigator.db.base import NAVIGATOR_SCHEMA, Base
from saudi_business_launch_navigator.db.models import *  # noqa: F403

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def database_url() -> str:
    """Return the validated database URL without writing it to Alembic files."""
    return cast(str, get_settings().database_url.get_secret_value())


def include_name(
    name: str | None,
    object_type: Literal[
        "schema",
        "table",
        "column",
        "index",
        "unique_constraint",
        "foreign_key_constraint",
        "check_constraint",
    ],
    parent_names: MutableMapping[
        Literal["schema_name", "table_name", "schema_qualified_table_name"],
        str | None,
    ],
) -> bool:
    """Limit autogeneration to application objects, excluding Alembic metadata."""
    if object_type == "schema":
        return name == NAVIGATOR_SCHEMA
    if object_type == "table":
        schema_name = parent_names.get("schema_name")
        return schema_name == NAVIGATOR_SCHEMA and name != "alembic_version"
    return True


def configure_context(*, connection: Connection | None = None) -> None:
    """Configure schema-aware migration behavior for online or offline use."""
    if connection is None:
        context.configure(
            url=database_url(),
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
            target_metadata=target_metadata,
            include_schemas=True,
            version_table="alembic_version",
            version_table_schema=NAVIGATOR_SCHEMA,
            compare_type=True,
            compare_server_default=True,
            render_as_batch=False,
            include_name=include_name,
        )
    else:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            version_table="alembic_version",
            version_table_schema=NAVIGATOR_SCHEMA,
            compare_type=True,
            compare_server_default=True,
            render_as_batch=False,
            include_name=include_name,
        )


def run_migrations_offline() -> None:
    """Emit SQL without connecting, including the Alembic schema bootstrap."""
    configure_context()
    with context.begin_transaction():
        context.execute(text(f"CREATE SCHEMA IF NOT EXISTS {NAVIGATOR_SCHEMA}"))
        context.run_migrations()


def run_sync_migrations(connection: Connection) -> None:
    """Run migrations through one synchronous bridge connection."""
    connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {NAVIGATOR_SCHEMA}"))
    connection.execute(text("SET search_path TO public"))
    connection.commit()
    # The development role shares its name with the application schema, so
    # PostgreSQL initially reports ``navigator`` as the default schema.
    # Alembic must still reflect ``navigator`` as an explicitly named schema.
    connection.dialect.default_schema_name = "public"
    configure_context(connection=connection)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations using the approved async Psycopg SQLAlchemy URL."""
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = database_url()
    connectable = async_engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        hide_parameters=True,
    )
    try:
        async with connectable.connect() as connection:
            await connection.run_sync(run_sync_migrations)
    finally:
        await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
