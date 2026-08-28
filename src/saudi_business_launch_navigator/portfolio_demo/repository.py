"""Read-only adapters over the separately verified synthetic demo graph."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from saudi_business_launch_navigator.checklist.models import ActivitySummary
from saudi_business_launch_navigator.checklist.repository import GovernedCatalog
from saudi_business_launch_navigator.core.config import Settings
from saudi_business_launch_navigator.portfolio_demo.catalog import build_demo_catalog
from saudi_business_launch_navigator.portfolio_demo.store import read_verified_demo_spec


class PortfolioDemoActivityDirectory:
    """List activities only after revalidating the exact demo identity and graph."""

    def __init__(self, engine: AsyncEngine, settings: Settings) -> None:
        self._engine = engine
        self._settings = settings

    async def list_active(self) -> tuple[ActivitySummary, ...]:
        async with AsyncSession(self._engine, expire_on_commit=False) as session, session.begin():
            await session.execute(
                text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            )
            spec, _verified = await read_verified_demo_spec(session, self._settings)
            return tuple(
                ActivitySummary(
                    code=activity.code,
                    name_ar=activity.name_ar,
                    name_en=activity.name_en,
                )
                for activity in spec.activities
            )


class PortfolioDemoCatalogRepository:
    """Expand only the identity-bound synthetic graph into the checklist read model."""

    def __init__(self, engine: AsyncEngine, settings: Settings) -> None:
        self._engine = engine
        self._settings = settings

    async def load(self, activity_code: str) -> GovernedCatalog:
        async with AsyncSession(self._engine, expire_on_commit=False) as session, session.begin():
            await session.execute(
                text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            )
            spec, verified = await read_verified_demo_spec(session, self._settings)
            return build_demo_catalog(
                spec,
                activity_code=activity_code,
                database_timestamp=verified.database_timestamp,
                migration_revision=verified.migration_revision,
            )


__all__ = ["PortfolioDemoActivityDirectory", "PortfolioDemoCatalogRepository"]
