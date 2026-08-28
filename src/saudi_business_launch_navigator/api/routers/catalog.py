"""Thin deterministic catalog, questionnaire, and checklist routes."""

from typing import Any

from fastapi import APIRouter

from saudi_business_launch_navigator.api.catalog_boundary import (
    CatalogExposurePolicy,
    VerifiedCatalogBoundary,
)
from saudi_business_launch_navigator.api.dependencies import (
    CatalogBoundaryDependency,
    ServicesDependency,
)
from saudi_business_launch_navigator.api.errors import APIRequestError
from saudi_business_launch_navigator.api.schemas import (
    ActivitiesResponse,
    APIErrorResponse,
    CatalogBoundary,
    ChecklistRequest,
    ChecklistResponse,
    QuestionnaireRequest,
    QuestionnaireResponse,
)

router = APIRouter(tags=["deterministic navigator"])
_ERRORS: dict[int | str, dict[str, Any]] = {
    400: {"model": APIErrorResponse, "description": "Unsupported governed input"},
    422: {"model": APIErrorResponse, "description": "Schema validation failure"},
    503: {"model": APIErrorResponse, "description": "Governed catalog unavailable"},
}


@router.get(
    "/activities",
    response_model=ActivitiesResponse,
    summary="List active supported activities",
    description=(
        "Returns governed activity codes and bilingual project labels. The catalog is "
        "INTERNAL_GOVERNED and unpublished."
    ),
    responses={503: _ERRORS[503]},
)
async def list_activities(
    services: ServicesDependency,
    boundary: CatalogBoundaryDependency,
) -> ActivitiesResponse:
    _enforce_catalog_exposure(boundary)
    return ActivitiesResponse(
        metadata=CatalogBoundary.from_verified(boundary),
        activities=await services.activities.list_active(),
    )


@router.post(
    "/questionnaire",
    response_model=QuestionnaireResponse,
    summary="Build the governed questionnaire for an activity",
    description="Builds the minimum questionnaire from verified condition facts.",
    responses=_ERRORS,
)
async def build_questionnaire(
    payload: QuestionnaireRequest,
    services: ServicesDependency,
    boundary: CatalogBoundaryDependency,
) -> QuestionnaireResponse:
    _enforce_catalog_exposure(boundary)
    questionnaire = await services.checklist.build_questionnaire(payload.activity_code.value)
    return QuestionnaireResponse(
        metadata=CatalogBoundary.from_verified(boundary),
        questionnaire=questionnaire,
    )


@router.post(
    "/checklist",
    response_model=ChecklistResponse,
    summary="Generate a deterministic personalized checklist",
    description=(
        "Evaluates a strict BusinessProfile with deterministic rules. No language model "
        "decides applicability."
    ),
    responses=_ERRORS,
)
async def build_checklist(
    payload: ChecklistRequest,
    services: ServicesDependency,
    boundary: CatalogBoundaryDependency,
) -> ChecklistResponse:
    _enforce_catalog_exposure(boundary)
    result = await services.checklist.evaluate_business_profile(
        payload.to_profile(),
        payload.navigation_facts.to_profile(),
    )
    return ChecklistResponse(metadata=CatalogBoundary.from_verified(boundary), result=result)


def _enforce_catalog_exposure(boundary: VerifiedCatalogBoundary) -> None:
    """Never expose the unpublished governed catalog from public production."""
    if boundary.exposure_policy is CatalogExposurePolicy.SYNTHETIC_PORTFOLIO_DEMO:
        if boundary.demo_database is not None:
            return
        raise APIRequestError(
            status_code=503,
            code="CATALOG_IDENTITY_UNVERIFIED",
            message="The portfolio demonstration catalog identity is unavailable.",
        )
    if boundary.exposure_policy is CatalogExposurePolicy.CLOSED_UNPUBLISHED_GOVERNED:
        raise APIRequestError(
            status_code=503,
            code="UNPUBLISHED_CATALOG_DISABLED",
            message="The public regulatory catalog is not authorized for publication.",
        )
    if boundary.exposure_policy is CatalogExposurePolicy.INTERNAL_LOOPBACK_GOVERNED:
        return
    raise APIRequestError(
        status_code=503,
        code="CATALOG_IDENTITY_UNVERIFIED",
        message="The catalog boundary is unavailable.",
    )


__all__ = ["_enforce_catalog_exposure", "router"]
