"""FastAPI dependency accessors for lifecycle-owned application services."""

from typing import Annotated, cast

from fastapi import Depends, Request

from saudi_business_launch_navigator.api.catalog_boundary import VerifiedCatalogBoundary
from saudi_business_launch_navigator.api.container import ApplicationServices
from saudi_business_launch_navigator.core.config import Settings


def get_services(request: Request) -> ApplicationServices:
    return cast("ApplicationServices", request.app.state.services)


def get_api_settings(request: Request) -> Settings:
    return cast("Settings", request.app.state.settings)


def get_catalog_boundary(request: Request) -> VerifiedCatalogBoundary:
    return cast("VerifiedCatalogBoundary", request.app.state.catalog_boundary)


ServicesDependency = Annotated[ApplicationServices, Depends(get_services)]
SettingsDependency = Annotated[Settings, Depends(get_api_settings)]
CatalogBoundaryDependency = Annotated[VerifiedCatalogBoundary, Depends(get_catalog_boundary)]

__all__ = [
    "CatalogBoundaryDependency",
    "ServicesDependency",
    "SettingsDependency",
    "get_api_settings",
    "get_catalog_boundary",
    "get_services",
]
