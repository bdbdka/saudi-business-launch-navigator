"""Provider-independent AI ports isolated from deterministic applicability."""

from typing import Protocol

from saudi_business_launch_navigator.interpretation.models import (
    ExplanationCandidate,
    ExplanationContext,
    InterpretationCandidate,
)


class AIInterpreter(Protocol):
    async def interpret(self, user_text: str) -> InterpretationCandidate:
        """Return strict but still untrusted language-understanding candidates."""


class AIExplainer(Protocol):
    async def explain(self, context: ExplanationContext) -> ExplanationCandidate:
        """Return bounded prose for an already authoritative checklist."""


__all__ = ["AIExplainer", "AIInterpreter"]
