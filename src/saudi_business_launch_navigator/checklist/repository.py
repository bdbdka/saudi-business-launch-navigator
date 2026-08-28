"""Read-only SQLAlchemy repository for the governed catalog."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy import Text, column, func, select, table, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from saudi_business_launch_navigator.checklist.exceptions import UnsupportedActivityError
from saudi_business_launch_navigator.checklist.models import CatalogMode
from saudi_business_launch_navigator.db.base import NAVIGATOR_SCHEMA
from saudi_business_launch_navigator.db.models.actionability import (
    RequirementActionabilityRelease,
    RequirementActionabilityVersion,
)
from saudi_business_launch_navigator.db.models.conditions import (
    FactDefinition,
    RequirementConditionFact,
    RequirementConditionSet,
)
from saudi_business_launch_navigator.db.models.governance import (
    Domain,
    GovernmentEntity,
    Platform,
    Source,
    SourceVersion,
)
from saudi_business_launch_navigator.db.models.journey import (
    JourneyTopic,
    JourneyTopicDestination,
    JourneyTopicEvidence,
    JourneyTopicFactLink,
    JourneyTopicRelease,
    JourneyTopicVersion,
)
from saudi_business_launch_navigator.db.models.reference import BusinessActivity
from saudi_business_launch_navigator.db.models.requirements import (
    Requirement,
    RequirementActivity,
    RequirementPublication,
    RequirementSource,
    RequirementVersion,
)


@dataclass(frozen=True)
class CatalogActivity:
    id: UUID
    code: str
    name_ar: str
    name_en: str
    is_active: bool


@dataclass(frozen=True)
class CatalogAuthority:
    id: UUID
    code: str
    name_ar: str
    name_en: str | None
    verification_status: str
    last_verified_at: datetime | None
    next_review_at: datetime | None


@dataclass(frozen=True)
class CatalogFact:
    id: UUID
    code: str
    version_number: int
    data_type: str
    allowed_values: tuple[str, ...] | None
    unit: str | None
    privacy_class: str
    verification_status: str
    is_current: bool


@dataclass(frozen=True)
class CatalogCondition:
    id: UUID
    expression: object
    expression_sha256: str
    dsl_schema_version: int
    verification_status: str
    fact_definition_ids: tuple[UUID, ...]


@dataclass(frozen=True)
class CatalogSource:
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


@dataclass(frozen=True)
class CatalogPlatform:
    id: UUID
    code: str
    name_ar: str
    name_en: str | None
    verification_status: str
    next_review_at: datetime | None


@dataclass(frozen=True)
class CatalogGovernedSource:
    source_id: UUID
    source_code: str
    official_title_ar: str | None
    official_title_en: str | None
    canonical_url: str
    canonical_host: str
    source_verification_status: str
    source_next_review_at: datetime | None
    source_domain_id: UUID
    source_entity_id: UUID
    source_version_id: UUID
    source_version_number: int
    reviewed_url: str
    resolved_url: str
    source_version_review_status: str
    source_version_is_current: bool
    source_version_last_verified_at: datetime | None
    source_version_next_review_at: datetime | None
    domain_id_at_review: UUID
    responsible_entity_id_at_review: UUID
    platform_id_at_review: UUID | None
    domain_name: str
    domain_verification_status: str
    domain_next_review_at: datetime | None
    authority: CatalogAuthority
    platform: CatalogPlatform | None


@dataclass(frozen=True)
class CatalogJourneyEvidence:
    id: UUID
    source: CatalogGovernedSource
    evidence_role: str
    excerpt_locator: str | None


@dataclass(frozen=True)
class CatalogJourneyDestination:
    code: str
    destination_kind: str
    guidance_ar: str
    guidance_en: str | None
    what_to_verify_ar: str
    what_to_verify_en: str | None
    route_fact_definition_id: UUID | None
    route_match_kind: str
    route_match_value: object | None
    display_order: int
    is_primary: bool
    evidence: CatalogJourneyEvidence


@dataclass(frozen=True)
class CatalogJourneyTopicVersion:
    id: UUID
    topic_code: str
    activity_code: str
    title_ar: str
    title_en: str | None
    coverage_state: str
    verified_summary_ar: str | None
    verified_summary_en: str | None
    limitation_summary_ar: str | None
    limitation_summary_en: str | None
    what_to_verify_ar: str | None
    what_to_verify_en: str | None
    verification_status: str
    is_current: bool
    last_verified_at: datetime | None
    next_review_at: datetime | None
    evidence: tuple[CatalogJourneyEvidence, ...]
    facts: tuple[CatalogFact, ...]
    destinations: tuple[CatalogJourneyDestination, ...]


@dataclass(frozen=True)
class CatalogActionabilityVersion:
    id: UUID
    code: str
    version_number: int
    requirement_version_id: UUID
    detail_type: str
    value_state: str
    value_payload: dict[str, object] | None
    value_sha256: str | None
    source: CatalogGovernedSource
    verification_status: str
    is_current: bool
    last_verified_at: datetime | None
    next_review_at: datetime | None
    display_order: int


@dataclass(frozen=True)
class CatalogRequirementVersion:
    id: UUID
    version_number: int
    canonical_title_ar: str
    canonical_description_ar: str
    canonical_title_en: str | None
    canonical_description_en: str | None
    verification_status: str
    is_current: bool
    authority: CatalogAuthority
    activity_codes: tuple[str, ...]
    conditions: tuple[CatalogCondition, ...]
    sources: tuple[CatalogSource, ...]


@dataclass(frozen=True)
class CatalogRequirementFamily:
    id: UUID
    code: str
    versions: tuple[CatalogRequirementVersion, ...]


@dataclass(frozen=True)
class GovernedCatalog:
    activity: CatalogActivity
    requirement_families: tuple[CatalogRequirementFamily, ...]
    facts: tuple[CatalogFact, ...]
    migration_revision: str
    publication_count: int
    database_timestamp: datetime
    catalog_mode: CatalogMode = CatalogMode.INTERNAL_GOVERNED
    journey_topics: tuple[CatalogJourneyTopicVersion, ...] = ()
    actionability_versions: tuple[CatalogActionabilityVersion, ...] = ()
    journey_release_count: int = 0
    actionability_release_count: int = 0


class GovernedCatalogRepository(Protocol):
    """Boundary that supplies one immutable read-only catalog snapshot."""

    async def load(self, activity_code: str) -> GovernedCatalog:
        """Load the governed database graph for one supported activity."""


class SqlAlchemyGovernedCatalogRepository:
    """Load application data inside a transaction explicitly marked READ ONLY."""

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def load(self, activity_code: str) -> GovernedCatalog:
        async with (
            AsyncSession(self._engine, expire_on_commit=False) as session,
            session.begin(),
        ):
            await session.execute(text("SET TRANSACTION READ ONLY"))
            return await self._load_in_transaction(session, activity_code)

    async def _load_in_transaction(
        self,
        session: AsyncSession,
        activity_code: str,
    ) -> GovernedCatalog:
        activity = (
            await session.execute(
                select(BusinessActivity).where(BusinessActivity.code == activity_code)
            )
        ).scalar_one_or_none()
        if activity is None or not activity.is_active:
            raise UnsupportedActivityError(f"unsupported activity: {activity_code}")

        database_timestamp = (await session.execute(select(func.current_timestamp()))).scalar_one()
        alembic_version = table(
            "alembic_version",
            column("version_num", Text),
            schema=NAVIGATOR_SCHEMA,
        )
        migration_revision = (
            await session.execute(select(alembic_version.c.version_num))
        ).scalar_one()
        publication_count = (
            await session.execute(select(func.count()).select_from(RequirementPublication))
        ).scalar_one()
        journey_release_count = (
            await session.execute(select(func.count()).select_from(JourneyTopicRelease))
        ).scalar_one()
        actionability_release_count = (
            await session.execute(select(func.count()).select_from(RequirementActionabilityRelease))
        ).scalar_one()

        requirements = (
            (await session.execute(select(Requirement).order_by(Requirement.code))).scalars().all()
        )
        versions = (
            (
                await session.execute(
                    select(RequirementVersion).order_by(
                        RequirementVersion.requirement_id,
                        RequirementVersion.version_number,
                    )
                )
            )
            .scalars()
            .all()
        )
        activities = (
            await session.execute(
                select(RequirementActivity, BusinessActivity).join(
                    BusinessActivity,
                    BusinessActivity.id == RequirementActivity.activity_id,
                )
            )
        ).all()
        authorities = (await session.execute(select(GovernmentEntity))).scalars().all()
        facts = (
            (
                await session.execute(
                    select(FactDefinition).order_by(
                        FactDefinition.code,
                        FactDefinition.version_number,
                    )
                )
            )
            .scalars()
            .all()
        )
        conditions = (await session.execute(select(RequirementConditionSet))).scalars().all()
        condition_fact_links = (
            (await session.execute(select(RequirementConditionFact))).scalars().all()
        )
        source_rows = (
            await session.execute(
                select(RequirementSource, SourceVersion, Source)
                .join(SourceVersion, SourceVersion.id == RequirementSource.source_version_id)
                .join(Source, Source.id == SourceVersion.source_id)
            )
        ).all()
        source_context_rows = (
            await session.execute(
                select(SourceVersion, Source, Domain, GovernmentEntity, Platform)
                .join(Source, Source.id == SourceVersion.source_id)
                .join(Domain, Domain.id == Source.domain_id)
                .join(GovernmentEntity, GovernmentEntity.id == Source.responsible_entity_id)
                .outerjoin(Platform, Platform.id == Domain.platform_id)
            )
        ).all()
        journey_version_rows = (
            await session.execute(
                select(JourneyTopicVersion, JourneyTopic)
                .join(JourneyTopic, JourneyTopic.id == JourneyTopicVersion.journey_topic_id)
                .where(JourneyTopicVersion.activity_id == activity.id)
                .order_by(JourneyTopic.code, JourneyTopicVersion.version_number)
            )
        ).all()
        journey_version_ids = tuple(version.id for version, _topic in journey_version_rows)
        journey_evidence = (
            (
                await session.execute(
                    select(JourneyTopicEvidence).where(
                        JourneyTopicEvidence.journey_topic_version_id.in_(journey_version_ids)
                    )
                )
            )
            .scalars()
            .all()
            if journey_version_ids
            else []
        )
        journey_fact_links = (
            (
                await session.execute(
                    select(JourneyTopicFactLink).where(
                        JourneyTopicFactLink.journey_topic_version_id.in_(journey_version_ids)
                    )
                )
            )
            .scalars()
            .all()
            if journey_version_ids
            else []
        )
        journey_destinations = (
            (
                await session.execute(
                    select(JourneyTopicDestination).where(
                        JourneyTopicDestination.journey_topic_version_id.in_(journey_version_ids)
                    )
                )
            )
            .scalars()
            .all()
            if journey_version_ids
            else []
        )
        actionability_versions = (
            (
                await session.execute(
                    select(RequirementActionabilityVersion).order_by(
                        RequirementActionabilityVersion.code,
                        RequirementActionabilityVersion.version_number,
                    )
                )
            )
            .scalars()
            .all()
        )

        authority_by_id = {
            entity.id: CatalogAuthority(
                id=entity.id,
                code=entity.code,
                name_ar=entity.official_name_ar,
                name_en=entity.official_name_en or entity.explanatory_name_en,
                verification_status=entity.verification_status,
                last_verified_at=entity.last_verified_at,
                next_review_at=entity.next_review_at,
            )
            for entity in authorities
        }
        governed_source_by_version: dict[UUID, CatalogGovernedSource] = {}
        for source_version, source, domain, entity, platform in source_context_rows:
            catalog_platform = (
                CatalogPlatform(
                    id=platform.id,
                    code=platform.code,
                    name_ar=platform.official_name_ar,
                    name_en=platform.official_name_en or platform.explanatory_name_en,
                    verification_status=platform.verification_status,
                    next_review_at=platform.next_review_at,
                )
                if platform is not None
                else None
            )
            governed_source_by_version[source_version.id] = CatalogGovernedSource(
                source_id=source.id,
                source_code=source.code,
                official_title_ar=source.official_title_ar,
                official_title_en=source.official_title_en,
                canonical_url=source.canonical_url,
                canonical_host=source.canonical_host,
                source_verification_status=source.verification_status,
                source_next_review_at=source.next_review_at,
                source_domain_id=source.domain_id,
                source_entity_id=source.responsible_entity_id,
                source_version_id=source_version.id,
                source_version_number=source_version.version_number,
                reviewed_url=source_version.reviewed_url,
                resolved_url=source_version.resolved_url,
                source_version_review_status=source_version.review_status,
                source_version_is_current=source_version.is_current,
                source_version_last_verified_at=source_version.last_verified_at,
                source_version_next_review_at=source_version.next_review_at,
                domain_id_at_review=source_version.domain_id_at_review,
                responsible_entity_id_at_review=(source_version.responsible_entity_id_at_review),
                platform_id_at_review=source_version.platform_id_at_review,
                domain_name=domain.domain_name,
                domain_verification_status=domain.verification_status,
                domain_next_review_at=domain.next_review_at,
                authority=authority_by_id[entity.id],
                platform=catalog_platform,
            )
        activity_codes_by_version: dict[UUID, set[str]] = defaultdict(set)
        for link, linked_activity in activities:
            activity_codes_by_version[link.requirement_version_id].add(linked_activity.code)

        fact_ids_by_condition: dict[UUID, set[UUID]] = defaultdict(set)
        for link in condition_fact_links:
            fact_ids_by_condition[link.condition_set_id].add(link.fact_definition_id)

        conditions_by_version: dict[UUID, list[CatalogCondition]] = defaultdict(list)
        for condition in conditions:
            conditions_by_version[condition.requirement_version_id].append(
                CatalogCondition(
                    id=condition.id,
                    expression=condition.expression,
                    expression_sha256=condition.expression_sha256,
                    dsl_schema_version=condition.dsl_schema_version,
                    verification_status=condition.verification_status,
                    fact_definition_ids=tuple(sorted(fact_ids_by_condition[condition.id], key=str)),
                )
            )

        sources_by_version: dict[UUID, list[CatalogSource]] = defaultdict(list)
        for relationship, source_version, source in source_rows:
            sources_by_version[relationship.requirement_version_id].append(
                CatalogSource(
                    requirement_source_id=relationship.id,
                    source_id=source.id,
                    source_code=source.code,
                    official_title_ar=source.official_title_ar,
                    official_title_en=source.official_title_en,
                    source_role=relationship.source_role,
                    relationship_status=relationship.relationship_status,
                    canonical_url=source.canonical_url,
                    canonical_host=source.canonical_host,
                    source_verification_status=source.verification_status,
                    source_last_verified_at=source.last_verified_at,
                    source_next_review_at=source.next_review_at,
                    source_version_id=source_version.id,
                    source_version_number=source_version.version_number,
                    reviewed_url=source_version.reviewed_url,
                    resolved_url=source_version.resolved_url,
                    source_version_review_status=source_version.review_status,
                    source_version_is_current=source_version.is_current,
                    source_version_last_verified_at=source_version.last_verified_at,
                    source_version_next_review_at=source_version.next_review_at,
                    excerpt_locator=relationship.excerpt_locator,
                )
            )

        versions_by_requirement: dict[UUID, list[CatalogRequirementVersion]] = defaultdict(list)
        for version in versions:
            versions_by_requirement[version.requirement_id].append(
                CatalogRequirementVersion(
                    id=version.id,
                    version_number=version.version_number,
                    canonical_title_ar=version.canonical_title_ar,
                    canonical_description_ar=version.canonical_description_ar,
                    canonical_title_en=version.canonical_title_en,
                    canonical_description_en=version.canonical_description_en,
                    verification_status=version.verification_status,
                    is_current=version.is_current,
                    authority=authority_by_id[version.responsible_entity_id],
                    activity_codes=tuple(sorted(activity_codes_by_version[version.id])),
                    conditions=tuple(
                        sorted(conditions_by_version[version.id], key=lambda item: str(item.id))
                    ),
                    sources=tuple(
                        sorted(
                            sources_by_version[version.id],
                            key=lambda item: (
                                item.source_role,
                                item.source_code,
                                str(item.source_version_id),
                            ),
                        )
                    ),
                )
            )

        fact_by_id = {fact.id: fact for fact in facts}
        journey_evidence_by_id: dict[UUID, CatalogJourneyEvidence] = {}
        journey_evidence_by_version: dict[UUID, list[CatalogJourneyEvidence]] = defaultdict(list)
        for evidence in journey_evidence:
            catalog_evidence = CatalogJourneyEvidence(
                id=evidence.id,
                source=governed_source_by_version[evidence.source_version_id],
                evidence_role=evidence.evidence_role,
                excerpt_locator=evidence.excerpt_locator,
            )
            journey_evidence_by_id[evidence.id] = catalog_evidence
            journey_evidence_by_version[evidence.journey_topic_version_id].append(catalog_evidence)

        journey_facts_by_version: dict[UUID, list[CatalogFact]] = defaultdict(list)
        for link in journey_fact_links:
            fact = fact_by_id[link.fact_definition_id]
            journey_facts_by_version[link.journey_topic_version_id].append(
                CatalogFact(
                    id=fact.id,
                    code=fact.code,
                    version_number=fact.version_number,
                    data_type=fact.data_type,
                    allowed_values=(
                        tuple(fact.allowed_values) if fact.allowed_values is not None else None
                    ),
                    unit=fact.unit,
                    privacy_class=fact.privacy_class,
                    verification_status=fact.verification_status,
                    is_current=fact.is_current,
                )
            )

        journey_destinations_by_version: dict[UUID, list[CatalogJourneyDestination]] = defaultdict(
            list
        )
        for destination in journey_destinations:
            journey_destinations_by_version[destination.journey_topic_version_id].append(
                CatalogJourneyDestination(
                    code=destination.code,
                    destination_kind=destination.destination_kind,
                    guidance_ar=destination.guidance_ar,
                    guidance_en=destination.guidance_en,
                    what_to_verify_ar=destination.what_to_verify_ar,
                    what_to_verify_en=destination.what_to_verify_en,
                    route_fact_definition_id=destination.route_fact_definition_id,
                    route_match_kind=destination.route_match_kind,
                    route_match_value=destination.route_match_value,
                    display_order=destination.display_order,
                    is_primary=destination.is_primary,
                    evidence=journey_evidence_by_id[destination.journey_topic_evidence_id],
                )
            )

        catalog_journey_topics = tuple(
            CatalogJourneyTopicVersion(
                id=version.id,
                topic_code=topic.code,
                activity_code=activity.code,
                title_ar=version.title_ar,
                title_en=version.title_en,
                coverage_state=version.coverage_state,
                verified_summary_ar=version.verified_summary_ar,
                verified_summary_en=version.verified_summary_en,
                limitation_summary_ar=version.limitation_summary_ar,
                limitation_summary_en=version.limitation_summary_en,
                what_to_verify_ar=version.what_to_verify_ar,
                what_to_verify_en=version.what_to_verify_en,
                verification_status=version.verification_status,
                is_current=version.is_current,
                last_verified_at=version.last_verified_at,
                next_review_at=version.next_review_at,
                evidence=tuple(
                    sorted(
                        journey_evidence_by_version[version.id],
                        key=lambda item: (item.evidence_role, str(item.id)),
                    )
                ),
                facts=tuple(
                    sorted(journey_facts_by_version[version.id], key=lambda item: item.code)
                ),
                destinations=tuple(
                    sorted(
                        journey_destinations_by_version[version.id],
                        key=lambda item: item.display_order,
                    )
                ),
            )
            for version, topic in journey_version_rows
        )

        catalog_actionability = tuple(
            CatalogActionabilityVersion(
                id=item.id,
                code=item.code,
                version_number=item.version_number,
                requirement_version_id=item.requirement_version_id,
                detail_type=item.detail_type,
                value_state=item.value_state,
                value_payload=item.value_payload,
                value_sha256=item.value_sha256,
                source=governed_source_by_version[item.primary_source_version_id],
                verification_status=item.verification_status,
                is_current=item.is_current,
                last_verified_at=item.last_verified_at,
                next_review_at=item.next_review_at,
                display_order=item.display_order,
            )
            for item in actionability_versions
        )

        return GovernedCatalog(
            activity=CatalogActivity(
                id=activity.id,
                code=activity.code,
                name_ar=activity.name_ar,
                name_en=activity.name_en,
                is_active=activity.is_active,
            ),
            requirement_families=tuple(
                CatalogRequirementFamily(
                    id=requirement.id,
                    code=requirement.code,
                    versions=tuple(versions_by_requirement[requirement.id]),
                )
                for requirement in requirements
            ),
            facts=tuple(
                CatalogFact(
                    id=fact.id,
                    code=fact.code,
                    version_number=fact.version_number,
                    data_type=fact.data_type,
                    allowed_values=(
                        tuple(fact.allowed_values) if fact.allowed_values is not None else None
                    ),
                    unit=fact.unit,
                    privacy_class=fact.privacy_class,
                    verification_status=fact.verification_status,
                    is_current=fact.is_current,
                )
                for fact in facts
            ),
            migration_revision=migration_revision,
            publication_count=publication_count,
            database_timestamp=database_timestamp,
            journey_topics=catalog_journey_topics,
            actionability_versions=catalog_actionability,
            journey_release_count=journey_release_count,
            actionability_release_count=actionability_release_count,
        )


class StaticGovernedCatalogRepository:
    """Deterministic in-memory repository used by unit tests and local examples."""

    def __init__(self, catalogs: Mapping[str, GovernedCatalog]) -> None:
        self._catalogs = dict(catalogs)

    async def load(self, activity_code: str) -> GovernedCatalog:
        try:
            return self._catalogs[activity_code]
        except KeyError as exc:
            raise UnsupportedActivityError(f"unsupported activity: {activity_code}") from exc


__all__ = [
    "CatalogActionabilityVersion",
    "CatalogActivity",
    "CatalogAuthority",
    "CatalogCondition",
    "CatalogFact",
    "CatalogGovernedSource",
    "CatalogJourneyDestination",
    "CatalogJourneyEvidence",
    "CatalogJourneyTopicVersion",
    "CatalogPlatform",
    "CatalogRequirementFamily",
    "CatalogRequirementVersion",
    "CatalogSource",
    "GovernedCatalog",
    "GovernedCatalogRepository",
    "SqlAlchemyGovernedCatalogRepository",
    "StaticGovernedCatalogRepository",
]
