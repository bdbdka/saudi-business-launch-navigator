"""Stable safe API error envelopes and domain-exception mapping."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from saudi_business_launch_navigator.api.schemas import (
    APIError,
    APIErrorResponse,
    ErrorDetail,
)
from saudi_business_launch_navigator.checklist.exceptions import (
    BusinessProfileError,
    RegulatoryCatalogError,
    UnsupportedActivityError,
)
from saudi_business_launch_navigator.interpretation.exceptions import (
    AIErrorCode,
    InterpretationError,
)
from saudi_business_launch_navigator.portfolio_demo.store import PortfolioDemoDatabaseError

logger = logging.getLogger(__name__)


class APIRequestError(Exception):
    def __init__(self, *, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.safe_message = message


def install_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(APIRequestError, _api_request_error)
    app.add_exception_handler(UnsupportedActivityError, _unsupported_activity)
    app.add_exception_handler(BusinessProfileError, _invalid_profile)
    app.add_exception_handler(RegulatoryCatalogError, _regulatory_state_error)
    app.add_exception_handler(PortfolioDemoDatabaseError, _portfolio_demo_state_error)
    app.add_exception_handler(InterpretationError, _interpretation_error)
    app.add_exception_handler(StarletteHTTPException, _http_error)
    app.add_exception_handler(Exception, _unexpected_error)


async def _validation_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    details = tuple(
        ErrorDetail(
            field=".".join(str(value) for value in error["loc"]),
            error_type=str(error["type"]),
        )
        for error in exc.errors()
    )
    return _response(
        request,
        status_code=422,
        code="VALIDATION_ERROR",
        message="The request did not match the required API schema.",
        details=details,
    )


async def _api_request_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, APIRequestError)
    if exc.code == "UNPUBLISHED_CATALOG_DISABLED":
        _log_controlled_event(request, "catalog_exposure_blocked", exc.code)
    return _response(
        request,
        status_code=exc.status_code,
        code=exc.code,
        message=exc.safe_message,
    )


async def _unsupported_activity(request: Request, exc: Exception) -> JSONResponse:
    return _response(
        request,
        status_code=400,
        code="INVALID_ACTIVITY",
        message="The selected activity is not supported by the governed catalog.",
    )


async def _invalid_profile(request: Request, exc: Exception) -> JSONResponse:
    return _response(
        request,
        status_code=400,
        code="INVALID_FACT",
        message="The business profile contains an unsupported governed fact.",
    )


async def _regulatory_state_error(request: Request, exc: Exception) -> JSONResponse:
    _log_exception(request, exc, "regulatory_state_invalid")
    return _response(
        request,
        status_code=503,
        code="REGULATORY_STATE_INVALID",
        message="The governed catalog is temporarily unavailable for safe evaluation.",
    )


async def _portfolio_demo_state_error(request: Request, exc: Exception) -> JSONResponse:
    _log_exception(request, exc, "portfolio_demo_identity_invalid")
    return _response(
        request,
        status_code=503,
        code="CATALOG_IDENTITY_UNVERIFIED",
        message="The portfolio demonstration catalog is temporarily unavailable.",
    )


async def _interpretation_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, InterpretationError)
    status_code = 422 if exc.code is AIErrorCode.SENSITIVE_INPUT else 503
    if status_code == 503:
        _log_controlled_event(request, "optional_ai_unavailable", exc.code.value)
    return _response(
        request,
        status_code=status_code,
        code=exc.code.value,
        message=(
            "Remove personal identifiers and submit only non-personal business facts."
            if exc.code is AIErrorCode.SENSITIVE_INPUT
            else "The bounded AI service is temporarily unavailable."
        ),
    )


async def _http_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    code = "NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR"
    message = (
        "The requested endpoint was not found." if exc.status_code == 404 else "Request failed."
    )
    return _response(request, status_code=exc.status_code, code=code, message=message)


async def _unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    _log_exception(request, exc, "unexpected_api_error")
    return _response(
        request,
        status_code=500,
        code="INTERNAL_ERROR",
        message="An unexpected internal error occurred.",
    )


def _response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    details: tuple[ErrorDetail, ...] = (),
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    payload = APIErrorResponse(
        error=APIError(
            code=code,
            message=message,
            details=details,
            request_id=request_id,
        )
    )
    headers = {
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
        "Cache-Control": "no-store",
    }
    if request_id is not None:
        headers["X-Request-ID"] = request_id
    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(mode="json"),
        headers=headers,
    )


def _log_exception(request: Request, exc: Exception, event: str) -> None:
    logger.error(
        "API request failed safely",
        extra={
            "event": event,
            "component": "api",
            "error_type": type(exc).__name__,
            "request_id": getattr(request.state, "request_id", "unavailable"),
        },
    )


def _log_controlled_event(request: Request, event: str, error_type: str) -> None:
    """Record an expected fail-closed condition without request content."""

    logger.warning(
        "API request stopped at a controlled safety boundary",
        extra={
            "event": event,
            "component": "api",
            "error_type": error_type,
            "request_id": getattr(request.state, "request_id", "unavailable"),
        },
    )


__all__ = ["APIRequestError", "install_exception_handlers"]
