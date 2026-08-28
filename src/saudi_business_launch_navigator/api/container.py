"""Application service composition kept outside HTTP route functions."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine

from saudi_business_launch_navigator.api.activities import (
    ActivityDirectory,
    SqlAlchemyActivityDirectory,
)
from saudi_business_launch_navigator.api.catalog_boundary import (
    CatalogExposurePolicy,
    VerifiedCatalogBoundary,
)
from saudi_business_launch_navigator.checklist.models import CoverageNotice
from saudi_business_launch_navigator.checklist.repository import (
    GovernedCatalogRepository,
    SqlAlchemyGovernedCatalogRepository,
)
from saudi_business_launch_navigator.checklist.service import ChecklistService
from saudi_business_launch_navigator.core.config import Settings
from saudi_business_launch_navigator.interpretation.openai_client import OpenAIResponsesAdapter
from saudi_business_launch_navigator.interpretation.service import (
    BoundedExplanationService,
    BoundedInterpreterService,
    InterpretationService,
)
from saudi_business_launch_navigator.portfolio_demo.catalog import (
    dataset_fingerprint,
    load_portfolio_demo_spec,
)
from saudi_business_launch_navigator.portfolio_demo.repository import (
    PortfolioDemoActivityDirectory,
    PortfolioDemoCatalogRepository,
)


@dataclass(frozen=True)
class ApplicationServices:
    activities: ActivityDirectory
    checklist: ChecklistService
    interpreter: BoundedInterpreterService | None
    navigator: InterpretationService | None


def build_application_services(
    settings: Settings,
    engine: AsyncEngine,
    boundary: VerifiedCatalogBoundary,
) -> ApplicationServices:
    """Compose production services once per application lifecycle."""

    if boundary.exposure_policy is CatalogExposurePolicy.SYNTHETIC_PORTFOLIO_DEMO:
        if boundary.demo_database is None:
            raise RuntimeError("verified portfolio demo boundary is unavailable")
        coverage = _portfolio_demo_coverage_notice()
        repository: GovernedCatalogRepository = PortfolioDemoCatalogRepository(engine, settings)
        activities: ActivityDirectory = PortfolioDemoActivityDirectory(engine, settings)
    else:
        coverage = _unpublished_coverage_notice()
        repository = SqlAlchemyGovernedCatalogRepository(engine)
        activities = SqlAlchemyActivityDirectory(engine)
    checklist = ChecklistService(
        repository,
        coverage,
    )
    interpreter: BoundedInterpreterService | None = None
    navigator: InterpretationService | None = None
    if settings.openai_api_key is not None:
        adapter = OpenAIResponsesAdapter(settings)
        interpreter = BoundedInterpreterService(adapter)
        navigator = InterpretationService(
            interpreter=interpreter,
            explainer=BoundedExplanationService(adapter),
            checklist_service=checklist,
            coverage_notice=coverage,
        )
    return ApplicationServices(
        activities=activities,
        checklist=checklist,
        interpreter=interpreter,
        navigator=navigator,
    )


def _unpublished_coverage_notice() -> CoverageNotice:
    """Keep the governed catalog unavailable unless a public catalog is configured."""

    return CoverageNotice(
        message_ar="الفهرس التنظيمي غير منشور وغير متاح في بيئة الإنتاج.",
        message_en="The regulatory catalog is unpublished and unavailable in production.",
        unresolved_topics=("publication_not_authorized",),
        source_artifact_id="UNPUBLISHED_CATALOG_DISABLED",
        source_artifact_fingerprint="0" * 64,
    )


def _portfolio_demo_coverage_notice() -> CoverageNotice:
    """Return a sample-data warning derived only from the public demo seed."""

    spec = load_portfolio_demo_spec()
    return CoverageNotice(
        message_ar=spec.warning_ar,
        message_en=spec.warning_en,
        unresolved_topics=("synthetic_sample_data", "real_regulatory_use_not_authorized"),
        source_artifact_id=spec.dataset_code,
        source_artifact_fingerprint=dataset_fingerprint(spec),
    )


__all__ = ["ApplicationServices", "build_application_services"]
