"""Deterministic questionnaire and personalized-checklist services."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass
from urllib.parse import urlsplit

from pydantic import TypeAdapter, ValidationError

from saudi_business_launch_navigator.checklist.exceptions import (
    BusinessProfileError,
    RegulatoryCatalogError,
)
from saudi_business_launch_navigator.checklist.models import (
    ActionabilityItem,
    ActionabilityValue,
    ActivitySummary,
    ApplicabilityReasonCode,
    ApplicabilityStatus,
    AuthorityTrace,
    BusinessChecklistResult,
    BusinessProfile,
    ChecklistItem,
    CoverageNotice,
    EvaluatedFactTrace,
    GovernedSourceTrace,
    JourneyDestination,
    JourneyGuidance,
    JourneyRoutingStatus,
    MissingNavigationInformation,
    NavigationProfile,
    PlatformTrace,
    QuestionnaireAnswerLabels,
    QuestionnaireDefinition,
    QuestionnaireItem,
    QuestionnaireOption,
    QuestionPurpose,
    RegulatorySnapshot,
    SourceTrace,
)
from saudi_business_launch_navigator.checklist.questionnaire import QUESTION_TEXT
from saudi_business_launch_navigator.checklist.repository import (
    CatalogActionabilityVersion,
    CatalogCondition,
    CatalogFact,
    CatalogGovernedSource,
    CatalogJourneyTopicVersion,
    CatalogRequirementFamily,
    CatalogRequirementVersion,
    GovernedCatalog,
    GovernedCatalogRepository,
)
from saudi_business_launch_navigator.core.canonical_hash import compute_canonical_sha256
from saudi_business_launch_navigator.rules.conditions import (
    AllCondition,
    AnyCondition,
    ConditionDefinitionError,
    ConditionExpression,
    EqualityPredicate,
    FactDataType,
    FactDefinition,
    FactValueError,
    NotCondition,
    TruthValue,
    condition_sha256,
    evaluate_condition,
    parse_condition,
    referenced_fact_codes,
    validate_condition_definition,
)

_EXPECTED_MIGRATION = "0005_coverage_actionability"
_APPROVED = "approved"
_ACTIVE = "active"
_HISTORICAL = "historical"
_NON_PERSONAL_BUSINESS = "non_personal_business"
_VERIFIED = "VERIFIED"
_EXPECTED_JOURNEY_TOPICS = frozenset(
    {
        "ownership_investment_route",
        "business_registration_route",
        "site_activity_verification",
        "vat_registration_navigation",
        "e_invoicing_confirmation",
        "zakat_registration_confirmation",
    }
)
_NAVIGATION_FACT_ORDER = (
    "ownership_investor_route",
    "planned_legal_form",
    "has_selected_business_premises",
)
_QUESTION_ORDER = {
    "ownership_investor_route": 1,
    "planned_legal_form": 2,
    "has_selected_business_premises": 3,
    "has_employees": 4,
    "has_food_establishment_workers": 5,
    "offers_home_delivery": 6,
    "uses_public_sidewalk_for_customer_service": 7,
    "zatca_confirmed_mandatory_vat_registration_applies": 8,
}
_ACTIONABILITY_LABELS = {
    "official_start": ("ابدأ من هنا", "Start here"),
    "prerequisite": ("قبل البدء", "Before you start"),
    "document": ("المستندات المطلوبة", "Required documents"),
    "fee": ("الرسوم", "Fees"),
    "sequence": ("الخطوات", "Steps"),
}
_ACTIONABILITY_VALUE_ADAPTER: TypeAdapter[ActionabilityValue] = TypeAdapter(ActionabilityValue)


@dataclass(frozen=True)
class _ResolvedRequirement:
    family: CatalogRequirementFamily
    version: CatalogRequirementVersion
    selected_activity_code: str
    condition: CatalogCondition | None
    definitions: dict[str, FactDefinition]
    facts: dict[str, CatalogFact]


@dataclass(frozen=True)
class _ResolvedCatalog:
    catalog: GovernedCatalog
    requirements: tuple[_ResolvedRequirement, ...]
    current_facts: dict[str, CatalogFact]
    journey_topics: tuple[CatalogJourneyTopicVersion, ...]
    navigation_facts: dict[str, CatalogFact]
    actionability_by_requirement_version: dict[object, tuple[ActionabilityItem, ...]]


class ChecklistService:
    """Application layer around governed data and the condition evaluator."""

    def __init__(
        self,
        repository: GovernedCatalogRepository,
        coverage_notice: CoverageNotice,
    ) -> None:
        self._repository = repository
        self._coverage_notice = coverage_notice

    async def build_questionnaire(self, activity_code: str) -> QuestionnaireDefinition:
        """Return governed applicability inputs plus navigation-only inputs."""

        resolved = self._resolve_catalog(await self._repository.load(activity_code))
        applicability_facts = {
            code: fact
            for requirement in resolved.requirements
            for code, fact in requirement.facts.items()
        }
        questions = [
            self._question_for(fact, purpose=QuestionPurpose.NAVIGATION)
            for fact in resolved.navigation_facts.values()
        ]
        questions.extend(
            self._question_for(fact, purpose=QuestionPurpose.APPLICABILITY)
            for fact in applicability_facts.values()
        )
        return QuestionnaireDefinition(
            activity=self._activity_summary(resolved.catalog),
            questions=tuple(
                sorted(
                    questions,
                    key=lambda item: (_QUESTION_ORDER.get(item.fact_code, 100), item.fact_code),
                )
            ),
        )

    async def evaluate_business_profile(
        self,
        profile: BusinessProfile,
        navigation_profile: NavigationProfile | None = None,
    ) -> BusinessChecklistResult:
        """Evaluate one in-memory profile with no persistence, inference, or LLM."""

        resolved = self._resolve_catalog(await self._repository.load(profile.activity_code))
        navigation_profile = navigation_profile or NavigationProfile()
        regulatory_fact_codes = set(resolved.current_facts) - set(resolved.navigation_facts)
        unknown_codes = sorted(set(profile.facts) - regulatory_fact_codes)
        if unknown_codes:
            raise BusinessProfileError(f"unknown governed fact code: {unknown_codes[0]}")

        buckets: dict[ApplicabilityStatus, list[ChecklistItem]] = {
            ApplicabilityStatus.APPLIES: [],
            ApplicabilityStatus.DOES_NOT_APPLY: [],
            ApplicabilityStatus.NEEDS_INFORMATION: [],
        }
        questions_needed: dict[str, QuestionnaireItem] = {}

        for requirement in resolved.requirements:
            item = self._evaluate_requirement(
                requirement,
                profile,
                resolved.actionability_by_requirement_version.get(requirement.version.id, ()),
            )
            buckets[item.applicability_status].append(item)
            for code in item.missing_fact_codes:
                questions_needed[code] = self._question_for(requirement.facts[code])

        all_items = [item for items in buckets.values() for item in items]
        snapshot = self._build_snapshot(resolved, all_items)
        journey_guidance, missing_navigation = self._resolve_journey(
            resolved,
            navigation_profile,
        )
        return BusinessChecklistResult(
            activity=self._activity_summary(resolved.catalog),
            applies=tuple(sorted(buckets[ApplicabilityStatus.APPLIES], key=_item_sort_key)),
            does_not_apply=tuple(
                sorted(buckets[ApplicabilityStatus.DOES_NOT_APPLY], key=_item_sort_key)
            ),
            needs_information=tuple(
                sorted(buckets[ApplicabilityStatus.NEEDS_INFORMATION], key=_item_sort_key)
            ),
            questions_needed=tuple(questions_needed[code] for code in sorted(questions_needed)),
            journey_guidance=journey_guidance,
            missing_navigation_information=missing_navigation,
            coverage_notice=self._coverage_notice,
            regulatory_snapshot=snapshot,
        )

    def _resolve_catalog(self, catalog: GovernedCatalog) -> _ResolvedCatalog:
        if catalog.migration_revision != _EXPECTED_MIGRATION:
            raise RegulatoryCatalogError(
                f"unsupported regulatory migration: {catalog.migration_revision}"
            )
        if not catalog.activity.is_active:
            raise RegulatoryCatalogError("selected activity is inactive")

        facts_by_code: dict[str, list[CatalogFact]] = {}
        facts_by_id: dict[object, CatalogFact] = {}
        for fact in catalog.facts:
            facts_by_code.setdefault(fact.code, []).append(fact)
            facts_by_id[fact.id] = fact

        current_facts: dict[str, CatalogFact] = {}
        for code, versions in facts_by_code.items():
            current = [fact for fact in versions if fact.is_current]
            if len(current) > 1:
                raise RegulatoryCatalogError(f"multiple current fact definitions: {code}")
            if current:
                current_facts[code] = current[0]

        resolved_requirements: list[_ResolvedRequirement] = []
        for family in catalog.requirement_families:
            current_versions = [version for version in family.versions if version.is_current]
            if len(current_versions) != 1:
                raise RegulatoryCatalogError(
                    f"requirement {family.code} has {len(current_versions)} current versions"
                )
            version = current_versions[0]
            if catalog.activity.code not in version.activity_codes:
                continue
            if version.verification_status != _APPROVED:
                raise RegulatoryCatalogError(f"current requirement is not approved: {family.code}")
            self._validate_authority(version, catalog)
            self._validate_sources(family.code, version, catalog)

            if len(version.conditions) > 1:
                raise RegulatoryCatalogError(f"multiple condition sets: {family.code}")
            condition = version.conditions[0] if version.conditions else None
            definitions: dict[str, FactDefinition] = {}
            linked_facts: dict[str, CatalogFact] = {}
            if condition is not None:
                definitions, linked_facts = self._validate_condition(
                    family.code,
                    condition,
                    facts_by_id,
                )
            resolved_requirements.append(
                _ResolvedRequirement(
                    family=family,
                    version=version,
                    selected_activity_code=catalog.activity.code,
                    condition=condition,
                    definitions=definitions,
                    facts=linked_facts,
                )
            )

        journey_topics, navigation_facts = self._resolve_journey_catalog(
            catalog,
            current_facts,
            resolved_requirements,
        )
        actionability_by_requirement_version = self._resolve_actionability_catalog(
            catalog,
            resolved_requirements,
        )

        return _ResolvedCatalog(
            catalog=catalog,
            requirements=tuple(sorted(resolved_requirements, key=lambda item: item.family.code)),
            current_facts=current_facts,
            journey_topics=journey_topics,
            navigation_facts=navigation_facts,
            actionability_by_requirement_version=actionability_by_requirement_version,
        )

    def _validate_authority(
        self,
        version: CatalogRequirementVersion,
        catalog: GovernedCatalog,
    ) -> None:
        authority = version.authority
        if authority.verification_status != _APPROVED:
            raise RegulatoryCatalogError(f"authority is not approved: {authority.code}")
        if (
            authority.next_review_at is None
            or authority.next_review_at <= catalog.database_timestamp
        ):
            raise RegulatoryCatalogError(f"authority verification is stale: {authority.code}")

    def _validate_sources(
        self,
        requirement_code: str,
        version: CatalogRequirementVersion,
        catalog: GovernedCatalog,
    ) -> None:
        active = tuple(
            source for source in version.sources if source.relationship_status == _ACTIVE
        )
        primary = tuple(source for source in active if source.source_role == "primary")
        if len(primary) != 1:
            raise RegulatoryCatalogError(
                f"requirement {requirement_code} needs exactly one active primary source"
            )
        for source in active:
            if source.source_verification_status != _APPROVED:
                raise RegulatoryCatalogError(f"source is not approved: {source.source_code}")
            if source.source_version_review_status != _APPROVED:
                raise RegulatoryCatalogError(
                    f"source version is not approved: {source.source_version_id}"
                )
            if source.source_role != _HISTORICAL and not source.source_version_is_current:
                raise RegulatoryCatalogError(
                    f"active source version is not current: {source.source_version_id}"
                )
            freshness_dates = (
                source.source_next_review_at,
                source.source_version_next_review_at,
            )
            if source.source_role != _HISTORICAL and any(
                value is None or value <= catalog.database_timestamp for value in freshness_dates
            ):
                raise RegulatoryCatalogError(f"source verification is stale: {source.source_code}")

    def _validate_condition(
        self,
        requirement_code: str,
        condition: CatalogCondition,
        facts_by_id: dict[object, CatalogFact],
    ) -> tuple[dict[str, FactDefinition], dict[str, CatalogFact]]:
        if condition.dsl_schema_version != 1 or condition.verification_status != _APPROVED:
            raise RegulatoryCatalogError(f"condition is not approved: {requirement_code}")
        try:
            expression = parse_condition(condition.expression)
        except ValidationError as exc:
            raise RegulatoryCatalogError(f"malformed condition graph: {requirement_code}") from exc
        if condition_sha256(expression) != condition.expression_sha256:
            raise RegulatoryCatalogError(f"condition hash mismatch: {requirement_code}")

        linked: list[CatalogFact] = []
        for fact_id in condition.fact_definition_ids:
            fact = facts_by_id.get(fact_id)
            if fact is None:
                raise RegulatoryCatalogError(
                    f"condition references missing fact definition: {requirement_code}"
                )
            linked.append(fact)
        if any(not fact.is_current for fact in linked):
            raise RegulatoryCatalogError(
                f"condition references historical fact definition: {requirement_code}"
            )
        if any(fact.verification_status != _APPROVED for fact in linked):
            raise RegulatoryCatalogError(
                f"condition references unapproved fact definition: {requirement_code}"
            )
        if any(fact.privacy_class != _NON_PERSONAL_BUSINESS for fact in linked):
            raise RegulatoryCatalogError(
                f"condition references prohibited personal fact: {requirement_code}"
            )
        linked_by_code = {fact.code: fact for fact in linked}
        if len(linked_by_code) != len(linked):
            raise RegulatoryCatalogError(f"duplicate fact meaning in condition: {requirement_code}")
        if set(linked_by_code) != set(referenced_fact_codes(expression)):
            raise RegulatoryCatalogError(f"condition fact links differ: {requirement_code}")

        try:
            definitions = {
                fact.code: FactDefinition(
                    code=fact.code,
                    data_type=FactDataType(fact.data_type),
                    allowed_values=fact.allowed_values,
                    unit=fact.unit,
                )
                for fact in linked
            }
            validate_condition_definition(expression, definitions)
        except (ValueError, ConditionDefinitionError) as exc:
            raise RegulatoryCatalogError(
                f"invalid governed fact definition: {requirement_code}"
            ) from exc
        return definitions, linked_by_code

    def _resolve_journey_catalog(
        self,
        catalog: GovernedCatalog,
        current_facts: dict[str, CatalogFact],
        requirements: list[_ResolvedRequirement],
    ) -> tuple[tuple[CatalogJourneyTopicVersion, ...], dict[str, CatalogFact]]:
        if not catalog.journey_topics:
            return (), {}
        if catalog.journey_release_count != 0:
            raise RegulatoryCatalogError("internal journey catalog unexpectedly contains releases")

        current_by_code: dict[str, list[CatalogJourneyTopicVersion]] = defaultdict(list)
        for topic in catalog.journey_topics:
            if topic.is_current:
                current_by_code[topic.topic_code].append(topic)
        if set(current_by_code) != _EXPECTED_JOURNEY_TOPICS:
            raise RegulatoryCatalogError(
                "current journey-topic set differs from the verified navigation catalog"
            )
        if any(len(versions) != 1 for versions in current_by_code.values()):
            raise RegulatoryCatalogError("journey topic has multiple current activity versions")

        current_topics = tuple(current_by_code[code][0] for code in sorted(current_by_code))
        navigation_facts: dict[str, CatalogFact] = {}
        for topic in current_topics:
            if topic.activity_code != catalog.activity.code:
                raise RegulatoryCatalogError(
                    "journey topic activity differs from selected activity"
                )
            if topic.verification_status != _APPROVED:
                raise RegulatoryCatalogError(f"journey topic is not approved: {topic.topic_code}")
            if topic.coverage_state == "NOT_RESEARCHED":
                raise RegulatoryCatalogError(
                    f"not-researched journey topic cannot enter runtime: {topic.topic_code}"
                )
            if (
                topic.last_verified_at is None
                or topic.next_review_at is None
                or topic.next_review_at <= catalog.database_timestamp
            ):
                raise RegulatoryCatalogError(f"journey topic is stale: {topic.topic_code}")
            primary_evidence = [
                evidence for evidence in topic.evidence if evidence.evidence_role == "primary"
            ]
            if len(primary_evidence) != 1:
                raise RegulatoryCatalogError(
                    f"journey topic needs one primary evidence link: {topic.topic_code}"
                )
            for evidence in topic.evidence:
                self._validate_governed_source(evidence.source, catalog)
            linked_fact_ids = {fact.id for fact in topic.facts}
            for fact in topic.facts:
                if (
                    not fact.is_current
                    or fact.verification_status != _APPROVED
                    or fact.privacy_class != _NON_PERSONAL_BUSINESS
                    or current_facts.get(fact.code) != fact
                ):
                    raise RegulatoryCatalogError(
                        f"invalid navigation fact for topic {topic.topic_code}: {fact.code}"
                    )
                existing = navigation_facts.get(fact.code)
                if existing is not None and existing.id != fact.id:
                    raise RegulatoryCatalogError(f"conflicting navigation fact: {fact.code}")
                navigation_facts[fact.code] = fact
            for destination in topic.destinations:
                self._validate_governed_source(destination.evidence.source, catalog)
                if destination.evidence not in topic.evidence:
                    raise RegulatoryCatalogError(
                        f"destination evidence differs from topic graph: {destination.code}"
                    )
                if destination.route_match_kind == "always":
                    if (
                        destination.route_fact_definition_id is not None
                        or destination.route_match_value is not None
                    ):
                        raise RegulatoryCatalogError(
                            f"invalid always route shape: {destination.code}"
                        )
                    continue
                if destination.route_match_kind != "equals":
                    raise RegulatoryCatalogError(
                        f"unsupported journey route kind: {destination.route_match_kind}"
                    )
                if destination.route_fact_definition_id not in linked_fact_ids:
                    raise RegulatoryCatalogError(
                        f"route fact is not navigation-linked: {destination.code}"
                    )
                fact = next(
                    item for item in topic.facts if item.id == destination.route_fact_definition_id
                )
                self._validate_route_value(fact, destination.route_match_value)

        if set(navigation_facts) != set(_NAVIGATION_FACT_ORDER):
            raise RegulatoryCatalogError("navigation facts differ from the verified catalog")
        applicability_fact_ids = {
            fact.id for requirement in requirements for fact in requirement.facts.values()
        }
        if applicability_fact_ids & {fact.id for fact in navigation_facts.values()}:
            raise RegulatoryCatalogError("navigation fact entered the applicability graph")
        return current_topics, navigation_facts

    @staticmethod
    def _validate_route_value(fact: CatalogFact, value: object | None) -> None:
        if fact.data_type == FactDataType.BOOLEAN.value and type(value) is bool:
            return
        if (
            fact.data_type == FactDataType.ENUM.value
            and isinstance(value, str)
            and fact.allowed_values is not None
            and value in fact.allowed_values
        ):
            return
        raise RegulatoryCatalogError(f"invalid exact route value for fact: {fact.code}")

    def _resolve_actionability_catalog(
        self,
        catalog: GovernedCatalog,
        requirements: list[_ResolvedRequirement],
    ) -> dict[object, tuple[ActionabilityItem, ...]]:
        if not catalog.actionability_versions:
            return {}
        if catalog.actionability_release_count != 0:
            raise RegulatoryCatalogError(
                "internal actionability catalog unexpectedly contains releases"
            )
        current_requirement_ids = {requirement.version.id for requirement in requirements}
        current_by_code: dict[str, list[CatalogActionabilityVersion]] = defaultdict(list)
        for item in catalog.actionability_versions:
            if item.is_current:
                current_by_code[item.code].append(item)
        if any(len(items) != 1 for items in current_by_code.values()):
            raise RegulatoryCatalogError("actionability code has multiple current versions")

        by_requirement: dict[object, list[ActionabilityItem]] = defaultdict(list)
        for code in sorted(current_by_code):
            item = current_by_code[code][0]
            if item.requirement_version_id not in current_requirement_ids:
                continue
            if item.verification_status != _APPROVED or item.value_state != _VERIFIED:
                raise RegulatoryCatalogError(f"actionability is not verified: {item.code}")
            if (
                item.last_verified_at is None
                or item.next_review_at is None
                or item.next_review_at <= catalog.database_timestamp
            ):
                raise RegulatoryCatalogError(f"actionability is stale: {item.code}")
            if item.detail_type not in _ACTIONABILITY_LABELS:
                raise RegulatoryCatalogError(
                    f"unsupported actionability detail type: {item.detail_type}"
                )
            if item.value_payload is None or item.value_sha256 is None:
                raise RegulatoryCatalogError(f"verified actionability has no value: {item.code}")
            try:
                value = _ACTIONABILITY_VALUE_ADAPTER.validate_python(item.value_payload)
            except ValidationError as exc:
                raise RegulatoryCatalogError(
                    f"invalid typed actionability value: {item.code}"
                ) from exc
            if compute_canonical_sha256(value.model_dump(mode="json")) != item.value_sha256:
                raise RegulatoryCatalogError(f"actionability value hash mismatch: {item.code}")
            expected_kinds = {
                "official_start": "official_destination",
                "prerequisite": "text",
                "document": "text",
                "fee": "money",
                "sequence": "text",
            }
            if value.kind != expected_kinds[item.detail_type]:
                raise RegulatoryCatalogError(f"actionability type and value differ: {item.code}")
            self._validate_governed_source(item.source, catalog)
            label_ar, label_en = _ACTIONABILITY_LABELS[item.detail_type]
            by_requirement[item.requirement_version_id].append(
                ActionabilityItem(
                    code=item.code,
                    actionability_version_id=item.id,
                    version_number=item.version_number,
                    requirement_version_id=item.requirement_version_id,
                    detail_type=item.detail_type,
                    display_order=item.display_order,
                    label_ar=label_ar,
                    label_en=label_en,
                    value=value,
                    source=self._governed_source_trace(item.source),
                    last_verified_at=item.last_verified_at,
                    next_review_at=item.next_review_at,
                )
            )
        return {
            requirement_id: tuple(
                sorted(items, key=lambda value: (value.display_order, value.code))
            )
            for requirement_id, items in by_requirement.items()
        }

    @staticmethod
    def _validate_governed_source(
        source: CatalogGovernedSource,
        catalog: GovernedCatalog,
    ) -> None:
        if source.source_verification_status != _APPROVED:
            raise RegulatoryCatalogError(f"source is not approved: {source.source_code}")
        if source.source_version_review_status != _APPROVED or not source.source_version_is_current:
            raise RegulatoryCatalogError(
                f"source version is not approved/current: {source.source_version_id}"
            )
        if source.domain_verification_status != _APPROVED:
            raise RegulatoryCatalogError(f"source domain is not approved: {source.domain_name}")
        if source.authority.verification_status != _APPROVED:
            raise RegulatoryCatalogError(
                f"source authority is not approved: {source.authority.code}"
            )
        freshness = (
            source.source_next_review_at,
            source.source_version_next_review_at,
            source.domain_next_review_at,
            source.authority.next_review_at,
        )
        if any(value is None or value <= catalog.database_timestamp for value in freshness):
            raise RegulatoryCatalogError(f"source chain is stale: {source.source_code}")
        if source.platform is not None:
            if source.platform.verification_status != _APPROVED:
                raise RegulatoryCatalogError(
                    f"source platform is not approved: {source.platform.code}"
                )
            if (
                source.platform.next_review_at is None
                or source.platform.next_review_at <= catalog.database_timestamp
            ):
                raise RegulatoryCatalogError(f"source platform is stale: {source.platform.code}")
        if (
            source.source_domain_id != source.domain_id_at_review
            or source.source_entity_id != source.responsible_entity_id_at_review
            or (source.platform.id if source.platform is not None else None)
            != source.platform_id_at_review
        ):
            raise RegulatoryCatalogError(f"source review context changed: {source.source_code}")
        parsed = urlsplit(source.resolved_url)
        if parsed.scheme != "https" or parsed.hostname != source.domain_name:
            raise RegulatoryCatalogError(f"unsafe governed source URL: {source.source_code}")

    @staticmethod
    def _governed_source_trace(source: CatalogGovernedSource) -> GovernedSourceTrace:
        if (
            source.source_version_last_verified_at is None
            or source.source_version_next_review_at is None
        ):
            raise RegulatoryCatalogError(f"source has incomplete freshness: {source.source_code}")
        return GovernedSourceTrace(
            source_id=source.source_id,
            source_code=source.source_code,
            official_title_ar=source.official_title_ar,
            official_title_en=source.official_title_en,
            official_url=source.resolved_url,
            canonical_host=source.canonical_host,
            source_version_id=source.source_version_id,
            source_version_number=source.source_version_number,
            authority=AuthorityTrace(
                authority_id=source.authority.id,
                code=source.authority.code,
                name_ar=source.authority.name_ar,
                name_en=source.authority.name_en,
                verification_status=source.authority.verification_status,
                last_verified_at=source.authority.last_verified_at,
                next_review_at=source.authority.next_review_at,
            ),
            platform=(
                PlatformTrace(
                    platform_id=source.platform.id,
                    code=source.platform.code,
                    name_ar=source.platform.name_ar,
                    name_en=source.platform.name_en,
                )
                if source.platform is not None
                else None
            ),
            last_verified_at=source.source_version_last_verified_at,
            next_review_at=source.source_version_next_review_at,
        )

    def _resolve_journey(
        self,
        resolved: _ResolvedCatalog,
        profile: NavigationProfile,
    ) -> tuple[tuple[JourneyGuidance, ...], tuple[MissingNavigationInformation, ...]]:
        values = profile.as_fact_values()
        affected_topics: dict[str, set[str]] = defaultdict(set)
        guidance: list[JourneyGuidance] = []
        for topic in resolved.journey_topics:
            missing_codes = tuple(
                sorted(fact.code for fact in topic.facts if values.get(fact.code) is None)
            )
            for code in missing_codes:
                affected_topics[code].add(topic.topic_code)
            destinations: list[JourneyDestination] = []
            for destination in topic.destinations:
                matches = destination.route_match_kind == "always"
                if destination.route_match_kind == "equals":
                    route_fact = next(
                        fact
                        for fact in topic.facts
                        if fact.id == destination.route_fact_definition_id
                    )
                    supplied = values.get(route_fact.code)
                    matches = supplied is not None and supplied == destination.route_match_value
                if matches:
                    destinations.append(
                        JourneyDestination(
                            code=destination.code,
                            destination_kind=destination.destination_kind,
                            guidance_ar=destination.guidance_ar,
                            guidance_en=destination.guidance_en,
                            what_to_verify_ar=destination.what_to_verify_ar,
                            what_to_verify_en=destination.what_to_verify_en,
                            is_primary=destination.is_primary,
                            source=self._governed_source_trace(destination.evidence.source),
                        )
                    )
            guidance.append(
                JourneyGuidance(
                    topic_code=topic.topic_code,
                    topic_version_id=topic.id,
                    activity_code=topic.activity_code,
                    title_ar=topic.title_ar,
                    title_en=topic.title_en,
                    coverage_state=topic.coverage_state,
                    verified_summary_ar=topic.verified_summary_ar,
                    verified_summary_en=topic.verified_summary_en,
                    limitation_summary_ar=topic.limitation_summary_ar,
                    limitation_summary_en=topic.limitation_summary_en,
                    what_to_verify_ar=topic.what_to_verify_ar,
                    what_to_verify_en=topic.what_to_verify_en,
                    routing_status=(
                        JourneyRoutingStatus.NEEDS_INFORMATION
                        if missing_codes
                        else JourneyRoutingStatus.ROUTED
                    ),
                    destinations=tuple(destinations),
                )
            )
        missing = tuple(
            MissingNavigationInformation(
                fact_code=code,
                question=self._question_for(
                    resolved.navigation_facts[code],
                    purpose=QuestionPurpose.NAVIGATION,
                ),
                affected_topic_codes=tuple(sorted(affected_topics[code])),
            )
            for code in _NAVIGATION_FACT_ORDER
            if code in affected_topics
        )
        return tuple(guidance), missing

    def _evaluate_requirement(
        self,
        requirement: _ResolvedRequirement,
        profile: BusinessProfile,
        actionability: tuple[ActionabilityItem, ...],
    ) -> ChecklistItem:
        if requirement.condition is None:
            return self._checklist_item(
                requirement,
                ApplicabilityStatus.APPLIES,
                ApplicabilityReasonCode.UNCONDITIONAL_CURRENT_REQUIREMENT,
                None,
                (),
                (),
                actionability,
            )

        expression = parse_condition(requirement.condition.expression)
        supplied: dict[str, object] = {
            code: value
            for code, value in profile.facts.items()
            if code in requirement.definitions and value is not None
        }
        try:
            truth = evaluate_condition(expression, requirement.definitions, supplied)
        except FactValueError as exc:
            raise BusinessProfileError(str(exc)) from exc

        evaluated_facts = self._evaluated_fact_traces(requirement, profile)

        if truth is TruthValue.TRUE:
            return self._checklist_item(
                requirement,
                ApplicabilityStatus.APPLIES,
                ApplicabilityReasonCode.CONDITION_TRUE,
                truth,
                (),
                evaluated_facts,
                actionability,
            )
        if truth is TruthValue.FALSE:
            return self._checklist_item(
                requirement,
                ApplicabilityStatus.DOES_NOT_APPLY,
                ApplicabilityReasonCode.CONDITION_FALSE,
                truth,
                (),
                evaluated_facts,
                (),
            )
        missing = _blocking_missing_fact_codes(expression, requirement.definitions, supplied)
        if not missing:
            raise RegulatoryCatalogError(
                f"UNKNOWN condition has no missing governed fact: {requirement.family.code}"
            )
        return self._checklist_item(
            requirement,
            ApplicabilityStatus.NEEDS_INFORMATION,
            ApplicabilityReasonCode.MISSING_REQUIRED_FACT,
            truth,
            missing,
            evaluated_facts,
            (),
        )

    def _evaluated_fact_traces(
        self,
        requirement: _ResolvedRequirement,
        profile: BusinessProfile,
    ) -> tuple[EvaluatedFactTrace, ...]:
        """Expose only governed condition inputs, without inference or persistence."""

        traces: list[EvaluatedFactTrace] = []
        for code in sorted(requirement.facts):
            question = self._question_for(requirement.facts[code])
            if question.answer_labels is None:
                raise RegulatoryCatalogError(
                    f"applicability fact is not Boolean: {question.fact_code}"
                )
            traces.append(
                EvaluatedFactTrace(
                    fact_code=code,
                    question_ar=question.question_ar,
                    question_en=question.question_en,
                    supplied_value=profile.facts.get(code),
                    answer_labels=question.answer_labels,
                )
            )
        return tuple(traces)

    def _checklist_item(
        self,
        requirement: _ResolvedRequirement,
        status: ApplicabilityStatus,
        reason: ApplicabilityReasonCode,
        truth: TruthValue | None,
        missing: tuple[str, ...],
        evaluated_facts: tuple[EvaluatedFactTrace, ...],
        actionability: tuple[ActionabilityItem, ...],
    ) -> ChecklistItem:
        version = requirement.version
        active_sources = tuple(
            SourceTrace(
                requirement_source_id=source.requirement_source_id,
                source_id=source.source_id,
                source_code=source.source_code,
                official_title_ar=source.official_title_ar,
                official_title_en=source.official_title_en,
                source_role=source.source_role,
                relationship_status=source.relationship_status,
                canonical_url=source.canonical_url,
                canonical_host=source.canonical_host,
                source_verification_status=source.source_verification_status,
                source_last_verified_at=source.source_last_verified_at,
                source_next_review_at=source.source_next_review_at,
                source_version_id=source.source_version_id,
                source_version_number=source.source_version_number,
                reviewed_url=source.reviewed_url,
                resolved_url=source.resolved_url,
                source_version_review_status=source.source_version_review_status,
                source_version_is_current=source.source_version_is_current,
                source_version_last_verified_at=source.source_version_last_verified_at,
                source_version_next_review_at=source.source_version_next_review_at,
                excerpt_locator=source.excerpt_locator,
            )
            for source in version.sources
            if source.relationship_status == _ACTIVE
        )
        authority = version.authority
        return ChecklistItem(
            requirement_code=requirement.family.code,
            requirement_version_id=version.id,
            requirement_version=version.version_number,
            project_arabic_title=version.canonical_title_ar,
            project_arabic_description=version.canonical_description_ar,
            project_english_title=version.canonical_title_en,
            project_english_description=version.canonical_description_en,
            authority=AuthorityTrace(
                authority_id=authority.id,
                code=authority.code,
                name_ar=authority.name_ar,
                name_en=authority.name_en,
                verification_status=authority.verification_status,
                last_verified_at=authority.last_verified_at,
                next_review_at=authority.next_review_at,
            ),
            activity_code=requirement.selected_activity_code,
            applicability_status=status,
            reason_code=reason,
            condition_result=truth,
            missing_fact_codes=missing,
            evaluated_facts=evaluated_facts,
            condition_expression_sha256=(
                requirement.condition.expression_sha256
                if requirement.condition is not None
                else None
            ),
            sources=active_sources,
            regulatory_status=version.verification_status,
            actionability=actionability,
        )

    def _question_for(
        self,
        fact: CatalogFact,
        *,
        purpose: QuestionPurpose = QuestionPurpose.APPLICABILITY,
    ) -> QuestionnaireItem:
        authored = QUESTION_TEXT.get(fact.code)
        if authored is None:
            raise RegulatoryCatalogError(f"missing project-authored question: {fact.code}")
        try:
            data_type = FactDataType(fact.data_type)
        except ValueError as exc:
            raise RegulatoryCatalogError(f"unsupported fact type: {fact.code}") from exc
        authored_option_values = tuple(option.value for option in authored.options)
        if data_type is FactDataType.ENUM:
            if fact.allowed_values is None or authored_option_values != fact.allowed_values:
                raise RegulatoryCatalogError(
                    f"question options differ from governed enum: {fact.code}"
                )
        elif authored.options:
            raise RegulatoryCatalogError(
                f"Boolean question cannot define enum options: {fact.code}"
            )
        answer_labels = (
            QuestionnaireAnswerLabels(
                true_ar=authored.true_label_ar,
                true_en=authored.true_label_en,
                false_ar=authored.false_label_ar,
                false_en=authored.false_label_en,
                unknown_ar=authored.unknown_label_ar,
                unknown_en=authored.unknown_label_en,
            )
            if data_type is FactDataType.BOOLEAN
            else None
        )
        return QuestionnaireItem(
            fact_code=fact.code,
            fact_version=fact.version_number,
            data_type=data_type,
            purpose=purpose,
            question_ar=authored.question_ar,
            question_en=authored.question_en,
            help_text_ar=authored.help_text_ar,
            help_text_en=authored.help_text_en,
            answer_labels=answer_labels,
            options=tuple(
                QuestionnaireOption(
                    value=option.value,
                    label_ar=option.label_ar,
                    label_en=option.label_en,
                )
                for option in authored.options
            ),
            unknown_label_ar=authored.unknown_label_ar,
            unknown_label_en=authored.unknown_label_en,
        )

    @staticmethod
    def _activity_summary(catalog: GovernedCatalog) -> ActivitySummary:
        return ActivitySummary(
            code=catalog.activity.code,
            name_ar=catalog.activity.name_ar,
            name_en=catalog.activity.name_en,
        )

    def _build_snapshot(
        self,
        resolved: _ResolvedCatalog,
        items: list[ChecklistItem],
    ) -> RegulatorySnapshot:
        version_ids = tuple(sorted((item.requirement_version_id for item in items), key=str))
        fact_ids = tuple(
            sorted(
                {
                    fact.id
                    for requirement in resolved.requirements
                    for fact in requirement.facts.values()
                },
                key=str,
            )
        )
        fingerprint_payload = {
            "activity": resolved.catalog.activity.code,
            "facts": [str(value) for value in fact_ids],
            "migration": resolved.catalog.migration_revision,
            "requirements": [
                {
                    "code": item.requirement_code,
                    "condition": item.condition_expression_sha256,
                    "sources": [str(source.source_version_id) for source in item.sources],
                    "version_id": str(item.requirement_version_id),
                }
                for item in sorted(items, key=_item_sort_key)
            ],
        }
        canonical = json.dumps(
            fingerprint_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return RegulatorySnapshot(
            catalog_mode=resolved.catalog.catalog_mode,
            migration_revision=resolved.catalog.migration_revision,
            catalog_fingerprint=hashlib.sha256(canonical).hexdigest(),
            requirement_version_ids=version_ids,
            fact_definition_ids=fact_ids,
            publication_count=resolved.catalog.publication_count,
        )


def _blocking_missing_fact_codes(
    expression: ConditionExpression,
    definitions: dict[str, FactDefinition],
    supplied: dict[str, object],
) -> tuple[str, ...]:
    """Trace only UNKNOWN branches while the condition evaluator remains authoritative."""

    if evaluate_condition(expression, definitions, supplied) is not TruthValue.UNKNOWN:
        return ()
    if isinstance(expression, EqualityPredicate):
        return (expression.fact,) if expression.fact not in supplied else ()
    if isinstance(expression, NotCondition):
        return _blocking_missing_fact_codes(expression.arg, definitions, supplied)
    if isinstance(expression, (AllCondition, AnyCondition)):
        missing = {
            code
            for child in expression.args
            if evaluate_condition(child, definitions, supplied) is TruthValue.UNKNOWN
            for code in _blocking_missing_fact_codes(child, definitions, supplied)
        }
        return tuple(sorted(missing))
    raise RegulatoryCatalogError("unsupported condition expression")


def _item_sort_key(item: ChecklistItem) -> tuple[str, int]:
    return item.requirement_code, item.requirement_version


__all__ = ["ChecklistService"]
