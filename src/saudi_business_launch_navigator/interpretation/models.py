"""Strict schemas for bounded bilingual interpretation and explanation."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

from saudi_business_launch_navigator.checklist.models import (
    ApplicabilityStatus,
    BusinessChecklistResult,
    BusinessProfile,
    ChecklistItem,
    CoverageNotice,
    QuestionnaireItem,
)
from saudi_business_launch_navigator.interpretation.exceptions import AIErrorCode

ShortText = Annotated[str, Field(min_length=1, max_length=240)]
ExplanationText = Annotated[str, Field(min_length=1, max_length=800)]


class InterpretationModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class InteractionLanguage(StrEnum):
    ARABIC = "ar"
    ENGLISH = "en"


class SupportedActivity(StrEnum):
    COFFEE_SHOP = "coffee_shop"
    RESTAURANT = "restaurant"
    CLOUD_KITCHEN = "cloud_kitchen"


class GovernedFactCode(StrEnum):
    HAS_FOOD_ESTABLISHMENT_WORKERS = "has_food_establishment_workers"
    HAS_EMPLOYEES = "has_employees"
    GOSI_COVERAGE_CONDITIONS_MET = "gosi_coverage_conditions_met"
    OFFERS_HOME_DELIVERY = "offers_home_delivery"
    USES_PUBLIC_SIDEWALK_FOR_CUSTOMER_SERVICE = "uses_public_sidewalk_for_customer_service"


class MappingBasis(StrEnum):
    EXPLICIT_STATEMENT = "explicit_statement"
    DIRECT_SEMANTIC_EQUIVALENT = "direct_semantic_equivalent"
    UNRESOLVED = "unresolved"


class ClarificationTarget(StrEnum):
    ACTIVITY_CODE = "activity_code"
    HAS_FOOD_ESTABLISHMENT_WORKERS = "has_food_establishment_workers"
    ZATCA_CONFIRMED_MANDATORY_VAT_REGISTRATION_APPLIES = (
        "zatca_confirmed_mandatory_vat_registration_applies"
    )
    HAS_EMPLOYEES = "has_employees"
    GOSI_COVERAGE_CONDITIONS_MET = "gosi_coverage_conditions_met"
    OFFERS_HOME_DELIVERY = "offers_home_delivery"
    USES_PUBLIC_SIDEWALK_FOR_CUSTOMER_SERVICE = "uses_public_sidewalk_for_customer_service"


class InterpretationRequest(InterpretationModel):
    user_text: Annotated[str, Field(min_length=1, max_length=2000)]
    language_override: InteractionLanguage | None = None


class FactCandidate(InterpretationModel):
    code: GovernedFactCode
    value: StrictBool | None
    evidence_text: ShortText
    mapping_basis: MappingBasis

    @model_validator(mode="after")
    def unknown_must_be_unresolved(self) -> FactCandidate:
        if (self.value is None) != (self.mapping_basis is MappingBasis.UNRESOLVED):
            raise ValueError("null value and unresolved mapping basis must appear together")
        return self


class InterpretationCandidate(InterpretationModel):
    """Structured model output; still untrusted until deterministic validation."""

    schema_version: Literal["interpretation.v1"]
    detected_language: InteractionLanguage
    activity_candidate: SupportedActivity | None
    activity_evidence: ShortText | None
    fact_candidates: Annotated[tuple[FactCandidate, ...], Field(max_length=8)]
    clarification_needed: bool
    clarification_targets: Annotated[tuple[ClarificationTarget, ...], Field(max_length=5)]
    unsupported_or_unmapped_statements: Annotated[tuple[ShortText, ...], Field(max_length=10)]

    @model_validator(mode="after")
    def activity_evidence_matches_candidate(self) -> InterpretationCandidate:
        if (self.activity_candidate is None) != (self.activity_evidence is None):
            raise ValueError("activity candidate and evidence must appear together")
        return self


class ValidatedFact(InterpretationModel):
    code: GovernedFactCode
    value: StrictBool
    evidence_text: ShortText
    mapping_basis: Literal[
        MappingBasis.EXPLICIT_STATEMENT,
        MappingBasis.DIRECT_SEMANTIC_EQUIVALENT,
    ]


class ValidatedInterpretation(InterpretationModel):
    language: InteractionLanguage
    activity_code: SupportedActivity | None
    facts: tuple[ValidatedFact, ...]
    clarification_needed: bool
    clarification_targets: tuple[ClarificationTarget, ...]
    unsupported_or_unmapped_statements: tuple[ShortText, ...]

    def to_business_profile(self) -> BusinessProfile:
        if self.activity_code is None:
            raise ValueError("activity clarification is required")
        return BusinessProfile(
            activity_code=self.activity_code.value,
            facts={fact.code.value: fact.value for fact in self.facts},
        )


class ExplanationItemCandidate(InterpretationModel):
    item_index: Annotated[int, Field(ge=0, le=100)]
    summary: ExplanationText
    why_status: ExplanationText


class ExplanationCandidate(InterpretationModel):
    schema_version: Literal["explanation.v1"]
    language: InteractionLanguage
    items: Annotated[tuple[ExplanationItemCandidate, ...], Field(max_length=50)]
    coverage_summary: ExplanationText


class AuthoritativeItemExplanation(InterpretationModel):
    """Authoritative identity stays attached to bounded AI prose."""

    item: ChecklistItem
    summary: str
    why_status: str
    next_question: QuestionnaireItem | None


class ChecklistExplanation(InterpretationModel):
    language: InteractionLanguage
    items: tuple[AuthoritativeItemExplanation, ...]
    authoritative_coverage: CoverageNotice
    ai_coverage_summary: str


class ClarificationPrompt(InterpretationModel):
    target: ClarificationTarget
    question_ar: str
    question_en: str
    project_authored: Literal[True] = True


class CoverageLimitation(InterpretationModel):
    unresolved_topics: tuple[str, ...]
    message_ar: str
    message_en: str
    supported_determination: Literal[False] = False


class AIErrorInfo(InterpretationModel):
    code: AIErrorCode
    message: str


class InterpretationResult(InterpretationModel):
    interpretation: ValidatedInterpretation | None
    profile: BusinessProfile | None
    checklist: BusinessChecklistResult | None
    explanation: ChecklistExplanation | None
    clarifications: tuple[ClarificationPrompt, ...]
    coverage_limitation: CoverageLimitation | None
    ai_error: AIErrorInfo | None


class ExplanationContextItem(InterpretationModel):
    item_index: int
    applicability_status: ApplicabilityStatus
    reason_code: str
    project_title: str
    project_description: str
    authority_name: str
    missing_fact_codes: tuple[str, ...]
    source_codes: tuple[str, ...]


class ExplanationContext(InterpretationModel):
    language: InteractionLanguage
    items: tuple[ExplanationContextItem, ...]
    coverage_status: str
    coverage_message: str
    unresolved_topics: tuple[str, ...]


__all__ = [
    "AIErrorInfo",
    "AuthoritativeItemExplanation",
    "ChecklistExplanation",
    "ClarificationPrompt",
    "ClarificationTarget",
    "CoverageLimitation",
    "ExplanationCandidate",
    "ExplanationContext",
    "ExplanationContextItem",
    "ExplanationItemCandidate",
    "FactCandidate",
    "GovernedFactCode",
    "InteractionLanguage",
    "InterpretationCandidate",
    "InterpretationRequest",
    "InterpretationResult",
    "MappingBasis",
    "SupportedActivity",
    "ValidatedFact",
    "ValidatedInterpretation",
]
