"""Strict public data contracts for the internal deterministic checklist engine."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt

from saudi_business_launch_navigator.checklist.exceptions import DuplicateFactCodeError
from saudi_business_launch_navigator.rules.conditions import FactDataType, TruthValue

FactCode = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]*$")]
ActivityCode = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]*$")]


class ApplicabilityStatus(StrEnum):
    """The only three deterministic applicability outcomes."""

    APPLIES = "APPLIES"
    DOES_NOT_APPLY = "DOES_NOT_APPLY"
    NEEDS_INFORMATION = "NEEDS_INFORMATION"


class ApplicabilityReasonCode(StrEnum):
    """Stable explanations for deterministic checklist placement."""

    UNCONDITIONAL_CURRENT_REQUIREMENT = "UNCONDITIONAL_CURRENT_REQUIREMENT"
    CONDITION_TRUE = "CONDITION_TRUE"
    CONDITION_FALSE = "CONDITION_FALSE"
    MISSING_REQUIRED_FACT = "MISSING_REQUIRED_FACT"


class CatalogMode(StrEnum):
    """Catalog source exposed by the application."""

    INTERNAL_GOVERNED = "INTERNAL_GOVERNED"
    PORTFOLIO_DEMO = "PORTFOLIO_DEMO"


class CoverageStatus(StrEnum):
    """Coverage statement for the currently governed internal catalog."""

    PARTIAL_VERIFIED_COVERAGE = "PARTIAL_VERIFIED_COVERAGE"


class TextOrigin(StrEnum):
    """Distinguish interface copy from official evidence."""

    PROJECT_AUTHORED = "PROJECT_AUTHORED"


class QuestionPurpose(StrEnum):
    """Keep legal applicability inputs separate from navigation-only inputs."""

    APPLICABILITY = "APPLICABILITY"
    NAVIGATION = "NAVIGATION"


class OwnershipInvestorRoute(StrEnum):
    SAUDI_PERSON_OR_SAUDI_OWNED_ENTITY = "saudi_person_or_saudi_owned_entity"
    GCC_PERSON_OR_WHOLLY_GCC_OWNED_ENTITY = "gcc_person_or_wholly_gcc_owned_entity"
    FOREIGN_LEGAL_ENTITY_OR_MIXED_FOREIGN_OWNERSHIP = (
        "foreign_legal_entity_or_mixed_foreign_ownership"
    )
    PREMIUM_RESIDENCY_INDIVIDUAL = "premium_residency_individual"
    OTHER = "other"


class PlannedLegalForm(StrEnum):
    INDIVIDUAL_ESTABLISHMENT = "individual_establishment"
    LIMITED_LIABILITY_COMPANY = "limited_liability_company"
    OTHER = "other"


class JourneyRoutingStatus(StrEnum):
    ROUTED = "ROUTED"
    NEEDS_INFORMATION = "NEEDS_INFORMATION"


class ChecklistModel(BaseModel):
    """Immutable strict base for deterministic serialized results."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class BusinessProfile(ChecklistModel):
    """Non-persistent business activity and governed fact answers."""

    activity_code: ActivityCode
    facts: dict[FactCode, StrictBool | None] = Field(default_factory=dict)

    @classmethod
    def from_fact_pairs(
        cls,
        *,
        activity_code: str,
        fact_pairs: Iterable[tuple[str, bool | None]],
    ) -> BusinessProfile:
        """Build a profile while rejecting duplicate codes before mapping conversion."""

        facts: dict[str, bool | None] = {}
        for code, value in fact_pairs:
            if code in facts:
                raise DuplicateFactCodeError(f"duplicate fact code: {code}")
            facts[code] = value
        return cls(activity_code=activity_code, facts=facts)


class NavigationProfile(ChecklistModel):
    """Non-persistent navigation inputs that can never enter applicability."""

    ownership_investor_route: OwnershipInvestorRoute | None = None
    planned_legal_form: PlannedLegalForm | None = None
    has_selected_business_premises: StrictBool | None = None

    def as_fact_values(self) -> dict[FactCode, str | bool | None]:
        return {
            "ownership_investor_route": self.ownership_investor_route,
            "planned_legal_form": self.planned_legal_form,
            "has_selected_business_premises": self.has_selected_business_premises,
        }


