"""Production startup and unpublished-catalog boundary tests."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncEngine

import saudi_business_launch_navigator.api.container as container
from saudi_business_launch_navigator.api.activities import SqlAlchemyActivityDirectory
from saudi_business_launch_navigator.api.app import create_app
from saudi_business_launch_navigator.api.catalog_boundary import (
    CatalogExposurePolicy,
    VerifiedCatalogBoundary,
)
from saudi_business_launch_navigator.checklist.service import ChecklistService
from saudi_business_launch_navigator.core.config import CatalogDataMode, Settings


def _settings() -> Settings:
    return Settings(
        _env_file=None,
        environment="production",
        api_docs_enabled=False,
        database_url=("postgresql+psycopg://runtime:secret@db.internal/navigator?sslmode=require"),
        cors_allowed_origins=("https://navigator.example.invalid",),
        allowed_hosts=("api.example.invalid",),
    )


def test_closed_catalog_mode_starts_without_external_coverage_files() -> None:
    engine = MagicMock(spec=AsyncEngine)

    boundary = VerifiedCatalogBoundary(
        mode=CatalogDataMode.GOVERNED_REAL_CATALOG,
        exposure_policy=CatalogExposurePolicy.CLOSED_UNPUBLISHED_GOVERNED,
    )
    services = container.build_application_services(_settings(), engine, boundary)

    assert services.checklist is not None
    assert services.navigator is None


def test_production_routes_reject_before_catalog_data_reads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def forbidden_data_read(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("unpublished production route attempted a catalog read")

    monkeypatch.setattr(
        SqlAlchemyActivityDirectory,
        "list_active",
        forbidden_data_read,
    )
    monkeypatch.setattr(
        ChecklistService,
        "build_questionnaire",
        forbidden_data_read,
    )
    monkeypatch.setattr(
        ChecklistService,
        "evaluate_business_profile",
        forbidden_data_read,
    )
    engine = MagicMock(spec=AsyncEngine)
    engine.dispose = AsyncMock()
    app = create_app(
        _settings(),
        engine_factory=lambda _settings: engine,
        services_factory=container.build_application_services,
    )
    headers = {"Host": "api.example.invalid"}

    with TestClient(app) as client:
        responses = (
            client.get("/api/v1/activities", headers=headers),
            client.post(
                "/api/v1/questionnaire",
                json={"activity_code": "restaurant"},
                headers=headers,
            ),
            client.post(
                "/api/v1/checklist",
                json={"activity_code": "restaurant", "facts": {}},
                headers=headers,
            ),
            client.post(
                "/api/v1/navigator",
                json={"text": "restaurant"},
                headers=headers,
            ),
        )

    assert {response.status_code for response in responses} == {503}
    assert {response.json()["error"]["code"] for response in responses} == {
        "UNPUBLISHED_CATALOG_DISABLED"
    }


__all__: list[str] = []
