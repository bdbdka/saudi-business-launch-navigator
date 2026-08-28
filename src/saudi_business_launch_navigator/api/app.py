"""FastAPI application factory and lifecycle ownership."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncEngine
from starlette.middleware.trustedhost import TrustedHostMiddleware

from saudi_business_launch_navigator.api.catalog_boundary import (
    VerifiedCatalogBoundary,
    resolve_catalog_boundary,
)
from saudi_business_launch_navigator.api.container import (
    ApplicationServices,
    build_application_services,
)
from saudi_business_launch_navigator.api.errors import install_exception_handlers
from saudi_business_launch_navigator.api.health import router as health_router
from saudi_business_launch_navigator.api.middleware import RequestContextMiddleware
from saudi_business_launch_navigator.api.routers.ai import router as ai_router
from saudi_business_launch_navigator.api.routers.catalog import router as catalog_router
from saudi_business_launch_navigator.core.config import Settings, get_settings
from saudi_business_launch_navigator.core.logging import configure_logging
from saudi_business_launch_navigator.db.engine import (
    create_database_engine,
    dispose_database_engine,
)

EngineFactory = Callable[[Settings], AsyncEngine]
ServicesFactory = Callable[
    [Settings, AsyncEngine, VerifiedCatalogBoundary],
    ApplicationServices,
]
API_VERSION_PREFIX = "/api/v1"


def create_app(
    settings: Settings | None = None,
    engine_factory: EngineFactory = create_database_engine,
    services_factory: ServicesFactory = build_application_services,
) -> FastAPI:
    """Create an isolated API whose routes only adapt application services."""

    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings.log_level)
    logger = logging.getLogger(__name__)

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        engine = engine_factory(resolved_settings)
        application.state.database_engine = engine
        application.state.settings = resolved_settings
        try:
            boundary = await resolve_catalog_boundary(
                resolved_settings,
                engine,
            )
            application.state.catalog_boundary = boundary
            application.state.services = services_factory(resolved_settings, engine, boundary)
            logger.info(
                "Navigator API started",
                extra={
                    "event": "api_started",
                    "component": "api",
                    "environment": resolved_settings.environment,
                    "catalog_mode": resolved_settings.catalog_mode.value,
                },
            )
            yield
        finally:
            await dispose_database_engine(engine)
            application.state.database_engine = None
            logger.info(
                "API stopped",
                extra={
                    "event": "api_stopped",
                    "component": "api",
                    "environment": resolved_settings.environment,
                },
            )

    application = FastAPI(
        title=(
            "Saudi Business Launch Navigator — Portfolio Demo API"
            if resolved_settings.catalog_mode.value == "PORTFOLIO_DEMO_CATALOG"
            else "Saudi Business Launch Navigator — Internal API"
        ),
        version="1.0.0",
        description=(
            "Deterministic decision-support API. Governed real content remains unpublished; "
            "portfolio-demo mode uses explicitly synthetic sample data. It is not a government "
            "service, legal advice, or a guarantee of compliance, licensing, timing, or cost."
        ),
        debug=False,
        docs_url="/docs" if resolved_settings.api_docs_enabled else None,
        redoc_url="/redoc" if resolved_settings.api_docs_enabled else None,
        openapi_url="/openapi.json" if resolved_settings.api_docs_enabled else None,
        lifespan=lifespan,
    )
    application.state.settings = resolved_settings
    application.add_middleware(
        RequestContextMiddleware,
        maximum_request_bytes=resolved_settings.api_max_request_bytes,
    )
    application.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=list(resolved_settings.allowed_hosts),
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(resolved_settings.cors_allowed_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )
    install_exception_handlers(application)
    application.include_router(health_router)
    application.include_router(catalog_router, prefix=API_VERSION_PREFIX)
    application.include_router(ai_router, prefix=API_VERSION_PREFIX)
    return application


__all__ = ["API_VERSION_PREFIX", "create_app"]
