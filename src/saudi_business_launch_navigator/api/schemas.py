"""Strict public HTTP contracts for the internal/development API."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool

from saudi_business_launch_navigator.api.catalog_boundary import VerifiedCatalogBoundary
from saudi_business_launch_navigator.checklist.models import (
    ActivitySummary,
    BusinessChecklistResult,
    BusinessProfile,
    NavigationProfile,
    OwnershipInvestorRoute,
    PlannedLegalForm,
    QuestionnaireDefinition,
)
from saudi_business_launch_navigator.core.config import CatalogDataMode
from saudi_business_launch_navigator.interpretation.models import (
    AIErrorInfo,
    ChecklistExplanation,
    ClarificationPrompt,
    CoverageLimitation,
    InteractionLanguage,
    SupportedActivity,
    ValidatedInterpretation,
)


class APIModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class CatalogBoundary(APIModel):
    catalog_mode: Literal["GOVERNED_REAL_CATALOG", "PORTFOLIO_DEMO_CATALOG"]
    publication_state: Literal["UNPUBLISHED", "SAMPLE_ONLY"]
    data_classification: Literal[
        "PRIVATE_GOVERNED_UNPUBLISHED",
        "SYNTHETIC_PORTFOLIO_DEMO",
    ]
    public_catalog_approved: Literal[False] = False
    warning_ar: str
    warning_en: str

    @classmethod
    def from_verified(cls, boundary: VerifiedCatalogBoundary) -> CatalogBoundary:
        if boundary.mode is CatalogDataMode.PORTFOLIO_DEMO_CATALOG:
            return cls(
                catalog_mode="PORTFOLIO_DEMO_CATALOG",
                publication_state="SAMPLE_ONLY",
                data_classification="SYNTHETIC_PORTFOLIO_DEMO",
                warning_ar=(
                    "نسخة تجريبية لأغراض العرض التقني. تستخدم هذه النسخة بيانات نموذجية "
                    "ولا ينبغي الاعتماد عليها لاتخاذ قرار تنظيمي فعلي."
                ),
                warning_en=(
                    "Portfolio demonstration. This version uses sample data and should not "
                    "be relied on for real regulatory decisions."
                ),
            )
        return cls(
            catalog_mode="GOVERNED_REAL_CATALOG",
            publication_state="UNPUBLISHED",
            data_classification="PRIVATE_GOVERNED_UNPUBLISHED",
            warning_ar=(
                "واجهة تطوير داخلية لبيانات محكومة غير منشورة، وليست كتالوجاً تنظيمياً عاماً."
            ),
            warning_en=(
                "Internal development API over governed unpublished data; not a public "
                "regulatory catalog."
            ),
        )


class ActivitiesResponse(APIModel):
    metadata: CatalogBoundary
    activities: tuple[ActivitySummary, ...]


class QuestionnaireRequest(APIModel):
    activity_code: SupportedActivity


class QuestionnaireResponse(APIModel):
    metadata: CatalogBoundary
    questionnaire: QuestionnaireDefinition


class GovernedFactsInput(APIModel):
    has_food_establishment_workers: StrictBool | None = None
    zatca_confirmed_mandatory_vat_registration_applies: StrictBool | None = None
    has_employees: StrictBool | None = None
    gosi_coverage_conditions_met: StrictBool | None = None
    offers_home_delivery: StrictBool | None = None
    uses_public_sidewalk_for_customer_service: StrictBool | None = None

    def supplied_facts(self) -> dict[str, bool | None]:
        return {name: getattr(self, name) for name in self.model_fields_set}


class NavigationFactsInput(APIModel):
    """Explicit guided answers that are never passed to the requirement evaluator."""

    ownership_investor_route: OwnershipInvestorRoute | None = None
    planned_legal_form: PlannedLegalForm | None = None
    has_selected_business_premises: StrictBool | None = None

    def to_profile(self) -> NavigationProfile:
        return NavigationProfile(
            ownership_investor_route=self.ownership_investor_route,
            planned_legal_form=self.planned_legal_form,
            has_selected_business_premises=self.has_selected_business_premises,
        )


class ChecklistRequest(APIModel):
    activity_code: SupportedActivity
    facts: GovernedFactsInput = Field(default_factory=GovernedFactsInput)
    navigation_facts: NavigationFactsInput = Field(default_factory=NavigationFactsInput)

    def to_profile(self) -> BusinessProfile:
        return BusinessProfile(
            activity_code=self.activity_code.value,
            facts=self.facts.supplied_facts(),
        )


class ChecklistResponse(APIModel):
    metadata: CatalogBoundary
    result: BusinessChecklistResult


class AIInterpretRequest(APIModel):
    text: Annotated[str, Field(min_length=1, max_length=8000)]
    language: InteractionLanguage | None = None


class AIInterpretResponse(APIModel):
    interpretation: ValidatedInterpretation


class ExistingProfileInput(APIModel):
    activity_code: SupportedActivity
    facts: GovernedFactsInput = Field(default_factory=GovernedFactsInput)

    def to_profile(self) -> BusinessProfile:
        return BusinessProfile(
            activity_code=self.activity_code.value,
            facts=self.facts.supplied_facts(),
        )


class NavigatorRequest(APIModel):
    text: Annotated[str, Field(min_length=1, max_length=8000)]
    language: InteractionLanguage | None = None
    existing_profile: ExistingProfileInput | None = None


class NavigatorResponse(APIModel):
    metadata: CatalogBoundary
    interpretation: ValidatedInterpretation
    authoritative_result: BusinessChecklistResult | None
    explanation: ChecklistExplanation | None
    clarifications: tuple[ClarificationPrompt, ...]
    coverage_limitation: CoverageLimitation | None
    ai_error: AIErrorInfo | None


class ErrorDetail(APIModel):
    field: str
    error_type: str


class APIError(APIModel):
    code: str
    message: str
    details: tuple[ErrorDetail, ...] = ()
    request_id: str | None = None


class APIErrorResponse(APIModel):
    error: APIError


__all__ = [
    "AIInterpretRequest",
    "AIInterpretResponse",
    "APIError",
    "APIErrorResponse",
    "ActivitiesResponse",
    "CatalogBoundary",
    "ChecklistRequest",
    "ChecklistResponse",
    "ErrorDetail",
    "ExistingProfileInput",
    "GovernedFactsInput",
    "NavigationFactsInput",
    "NavigatorRequest",
    "NavigatorResponse",
    "QuestionnaireRequest",
    "QuestionnaireResponse",
]
