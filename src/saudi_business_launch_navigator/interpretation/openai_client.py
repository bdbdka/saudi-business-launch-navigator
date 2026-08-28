"""OpenAI Responses API adapter for the bounded interpretation ports."""

from __future__ import annotations

import logging
from typing import Any, cast

from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AsyncOpenAI,
    AuthenticationError,
    RateLimitError,
)
from pydantic import ValidationError

from saudi_business_launch_navigator.core.config import Settings
from saudi_business_launch_navigator.interpretation.exceptions import (
    AIErrorCode,
    AIResponseError,
    AIUnavailableError,
)
from saudi_business_launch_navigator.interpretation.models import (
    ExplanationCandidate,
    ExplanationContext,
    InterpretationCandidate,
)
from saudi_business_launch_navigator.interpretation.prompts import (
    EXPLAINER_INSTRUCTIONS,
    INTERPRETER_INSTRUCTIONS,
)

logger = logging.getLogger(__name__)


class OpenAIResponsesAdapter:
    """Use strict Pydantic parsing while keeping OpenAI outside core logic."""

    def __init__(self, settings: Settings, client: Any | None = None) -> None:
        self._settings = settings
        if client is not None:
            self._client = client
            return
        if settings.openai_api_key is None:
            raise AIUnavailableError(
                AIErrorCode.UNAVAILABLE,
                "AI interpretation is unavailable because no API key is configured.",
            )
        self._client = AsyncOpenAI(
            api_key=settings.openai_api_key.get_secret_value(),
            timeout=settings.openai_timeout_seconds,
        )

    async def interpret(self, user_text: str) -> InterpretationCandidate:
        return await self._parse(
            instructions=INTERPRETER_INSTRUCTIONS,
            input_value=user_text,
            response_model=InterpretationCandidate,
        )

    async def explain(self, context: ExplanationContext) -> ExplanationCandidate:
        return await self._parse(
            instructions=EXPLAINER_INSTRUCTIONS,
            input_value=context.model_dump_json(),
            response_model=ExplanationCandidate,
        )

    async def _parse[ResponseModel: (InterpretationCandidate, ExplanationCandidate)](
        self,
        *,
        instructions: str,
        input_value: str,
        response_model: type[ResponseModel],
    ) -> ResponseModel:
        try:
            response = await self._client.responses.parse(
                model=self._settings.openai_model,
                instructions=instructions,
                input=input_value,
                text_format=response_model,
                max_output_tokens=self._settings.openai_max_output_tokens,
                store=False,
            )
            parsed = response.output_parsed
            if parsed is None or not isinstance(parsed, response_model):
                raise AIResponseError(
                    AIErrorCode.MALFORMED_RESPONSE,
                    "The AI service did not return the required structured response.",
                )
            return cast("ResponseModel", parsed)
        except AIResponseError:
            raise
        except APITimeoutError as exc:
            self._log_failure(exc)
            raise AIUnavailableError(AIErrorCode.TIMEOUT, "The AI service timed out.") from exc
        except AuthenticationError as exc:
            self._log_failure(exc)
            raise AIUnavailableError(
                AIErrorCode.AUTHENTICATION,
                "The AI service could not authenticate.",
            ) from exc
        except RateLimitError as exc:
            self._log_failure(exc)
            raise AIUnavailableError(
                AIErrorCode.RATE_LIMITED,
                "The AI service is temporarily rate limited.",
            ) from exc
        except APIConnectionError as exc:
            self._log_failure(exc)
            raise AIUnavailableError(
                AIErrorCode.UNAVAILABLE,
                "The AI service is temporarily unavailable.",
            ) from exc
        except (APIError, ValidationError, TypeError, ValueError) as exc:
            self._log_failure(exc)
            raise AIResponseError(
                AIErrorCode.MALFORMED_RESPONSE,
                "The AI service returned an unusable structured response.",
            ) from exc

    @staticmethod
    def _log_failure(exc: Exception) -> None:
        logger.warning(
            "Bounded AI request failed",
            extra={
                "event": "ai_interpretation_failure",
                "component": "openai_responses_adapter",
                "error_type": type(exc).__name__,
            },
        )


__all__ = ["OpenAIResponsesAdapter"]
