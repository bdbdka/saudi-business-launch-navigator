"""Validated synthetic catalog specification and deterministic read-model expansion."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Literal, Self
from urllib.parse import urlsplit
from uuid import UUID, uuid5

from pydantic import BaseModel, ConfigDict, Field, model_validator

from saudi_business_launch_navigator.checklist.models import CatalogMode
from saudi_business_launch_navigator.checklist.repository import (
    CatalogActionabilityVersion,
    CatalogActivity,
    CatalogAuthority,
    CatalogCondition,
    CatalogFact,
    CatalogGovernedSource,
    CatalogJourneyDestination,
    CatalogJourneyEvidence,
    CatalogJourneyTopicVersion,
    CatalogRequirementFamily,
    CatalogRequirementVersion,
    CatalogSource,
    GovernedCatalog,
)
from saudi_business_launch_navigator.core.canonical_hash import compute_canonical_sha256
from saudi_business_launch_navigator.rules.conditions import condition_sha256, parse_condition

DEMO_NAMESPACE = UUID("d9a3ad65-ce9d-53db-b4c4-235f01abe001")
DEMO_MIGRATION_REVISION = "0005_coverage_actionability"
DEMO_LAST_REVIEWED_AT = datetime(2026, 8, 27, tzinfo=UTC)
DEMO_NEXT_REVIEW_AT = datetime(2099, 1, 1, tzinfo=UTC)
_EXPECTED_ACTIVITIES = ("coffee_shop", "restaurant", "cloud_kitchen")
_EXPECTED_FACTS = {
    "ownership_investor_route": (
        "enum",
        (
            "saudi_person_or_saudi_owned_entity",
            "gcc_person_or_wholly_gcc_owned_entity",
            "foreign_legal_entity_or_mixed_foreign_ownership",
            "premium_residency_individual",
            "other",
        ),
        "NAVIGATION",
    ),
    "planned_legal_form": (
        "enum",
        ("individual_establishment", "limited_liability_company", "other"),
        "NAVIGATION",
    ),
    "has_selected_business_premises": ("boolean", None, "NAVIGATION"),
    "has_employees": ("boolean", None, "APPLICABILITY"),
    "has_food_establishment_workers": ("boolean", None, "APPLICABILITY"),
    "offers_home_delivery": ("boolean", None, "APPLICABILITY"),
    "zatca_confirmed_mandatory_vat_registration_applies": (
        "boolean",
        None,
        "APPLICABILITY",
    ),
    "uses_public_sidewalk_for_customer_service": ("boolean", None, "APPLICABILITY"),
}
_EXPECTED_REQUIREMENTS = {
    "demo_launch_orientation": ((_EXPECTED_ACTIVITIES), None),
    "demo_worker_readiness": (_EXPECTED_ACTIVITIES, "has_food_establishment_workers"),
    "demo_vat_confirmation": (
        _EXPECTED_ACTIVITIES,
        "zatca_confirmed_mandatory_vat_registration_applies",
    ),
    "demo_employment_setup": (_EXPECTED_ACTIVITIES, "has_employees"),
    "demo_delivery_setup": (_EXPECTED_ACTIVITIES, "offers_home_delivery"),
    "demo_sidewalk_setup": (("restaurant",), "uses_public_sidewalk_for_customer_service"),
}
_EXPECTED_ACTIONABILITY = {
    "demo_start_here": ("official_start", "official_destination"),
    "demo_sample_document": ("document", "text"),
    "demo_sample_sequence": ("sequence", "text"),
}
_EXPECTED_JOURNEY_TOPICS = {
    "ownership_investment_route": "ownership_investor_route",
    "business_registration_route": "planned_legal_form",
    "site_activity_verification": "has_selected_business_premises",
    "vat_registration_navigation": None,
    "e_invoicing_confirmation": None,
    "zakat_registration_confirmation": None,
}


class DemoModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class DemoActivity(DemoModel):
    code: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    name_ar: str = Field(min_length=1)
    name_en: str = Field(min_length=1)


class DemoAuthority(DemoModel):
    code: str = Field(pattern=r"^demo_[a-z0-9_]+$")
    name_ar: str = Field(min_length=1)
    name_en: str = Field(min_length=1)


class DemoSource(DemoModel):
    code: str = Field(pattern=r"^demo_[a-z0-9_]+$")
    title_ar: str = Field(min_length=1)
    title_en: str = Field(min_length=1)
    url: str


class DemoFact(DemoModel):
    code: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    data_type: Literal["boolean", "enum"]
    allowed_values: tuple[str, ...] | None
    purpose: Literal["NAVIGATION", "APPLICABILITY"]

    @model_validator(mode="after")
    def validate_values(self) -> Self:
        if self.data_type == "enum" and not self.allowed_values:
            raise ValueError("demo enum fact needs values")
        if self.data_type == "boolean" and self.allowed_values is not None:
            raise ValueError("demo boolean fact cannot define values")
        return self


class DemoRequirement(DemoModel):
    code: str = Field(pattern=r"^demo_[a-z0-9_]+$")
    title_ar: str = Field(min_length=1)
    description_ar: str = Field(min_length=1)
    title_en: str = Field(min_length=1)
    description_en: str = Field(min_length=1)
    activities: tuple[str, ...]
    condition_fact: str | None


class DemoJourneyTopic(DemoModel):
    code: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    navigation_fact: str | None


class DemoActionability(DemoModel):
    code: str = Field(pattern=r"^demo_[a-z0-9_]+$")
    detail_type: Literal["official_start", "document", "sequence"]
    value: dict[str, object]


class PortfolioDemoSpec(DemoModel):
    schema_version: Literal[1]
    dataset_code: Literal["portfolio_demo_v1"]
    dataset_revision: Literal[1]
    database_identity: UUID
    classification: Literal["PORTFOLIO_DEMO_CATALOG"]
    warning_ar: str = Field(min_length=1)
    warning_en: str = Field(min_length=1)
    activities: tuple[DemoActivity, ...]
    authority: DemoAuthority
    source: DemoSource
    facts: tuple[DemoFact, ...]
    requirements: tuple[DemoRequirement, ...]
    journey_topics: tuple[DemoJourneyTopic, ...]
    actionability: tuple[DemoActionability, ...]

    @model_validator(mode="after")
    def validate_demo_boundary(self) -> Self:
        expected_identity = demo_uuid("database/portfolio-demo-v1")
        if self.database_identity != expected_identity:
            raise ValueError("demo database identity is not namespace-derived")
        activity_codes = tuple(activity.code for activity in self.activities)
        if activity_codes != _EXPECTED_ACTIVITIES:
            raise ValueError("demo activities differ from the supported three-activity order")
        fact_by_code = {fact.code: fact for fact in self.facts}
        if len(fact_by_code) != len(self.facts):
            raise ValueError("duplicate demo fact code")
        actual_facts = {
            code: (fact.data_type, fact.allowed_values, fact.purpose)
            for code, fact in fact_by_code.items()
        }
        if actual_facts != _EXPECTED_FACTS:
            raise ValueError("demo fact inventory differs from the reviewed contract")
        requirement_by_code = {requirement.code: requirement for requirement in self.requirements}
        if len(requirement_by_code) != len(self.requirements):
            raise ValueError("duplicate demo requirement code")
        if not requirement_by_code:
            raise ValueError("demo needs at least one requirement")
        actual_requirements = {
            code: (requirement.activities, requirement.condition_fact)
            for code, requirement in requirement_by_code.items()
        }
        if actual_requirements != _EXPECTED_REQUIREMENTS:
            raise ValueError("demo requirement inventory differs from the reviewed contract")
        for requirement in self.requirements:
            if not requirement.activities or not set(requirement.activities) <= set(activity_codes):
                raise ValueError(f"invalid demo activity mapping: {requirement.code}")
            if requirement.condition_fact is not None:
                fact = fact_by_code.get(requirement.condition_fact)
                if fact is None or fact.purpose != "APPLICABILITY" or fact.data_type != "boolean":
                    raise ValueError(f"invalid demo condition fact: {requirement.code}")
        journey_mapping = {topic.code: topic.navigation_fact for topic in self.journey_topics}
        if journey_mapping != _EXPECTED_JOURNEY_TOPICS:
            raise ValueError("demo journey topics differ from the runtime contract")
        for fact_code in journey_mapping.values():
            if fact_code is not None and fact_by_code[fact_code].purpose != "NAVIGATION":
                raise ValueError(f"journey fact is not navigation-only: {fact_code}")
        parsed_source = urlsplit(self.source.url)
        if (
            parsed_source.scheme != "https"
            or parsed_source.hostname != "example.invalid"
            or parsed_source.username is not None
            or parsed_source.password is not None
            or parsed_source.port is not None
            or parsed_source.path != "/portfolio-demo"
            or parsed_source.query
            or parsed_source.fragment
        ):
            raise ValueError("demo source must be the exact reserved HTTPS sample URL")
        if (
            self.source.code != "demo_sample_source"
            or self.authority.code != "demo_non_government_authority"
        ):
            raise ValueError("demo source chain is not visibly synthetic")
        actionability = {
            item.code: (item.detail_type, item.value.get("kind")) for item in self.actionability
        }
        if actionability != _EXPECTED_ACTIONABILITY:
            raise ValueError("demo actionability inventory differs from the reviewed contract")
        dumped = json.dumps(self.model_dump(mode="json"), ensure_ascii=False).lower()
        if "gov.sa" in dumped:
            raise ValueError("demo specification must not reference Saudi government domains")
        question_counts = {
            activity: 3
            + len(
                {
                    requirement.condition_fact
                    for requirement in self.requirements
                    if activity in requirement.activities and requirement.condition_fact is not None
                }
            )
            for activity in activity_codes
        }
        if question_counts != {"coffee_shop": 7, "restaurant": 8, "cloud_kitchen": 7}:
            raise ValueError("demo questionnaire breadth must remain exactly 7/8/7")
        return self


def demo_uuid(path: str) -> UUID:
    """Return a stable public UUIDv5 that cannot collide with private random IDs."""

    return uuid5(DEMO_NAMESPACE, path)


def portfolio_demo_spec_path() -> Path:
    """Locate the checked-in safe seed in source and container layouts."""

    candidates = (
        Path(__file__).resolve().parents[3] / "public_demo/PORTFOLIO_DEMO_CATALOG.json",
        Path("/app/public_demo/PORTFOLIO_DEMO_CATALOG.json"),
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise RuntimeError("portfolio demo catalog specification is unavailable")


@lru_cache(maxsize=1)
def load_portfolio_demo_spec() -> PortfolioDemoSpec:
    """Parse the strict, sample-only catalog specification."""

    return PortfolioDemoSpec.model_validate_json(portfolio_demo_spec_path().read_bytes())


def graph_sha256(spec: PortfolioDemoSpec) -> str:
    return compute_canonical_sha256(spec.model_dump(mode="json"))


def dataset_fingerprint(spec: PortfolioDemoSpec) -> str:
    return compute_canonical_sha256(
        {
            "classification": spec.classification,
            "database_identity": str(spec.database_identity),
            "dataset_code": spec.dataset_code,
            "dataset_revision": spec.dataset_revision,
            "expanded_catalog_sha256": expanded_catalog_fingerprint(spec),
            "graph_sha256": graph_sha256(spec),
            "schema_version": spec.schema_version,
        }
    )


def expanded_catalog_fingerprint(spec: PortfolioDemoSpec) -> str:
    """Bind identity to every hard-coded field in the expanded API read model."""

    catalogs: list[object] = []
    for activity_code in _EXPECTED_ACTIVITIES:
        catalog = build_demo_catalog(
            spec,
            activity_code=activity_code,
            database_timestamp=DEMO_LAST_REVIEWED_AT,
            migration_revision=DEMO_MIGRATION_REVISION,
        )
        projection = asdict(catalog)
        projection.pop("database_timestamp")
        catalogs.append(_jsonable(projection))
    return compute_canonical_sha256(catalogs)


def _jsonable(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _jsonable(asdict(value))
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_jsonable(item) for item in value]
    return value


def build_demo_catalog(
    spec: PortfolioDemoSpec,
    *,
    activity_code: str,
    database_timestamp: datetime,
    migration_revision: str,
) -> GovernedCatalog:
    """Expand the compact seed into the authoritative checklist read model."""

    activity_spec = next(
        (activity for activity in spec.activities if activity.code == activity_code),
        None,
    )
    if activity_spec is None:
        from saudi_business_launch_navigator.checklist.exceptions import UnsupportedActivityError

        raise UnsupportedActivityError(f"unsupported activity: {activity_code}")

    authority = CatalogAuthority(
        id=demo_uuid("authority/demo"),
        code=spec.authority.code,
        name_ar=spec.authority.name_ar,
        name_en=spec.authority.name_en,
        verification_status="approved",
        last_verified_at=DEMO_LAST_REVIEWED_AT,
        next_review_at=DEMO_NEXT_REVIEW_AT,
    )
    source_id = demo_uuid("source/demo")
    source_version_id = demo_uuid("source/demo/version/1")
    domain_id = demo_uuid("domain/example.invalid")
    governed_source = CatalogGovernedSource(
        source_id=source_id,
        source_code=spec.source.code,
        official_title_ar=spec.source.title_ar,
        official_title_en=spec.source.title_en,
        canonical_url=spec.source.url,
        canonical_host="example.invalid",
        source_verification_status="approved",
        source_next_review_at=DEMO_NEXT_REVIEW_AT,
        source_domain_id=domain_id,
        source_entity_id=authority.id,
        source_version_id=source_version_id,
        source_version_number=1,
        reviewed_url=spec.source.url,
        resolved_url=spec.source.url,
        source_version_review_status="approved",
        source_version_is_current=True,
        source_version_last_verified_at=DEMO_LAST_REVIEWED_AT,
        source_version_next_review_at=DEMO_NEXT_REVIEW_AT,
        domain_id_at_review=domain_id,
        responsible_entity_id_at_review=authority.id,
        platform_id_at_review=None,
        domain_name="example.invalid",
        domain_verification_status="approved",
        domain_next_review_at=DEMO_NEXT_REVIEW_AT,
        authority=authority,
        platform=None,
    )

    facts = tuple(_catalog_fact(fact) for fact in spec.facts)
    fact_by_code = {fact.code: fact for fact in facts}
    families: list[CatalogRequirementFamily] = []
    requirement_version_by_code: dict[str, UUID] = {}
    for requirement in spec.requirements:
        requirement_id = demo_uuid(f"requirement/{requirement.code}")
        version_id = demo_uuid(f"requirement/{requirement.code}/version/1")
        requirement_version_by_code[requirement.code] = version_id
        condition: tuple[CatalogCondition, ...] = ()
        if requirement.condition_fact is not None:
            expression_value: dict[str, object] = {
                "op": "eq",
                "fact": requirement.condition_fact,
                "value": True,
            }
            expression = parse_condition(expression_value)
            condition = (
                CatalogCondition(
                    id=demo_uuid(f"condition/{requirement.code}"),
                    expression=expression_value,
                    expression_sha256=condition_sha256(expression),
                    dsl_schema_version=1,
                    verification_status="approved",
                    fact_definition_ids=(fact_by_code[requirement.condition_fact].id,),
                ),
            )
        source = CatalogSource(
            requirement_source_id=demo_uuid(f"requirement-source/{requirement.code}"),
            source_id=source_id,
            source_code=spec.source.code,
            official_title_ar=spec.source.title_ar,
            official_title_en=spec.source.title_en,
            source_role="primary",
            relationship_status="active",
            canonical_url=spec.source.url,
            canonical_host="example.invalid",
            source_verification_status="approved",
            source_last_verified_at=DEMO_LAST_REVIEWED_AT,
            source_next_review_at=DEMO_NEXT_REVIEW_AT,
            source_version_id=source_version_id,
            source_version_number=1,
            reviewed_url=spec.source.url,
            resolved_url=spec.source.url,
            source_version_review_status="approved",
            source_version_is_current=True,
            source_version_last_verified_at=DEMO_LAST_REVIEWED_AT,
            source_version_next_review_at=DEMO_NEXT_REVIEW_AT,
            excerpt_locator="synthetic_demo_locator",
        )
        families.append(
            CatalogRequirementFamily(
                id=requirement_id,
                code=requirement.code,
                versions=(
                    CatalogRequirementVersion(
                        id=version_id,
                        version_number=1,
                        canonical_title_ar=requirement.title_ar,
                        canonical_description_ar=requirement.description_ar,
                        canonical_title_en=requirement.title_en,
                        canonical_description_en=requirement.description_en,
                        verification_status="approved",
                        is_current=True,
                        authority=authority,
                        activity_codes=requirement.activities,
                        conditions=condition,
                        sources=(source,),
                    ),
                ),
            )
        )

    journey_topics = tuple(
        _journey_topic(
            spec=spec,
            activity_code=activity_code,
            topic=topic,
            fact_by_code=fact_by_code,
            source=governed_source,
        )
        for topic in spec.journey_topics
    )
    target_version_id = requirement_version_by_code["demo_launch_orientation"]
    actionability = tuple(
        CatalogActionabilityVersion(
            id=demo_uuid(f"actionability/{item.code}/version/1"),
            code=item.code,
            version_number=1,
            requirement_version_id=target_version_id,
            detail_type=item.detail_type,
            value_state="VERIFIED",
            value_payload=item.value,
            value_sha256=compute_canonical_sha256(item.value),
            source=governed_source,
            verification_status="approved",
            is_current=True,
            last_verified_at=DEMO_LAST_REVIEWED_AT,
            next_review_at=DEMO_NEXT_REVIEW_AT,
            display_order=spec.actionability.index(item) + 1,
        )
        for item in spec.actionability
    )
    return GovernedCatalog(
        activity=CatalogActivity(
            id=demo_uuid(f"activity/{activity_spec.code}"),
            code=activity_spec.code,
            name_ar=activity_spec.name_ar,
            name_en=activity_spec.name_en,
            is_active=True,
        ),
        requirement_families=tuple(families),
        facts=facts,
        migration_revision=migration_revision,
        publication_count=0,
        database_timestamp=database_timestamp,
        catalog_mode=CatalogMode.PORTFOLIO_DEMO,
        journey_topics=journey_topics,
        actionability_versions=actionability,
        journey_release_count=0,
        actionability_release_count=0,
    )


def _catalog_fact(fact: DemoFact) -> CatalogFact:
    return CatalogFact(
        id=demo_uuid(f"fact/{fact.code}/version/1"),
        code=fact.code,
        version_number=1,
        data_type=fact.data_type,
        allowed_values=fact.allowed_values,
        unit=None,
        privacy_class="non_personal_business",
        verification_status="approved",
        is_current=True,
    )


def _journey_topic(
    *,
    spec: PortfolioDemoSpec,
    activity_code: str,
    topic: DemoJourneyTopic,
    fact_by_code: dict[str, CatalogFact],
    source: CatalogGovernedSource,
) -> CatalogJourneyTopicVersion:
    version_id = demo_uuid(f"journey/{topic.code}/{activity_code}/version/1")
    evidence = CatalogJourneyEvidence(
        id=demo_uuid(f"journey-evidence/{topic.code}/{activity_code}"),
        source=source,
        evidence_role="primary",
        excerpt_locator="synthetic_demo_locator",
    )
    facts = (fact_by_code[topic.navigation_fact],) if topic.navigation_fact is not None else ()
    destinations: list[CatalogJourneyDestination] = []
    if facts:
        fact = facts[0]
        route_values: tuple[object, ...] = (
            fact.allowed_values if fact.data_type == "enum" else (True, False)
        ) or ()
        for index, route_value in enumerate(route_values, start=1):
            destinations.append(
                _journey_destination(
                    topic=topic,
                    activity_code=activity_code,
                    evidence=evidence,
                    display_order=index,
                    fact=fact,
                    route_value=route_value,
                )
            )
    else:
        destinations.append(
            _journey_destination(
                topic=topic,
                activity_code=activity_code,
                evidence=evidence,
                display_order=1,
                fact=None,
                route_value=None,
            )
        )
    return CatalogJourneyTopicVersion(
        id=version_id,
        topic_code=topic.code,
        activity_code=activity_code,
        title_ar=f"مسار تجريبي: {topic.code}",
        title_en=f"Demo route: {topic.code}",
        coverage_state="REQUIRES_OFFICIAL_CONFIRMATION",
        verified_summary_ar=None,
        verified_summary_en=None,
        limitation_summary_ar="هذا مسار نموذجي غير حكومي لأغراض العرض التقني فقط.",
        limitation_summary_en=(
            "This is a non-government sample route for technical demonstration only."
        ),
        what_to_verify_ar="استخدم الرابط النموذجي لفهم طريقة التنقل فقط، وليس لاتخاذ قرار تنظيمي.",
        what_to_verify_en=(
            "Use the sample link only to understand navigation, not for a regulatory decision."
        ),
        verification_status="approved",
        is_current=True,
        last_verified_at=DEMO_LAST_REVIEWED_AT,
        next_review_at=DEMO_NEXT_REVIEW_AT,
        evidence=(evidence,),
        facts=facts,
        destinations=tuple(destinations),
    )


def _journey_destination(
    *,
    topic: DemoJourneyTopic,
    activity_code: str,
    evidence: CatalogJourneyEvidence,
    display_order: int,
    fact: CatalogFact | None,
    route_value: object | None,
) -> CatalogJourneyDestination:
    return CatalogJourneyDestination(
        code=f"demo_{topic.code}_{display_order}",
        destination_kind="page",
        guidance_ar="افتح الوجهة التجريبية لمعاينة آلية الربط بالمصدر.",
        guidance_en="Open the demo destination to inspect the source-linking mechanism.",
        what_to_verify_ar="لا تعتبر هذه الوجهة مصدراً حكومياً أو دليلاً تنظيمياً.",
        what_to_verify_en="Do not treat this destination as a government or regulatory source.",
        route_fact_definition_id=fact.id if fact is not None else None,
        route_match_kind="equals" if fact is not None else "always",
        route_match_value=route_value,
        display_order=display_order,
        is_primary=True,
        evidence=evidence,
    )


__all__ = [
    "DEMO_MIGRATION_REVISION",
    "PortfolioDemoSpec",
    "build_demo_catalog",
    "dataset_fingerprint",
    "demo_uuid",
    "expanded_catalog_fingerprint",
    "graph_sha256",
    "load_portfolio_demo_spec",
]