class ActivitySummary(ChecklistModel):
    code: ActivityCode
    name_ar: str
    name_en: str


class QuestionnaireAnswerLabels(ChecklistModel):
    """Project-authored labels for the three Boolean/unknown answer values."""

    true_ar: str
    true_en: str
    false_ar: str
    false_en: str
    unknown_ar: str
    unknown_en: str


class QuestionnaireOption(ChecklistModel):
    value: str
    label_ar: str
    label_en: str


class QuestionnaireItem(ChecklistModel):
    """Project-authored question tied to one governed fact definition."""

    fact_code: FactCode
    fact_version: int
    data_type: FactDataType
    purpose: QuestionPurpose = QuestionPurpose.APPLICABILITY
    allows_unknown: bool = True
    question_ar: str
    question_en: str
    help_text_ar: str
    help_text_en: str
    answer_labels: QuestionnaireAnswerLabels | None = None
    options: tuple[QuestionnaireOption, ...] = ()
    unknown_label_ar: str = "لست متأكدًا"
    unknown_label_en: str = "Not sure"
    text_origin: TextOrigin = TextOrigin.PROJECT_AUTHORED


class QuestionnaireDefinition(ChecklistModel):
    activity: ActivitySummary
    questions: tuple[QuestionnaireItem, ...]


class AuthorityTrace(ChecklistModel):
    authority_id: UUID
    code: str
    name_ar: str
    name_en: str | None
    verification_status: str
    last_verified_at: datetime | None
    next_review_at: datetime | None


class SourceTrace(ChecklistModel):
    """Source identity and reviewed-version metadata without copying quotations."""

    requirement_source_id: UUID
    source_id: UUID
    source_code: str
    official_title_ar: str | None
    official_title_en: str | None
    source_role: str
    relationship_status: str
    canonical_url: str
    canonical_host: str
    source_verification_status: str
    source_last_verified_at: datetime | None
    source_next_review_at: datetime | None
    source_version_id: UUID
    source_version_number: int
    reviewed_url: str
    resolved_url: str
    source_version_review_status: str
    source_version_is_current: bool
    source_version_last_verified_at: datetime | None
    source_version_next_review_at: datetime | None
    excerpt_locator: str | None


class PlatformTrace(ChecklistModel):
    platform_id: UUID
    code: str
    name_ar: str
    name_en: str | None


class GovernedSourceTrace(ChecklistModel):
    """Reusable safe source trace for navigation and actionability."""

    source_id: UUID
    source_code: str
    official_title_ar: str | None
    official_title_en: str | None
    official_url: str
    canonical_host: str
    source_version_id: UUID
    source_version_number: int
    authority: AuthorityTrace
    platform: PlatformTrace | None
    last_verified_at: datetime
    next_review_at: datetime


class JourneyDestination(ChecklistModel):
    code: str
    destination_kind: str
    guidance_ar: str
    guidance_en: str | None
    what_to_verify_ar: str
    what_to_verify_en: str | None
    is_primary: bool
    source: GovernedSourceTrace


class JourneyGuidance(ChecklistModel):
    """A navigation conclusion that never represents legal applicability."""

    topic_code: str
    topic_version_id: UUID
    activity_code: ActivityCode
    title_ar: str
    title_en: str | None
    coverage_state: str
    verified_summary_ar: str | None
    verified_summary_en: str | None
    limitation_summary_ar: str | None
    limitation_summary_en: str | None
    what_to_verify_ar: str | None
    what_to_verify_en: str | None
    routing_status: JourneyRoutingStatus
    destinations: tuple[JourneyDestination, ...]


class MissingNavigationInformation(ChecklistModel):
    """Unknown routing input, deliberately distinct from regulatory NEEDS_INFORMATION."""

    fact_code: FactCode
    question: QuestionnaireItem
    affected_topic_codes: tuple[str, ...]


class ActionabilityOfficialDestination(ChecklistModel):
    kind: Literal["official_destination"]
    label_ar: str
    label_en: str | None = None


class ActionabilityText(ChecklistModel):
    kind: Literal["text"]
    text_ar: str
    text_en: str | None = None


