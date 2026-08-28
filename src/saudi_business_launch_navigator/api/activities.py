"""Read-only supported-activity directory used by the API adapter."""

from __future__ import annotations

from typing import Protocol

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from saudi_business_launch_navigator.checklist.models import ActivitySummary
from saudi_business_launch_navigator.db.models.reference import BusinessActivity
from saudi_business_launch_navigator.interpretation.models import SupportedActivity


class ActivityDirectory(Protocol):
    async def list_active(self) -> tuple[ActivitySummary, ...]:
        """Return active governed activity labels in stable code order."""


class SqlAlchemyActivityDirectory:
    """Read active activities in a transaction explicitly marked read only."""

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def list_active(self) -> tuple[ActivitySummary, ...]:
        async with (
            AsyncSession(self._engine, expire_on_commit=False) as session,
            session.begin(),
        ):
            await session.execute(text("SET TRANSACTION READ ONLY"))
            rows = (
                await session.execute(
                    select(BusinessActivity)
                    .where(BusinessActivity.is_active.is_(True))
                    .where(
                        BusinessActivity.code.in_(
                            tuple(activity.value for activity in SupportedActivity)
                        )
                    )
                    .order_by(BusinessActivity.code)
                )
            ).scalars()
            return tuple(
                ActivitySummary(code=row.code, name_ar=row.name_ar, name_en=row.name_en)
                for row in rows
            )


__all__ = ["ActivityDirectory", "SqlAlchemyActivityDirectory"]
