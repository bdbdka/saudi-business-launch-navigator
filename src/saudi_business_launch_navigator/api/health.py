"""Liveness and database-readiness API endpoints."""

from typing import Literal

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from saudi_business_launch_navigator.core.config import CatalogDataMode, Settings
from saudi_business_launch_navigator.db.health import database_is_available
from saudi_business_launch_navigator.portfolio_demo.store import (
    PortfolioDemoDatabaseError,
    assert_portfolio_demo_runtime_access,
    verify_portfolio_demo_database,
)

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    """Public health response without internal error or configuration details."""

    status: Literal["healthy", "unavailable"]
    service: str
    checks: dict[str, Literal["available", "unavailable"]] | None = None


@router.get("/live", response_model=HealthResponse)
async def liveness() -> HealthResponse:
    """Report process liveness without touching PostgreSQL."""
    return HealthResponse(status="healthy", service="api")


@router.get(
    "/ready",
    response_model=HealthResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": HealthResponse}},
)
async def readiness(request: Request) -> HealthResponse | JSONResponse:
    """Report whether the application can execute a PostgreSQL query."""
    engine: AsyncEngine | None = getattr(request.app.state, "database_engine", None)
    settings: Settings | None = getattr(request.app.state, "settings", None)
    available = engine is not None and await database_is_available(engine)
    if (
        available
        and engine is not None
        and settings is not None
        and settings.catalog_mode is CatalogDataMode.PORTFOLIO_DEMO_CATALOG
    ):
        try:
            await verify_portfolio_demo_database(engine, settings)
            if settings.environment == "production":
                await assert_portfolio_demo_runtime_access(engine)
        except (PortfolioDemoDatabaseError, SQLAlchemyError):
            available = False
    if available:
        return HealthResponse(
            status="healthy",
            service="api",
            checks={"database": "available"},
        )

    response = HealthResponse(
        status="unavailable",
        service="api",
        checks={"database": "unavailable"},
    )
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=response.model_dump(),
    )
