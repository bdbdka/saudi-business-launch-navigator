"""Thin HTTP adapter around bounded interpretation services."""

from typing import Any

from fastapi import APIRouter

from saudi_business_launch_navigator.api.dependencies import (
    CatalogBoundaryDependency,
    ServicesDependency,
    SettingsDependency,
)
from saudi_business_launch_navigator.api.errors import APIRequestError
from saudi_business_launch_navigator.api.routers.catalog import _enforce_catalog_exposure
from saudi_business_launch_navigator.api.schemas import (
    AIInterpretRequest,
    AIInterpretResponse,
    APIErrorResponse,
    CatalogBoundary,
    NavigatorRequest,
    NavigatorResponse,
)
from saudi_business_launch_navigator.interpretation.exceptions import InterpretationError
from saudi_business_launch_navigator.interpretation.models import InterpretationRequest

router = APIRouter(tags=["bounded AI"])
_AI_ERRORS: dict[int | str, dict[str, Any]] = {
    422: {"model": APIErrorResponse, "description": "Invalid or sensitive input"},
    503: {"model": APIErrorResponse, "description": "Bounded AI unavailable"},
}


@router.post(
    "/ai/interpret",
    response_model=AIInterpretResponse,
    summary="Interpret bounded Arabic or English business facts",
    description=(
        "Returns deterministically validated activity/fact candidates only. It does not "
        "produce or decide regulatory applicability."
    ),
    responses=_AI_ERRORS,
)
async def interpret_text(
    payload: AIInterpretRequest,
    services: ServicesDependency,
    settings: SettingsDependency,
) -> AIInterpretResponse:
    _enforce_text_limit(payload.text, settings.api_max_natural_language_chars)
    if services.interpreter is None:
        raise APIRequestError(
            status_code=503,
            code="AI_UNAVAILABLE",
            message="The bounded AI service is not configured.",
        )
    interpretation = await services.interpreter.interpret(
        InterpretationRequest(user_text=payload.text, language_override=payload.language)
    )
    return AIInterpretResponse(interpretation=interpretation)


@router.post(
    "/navigator",
    response_model=NavigatorResponse,
    summary="Run bounded interpretation and the authoritative checklist flow",
    description=(
        "Separates the authoritative deterministic checklist from non-authoritative AI "
        "explanatory prose. Operates over INTERNAL_GOVERNED unpublished data."
    ),
    responses=_AI_ERRORS,
)
async def navigate(
    payload: NavigatorRequest,
    services: ServicesDependency,
    settings: SettingsDependency,
    boundary: CatalogBoundaryDependency,
) -> NavigatorResponse:
    _enforce_catalog_exposure(boundary)
    _enforce_text_limit(payload.text, settings.api_max_natural_language_chars)
    if services.navigator is None:
        raise APIRequestError(
            status_code=503,
            code="AI_UNAVAILABLE",
            message="The bounded AI service is not configured.",
        )
    result = await services.navigator.process(
        InterpretationRequest(user_text=payload.text, language_override=payload.language),
        payload.existing_profile.to_profile() if payload.existing_profile is not None else None,
    )
    if result.interpretation is None:
        assert result.ai_error is not None
        raise InterpretationError(result.ai_error.code, result.ai_error.message)
    return NavigatorResponse(
        metadata=CatalogBoundary.from_verified(boundary),
        interpretation=result.interpretation,
        authoritative_result=result.checklist,
        explanation=result.explanation,
        clarifications=result.clarifications,
        coverage_limitation=result.coverage_limitation,
        ai_error=result.ai_error,
    )


def _enforce_text_limit(value: str, maximum: int) -> None:
    if len(value) > maximum:
        raise APIRequestError(
            status_code=422,
            code="INPUT_TOO_LONG",
            message="Natural-language input exceeds the configured maximum length.",
        )


__all__ = ["router"]
