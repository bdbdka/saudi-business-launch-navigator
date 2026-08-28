"""Clean AI failures that never masquerade as regulatory answers."""

from enum import StrEnum


class AIErrorCode(StrEnum):
    UNAVAILABLE = "AI_UNAVAILABLE"
    TIMEOUT = "AI_TIMEOUT"
    AUTHENTICATION = "AI_AUTHENTICATION_FAILED"
    RATE_LIMITED = "AI_RATE_LIMITED"
    MALFORMED_RESPONSE = "AI_MALFORMED_RESPONSE"
    INVALID_OUTPUT = "AI_INVALID_OUTPUT"
    SENSITIVE_INPUT = "SENSITIVE_INPUT_REJECTED"


class InterpretationError(Exception):
    """Base class carrying a safe, non-secret technical error code."""

    def __init__(self, code: AIErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class AIUnavailableError(InterpretationError):
    pass


class AIResponseError(InterpretationError):
    pass


class AIOutputValidationError(InterpretationError):
    pass


class SensitiveInputError(InterpretationError):
    pass


__all__ = [
    "AIErrorCode",
    "AIOutputValidationError",
    "AIResponseError",
    "AIUnavailableError",
    "InterpretationError",
    "SensitiveInputError",
]
