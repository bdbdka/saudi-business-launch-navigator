"""Lifecycle-verified catalog exposure token used by every catalog route."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from sqlalchemy.ext.asyncio import AsyncEngine

from saudi_business_launch_navigator.core.config import CatalogDataMode, Settings
from saudi_business_launch_navigator.portfolio_demo.store import (
    VerifiedPortfolioDemoDatabase,
    assert_portfolio_demo_runtime_access,
    verify_portfolio_demo_database,
)


class CatalogExposurePolicy(StrEnum):
    INTERNAL_LOOPBACK_GOVERNED = "INTERNAL_LOOPBACK_GOVERNED"
    SYNTHETIC_PORTFOLIO_DEMO = "SYNTHETIC_PORTFOLIO_DEMO"
    CLOSED_UNPUBLISHED_GOVERNED = "CLOSED_UNPUBLISHED_GOVERNED"


@dataclass(frozen=True)
class VerifiedCatalogBoundary:
    mode: CatalogDataMode
    exposure_policy: CatalogExposurePolicy
    demo_database: VerifiedPortfolioDemoDatabase | None = None


async def resolve_catalog_boundary(
    settings: Settings,
    engine: AsyncEngine,
) -> VerifiedCatalogBoundary:
    """Resolve demo mode only after exact database verification; governed mode stays closed."""

    if settings.catalog_mode is CatalogDataMode.PORTFOLIO_DEMO_CATALOG:
        verified = await verify_portfolio_demo_database(engine, settings)
        if settings.environment == "production":
            await assert_portfolio_demo_runtime_access(engine)
        return VerifiedCatalogBoundary(
            mode=settings.catalog_mode,
            exposure_policy=CatalogExposurePolicy.SYNTHETIC_PORTFOLIO_DEMO,
            demo_database=verified,
        )
    return VerifiedCatalogBoundary(
        mode=CatalogDataMode.GOVERNED_REAL_CATALOG,
        exposure_policy=(
            CatalogExposurePolicy.CLOSED_UNPUBLISHED_GOVERNED
            if settings.environment == "production"
            else CatalogExposurePolicy.INTERNAL_LOOPBACK_GOVERNED
        ),
    )


__all__ = [
    "CatalogExposurePolicy",
    "VerifiedCatalogBoundary",
    "resolve_catalog_boundary",
]
