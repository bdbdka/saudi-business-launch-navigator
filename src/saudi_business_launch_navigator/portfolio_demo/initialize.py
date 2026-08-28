"""Reproducible empty-database migration and portfolio-demo seed command."""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from saudi_business_launch_navigator.core.config import get_settings
from saudi_business_launch_navigator.db.engine import (
    create_database_engine,
    dispose_database_engine,
)
from saudi_business_launch_navigator.portfolio_demo.catalog import DEMO_MIGRATION_REVISION
from saudi_business_launch_navigator.portfolio_demo.store import (
    VerifiedPortfolioDemoDatabase,
    assert_portfolio_demo_migration_target,
    provision_portfolio_demo_runtime_role,
    seed_portfolio_demo_database,
)

_RUNTIME_PASSWORD_ENV = "SBLN_DEMO_RUNTIME_DATABASE_PASSWORD"
_INITIALIZATION_LOCK_KEY = 7_310_462_011


@asynccontextmanager
async def _initialization_lock(engine: AsyncEngine) -> AsyncIterator[None]:
    """Serialize every demo initializer before any migration DDL can run."""

    async with engine.connect() as connection:
        await connection.execution_options(isolation_level="AUTOCOMMIT")
        acquired = (
            await connection.execute(
                text("SELECT pg_catalog.pg_try_advisory_lock(:lock_key)"),
                {"lock_key": _INITIALIZATION_LOCK_KEY},
            )
        ).scalar_one()
        if not acquired:
            raise RuntimeError("another portfolio demo initializer is already running")
        try:
            yield
        finally:
            await connection.execute(
                text("SELECT pg_catalog.pg_advisory_unlock(:lock_key)"),
                {"lock_key": _INITIALIZATION_LOCK_KEY},
            )


def _upgrade() -> None:
    command.upgrade(Config("alembic.ini"), DEMO_MIGRATION_REVISION)


async def _initialize() -> tuple[str, str, VerifiedPortfolioDemoDatabase]:
    settings = get_settings()
    runtime_password = os.environ.get(_RUNTIME_PASSWORD_ENV, "")
    if len(runtime_password) < 24:
        raise RuntimeError("portfolio demo runtime database credential is unavailable")
    engine = create_database_engine(settings)
    try:
        async with _initialization_lock(engine):
            pre_migration = await assert_portfolio_demo_migration_target(engine, settings)
            await asyncio.to_thread(_upgrade)
            post_migration = await assert_portfolio_demo_migration_target(engine, settings)
            result = await seed_portfolio_demo_database(engine, settings)
            await provision_portfolio_demo_runtime_role(engine, settings, runtime_password)
        return pre_migration.value, post_migration.value, result
    finally:
        await dispose_database_engine(engine)


def main() -> None:
    """Lock, classify, migrate, reclassify, seed, and provision the demo database."""

    pre_migration, post_migration, result = asyncio.run(_initialize())
    print("portfolio_demo_database=verified")
    print(f"migration_revision={result.migration_revision}")
    print(f"dataset_code={result.dataset_code}")
    print(f"dataset_revision={result.dataset_revision}")
    print(f"dataset_fingerprint={result.dataset_fingerprint_sha256}")
    print(f"pre_migration_target={pre_migration}")
    print(f"post_migration_target={post_migration}")


if __name__ == "__main__":
    main()