class ActionabilityMoney(ChecklistModel):
    kind: Literal["money"]
    amount_minor: Annotated[StrictInt, Field(ge=0)]
    currency: Literal["SAR"]
    label_ar: str
    label_en: str | None = None


ActionabilityValue = Annotated[
    ActionabilityOfficialDestination | ActionabilityText | ActionabilityMoney,
    Field(discriminator="kind"),
]


class ActionabilityItem(ChecklistModel):
    code: str
    actionability_version_id: UUID
    version_number: int
    requirement_version_id: UUID
    detail_type: str
    display_order: int
    label_ar: str
    label_en: str
    value: ActionabilityValue
    source: GovernedSourceTrace
    last_verified_at: datetime
    next_review_at: datetime


class EvaluatedFactTrace(ChecklistModel):
    """Project-authored question and exact in-memory value used by a condition."""

    fact_code: FactCode
    question_ar: str
    question_en: str
    supplied_value: StrictBool | None
    answer_labels: QuestionnaireAnswerLabels
    text_origin: TextOrigin = TextOrigin.PROJECT_AUTHORED


class ChecklistItem(ChecklistModel):
    """One traceable deterministic result for one current requirement version."""

    requirement_code: str
    requirement_version_id: UUID
    requirement_version: int
    project_arabic_title: str
    project_arabic_description: str
    project_english_title: str | None
    project_english_description: str | None
    authority: AuthorityTrace
    activity_code: ActivityCode
    applicability_status: ApplicabilityStatus
    reason_code: ApplicabilityReasonCode
    condition_result: TruthValue | None
    missing_fact_codes: tuple[FactCode, ...]
    evaluated_facts: tuple[EvaluatedFactTrace, ...]
    condition_expression_sha256: str | None
    sources: tuple[SourceTrace, ...]
    regulatory_status: str
    actionability: tuple[ActionabilityItem, ...] = ()


class CoverageNotice(ChecklistModel):
    coverage_status: CoverageStatus = CoverageStatus.PARTIAL_VERIFIED_COVERAGE
    message_ar: str
    message_en: str
    unresolved_topics: tuple[str, ...]
    source_artifact_id: str
    source_artifact_fingerprint: str


class RegulatorySnapshot(ChecklistModel):
    catalog_mode: CatalogMode = CatalogMode.INTERNAL_GOVERNED
    migration_revision: str
    catalog_fingerprint: str
    requirement_version_ids: tuple[UUID, ...]
    fact_definition_ids: tuple[UUID, ...]
    publication_count: int


class BusinessChecklistResult(ChecklistModel):
    activity: ActivitySummary
    applies: tuple[ChecklistItem, ...]
    does_not_apply: tuple[ChecklistItem, ...]
    needs_information: tuple[ChecklistItem, ...]
    questions_needed: tuple[QuestionnaireItem, ...]
    journey_guidance: tuple[JourneyGuidance, ...] = ()
    missing_navigation_information: tuple[MissingNavigationInformation, ...] = ()
    coverage_notice: CoverageNotice
    regulatory_snapshot: RegulatorySnapshot


__all__ = [
    "ActionabilityItem",
    "ActionabilityMoney",
    "ActionabilityOfficialDestination",
    "ActionabilityText",
    "ActionabilityValue",
    "ActivitySummary",
    "ApplicabilityReasonCode",
    "ApplicabilityStatus",
    "BusinessChecklistResult",
    "BusinessProfile",
    "CatalogMode",
    "ChecklistItem",
    "CoverageNotice",
    "CoverageStatus",
    "EvaluatedFactTrace",
    "GovernedSourceTrace",
    "JourneyDestination",
    "JourneyGuidance",
    "JourneyRoutingStatus",
    "MissingNavigationInformation",
    "NavigationProfile",
    "OwnershipInvestorRoute",
    "PlannedLegalForm",
    "PlatformTrace",
    "QuestionPurpose",
    "QuestionnaireAnswerLabels",
    "QuestionnaireDefinition",
    "QuestionnaireItem",
    "QuestionnaireOption",
    "RegulatorySnapshot",
    "SourceTrace",
    "TextOrigin",
]
