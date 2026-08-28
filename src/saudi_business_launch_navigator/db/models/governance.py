"""Governance, source, research, and review table models."""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    PrimaryKeyConstraint,
    Text,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from saudi_business_launch_navigator.db.base import NAVIGATOR_SCHEMA, Base
from saudi_business_launch_navigator.db.statuses import (
    DomainCategory,
    EntityType,
    GovernanceStatus,
    PlatformType,
    ResearchEvidenceRole,
    ResearchRecommendation,
    ResearchStatus,
    ReviewDecision,
    SourceType,
    enum_sql,
)

ROLE_PATTERN = r"^[a-z][a-z0-9_]*$"
CODE_PATTERN = r"^[a-z][a-z0-9_]*$"
DOMAIN_PATTERN = r"^[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$"


class GovernmentEntity(Base):
    """Stable identity for a Saudi government entity."""

    __tablename__ = "government_entities"
    __table_args__ = (
        UniqueConstraint("code", name="uq_government_entities_code"),
        CheckConstraint(f"code ~ '{CODE_PATTERN}'", name="code_format"),
        CheckConstraint(f"entity_type IN ({enum_sql(EntityType)})", name="entity_type"),
        CheckConstraint(
            f"verification_status IN ({enum_sql(GovernanceStatus)})",
            name="verification_status",
        ),
        CheckConstraint("btrim(official_name_ar) <> ''", name="official_name_ar_nonblank"),
        CheckConstraint(
            "valid_until IS NULL OR valid_from IS NULL OR valid_until >= valid_from",
            name="valid_date_order",
        ),
        CheckConstraint(
            "(last_verified_at IS NULL AND review_interval_days IS NULL AND "
            "next_review_at IS NULL) OR (last_verified_at IS NOT NULL AND "
            "review_interval_days IS NOT NULL AND next_review_at IS NOT NULL AND "
            "next_review_at = last_verified_at + make_interval(days => review_interval_days))",
            name="freshness_order",
        ),
        CheckConstraint("review_interval_days BETWEEN 30 AND 180", name="review_interval"),
        CheckConstraint("parent_entity_id IS DISTINCT FROM id", name="not_own_parent"),
        CheckConstraint("supervising_entity_id IS DISTINCT FROM id", name="not_own_supervisor"),
        Index("ix_government_entities_verification_status", "verification_status"),
        Index("ix_government_entities_next_review_at", "next_review_at"),
        Index("ix_government_entities_parent_entity_id", "parent_entity_id"),
        Index("ix_government_entities_supervising_entity_id", "supervising_entity_id"),
        Index(
            "ix_government_entities_verification_review_event_id",
            "verification_review_event_id",
        ),
        {"schema": NAVIGATOR_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(Text)
    entity_type: Mapped[str] = mapped_column(Text)
    official_name_ar: Mapped[str] = mapped_column(Text)
    official_name_en: Mapped[str | None] = mapped_column(Text)
    explanatory_name_en: Mapped[str | None] = mapped_column(Text)
    parent_entity_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.government_entities.id",
            ondelete="RESTRICT",
            name="fk_government_entities_parent",
        ),
    )
    supervising_entity_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.government_entities.id",
            ondelete="RESTRICT",
            name="fk_government_entities_supervisor",
        ),
    )
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_until: Mapped[date | None] = mapped_column(Date)
    verification_status: Mapped[str] = mapped_column(Text, server_default=text("'discovered'"))
    verification_review_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.review_events.id",
            ondelete="RESTRICT",
            name="fk_government_entities_verification_review",
            use_alter=True,
        ),
    )
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_interval_days: Mapped[int | None] = mapped_column(Integer)
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )


class Platform(Base):
    """Government platform, portal, or official publication system."""

    __tablename__ = "platforms"
    __table_args__ = (
        UniqueConstraint("code", name="uq_platforms_code"),
        CheckConstraint(f"code ~ '{CODE_PATTERN}'", name="code_format"),
        CheckConstraint(f"platform_type IN ({enum_sql(PlatformType)})", name="platform_type"),
        CheckConstraint(
            f"verification_status IN ({enum_sql(GovernanceStatus)})",
            name="verification_status",
        ),
        CheckConstraint("btrim(official_name_ar) <> ''", name="official_name_ar_nonblank"),
        CheckConstraint(
            "valid_until IS NULL OR valid_from IS NULL OR valid_until >= valid_from",
            name="valid_date_order",
        ),
        CheckConstraint(
            "(last_verified_at IS NULL AND review_interval_days IS NULL AND "
            "next_review_at IS NULL) OR (last_verified_at IS NOT NULL AND "
            "review_interval_days IS NOT NULL AND next_review_at IS NOT NULL AND "
            "next_review_at = last_verified_at + make_interval(days => review_interval_days))",
            name="freshness_order",
        ),
        CheckConstraint("review_interval_days BETWEEN 30 AND 180", name="review_interval"),
        Index("ix_platforms_responsible_entity_id", "responsible_entity_id"),
        Index("ix_platforms_verification_status", "verification_status"),
        Index("ix_platforms_next_review_at", "next_review_at"),
        Index("ix_platforms_verification_review_event_id", "verification_review_event_id"),
        {"schema": NAVIGATOR_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(Text)
    platform_type: Mapped[str] = mapped_column(Text)
    official_name_ar: Mapped[str] = mapped_column(Text)
    official_name_en: Mapped[str | None] = mapped_column(Text)
    explanatory_name_en: Mapped[str | None] = mapped_column(Text)
    responsible_entity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.government_entities.id",
            ondelete="RESTRICT",
            name="fk_platforms_responsible_entity",
        ),
    )
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_until: Mapped[date | None] = mapped_column(Date)
    verification_status: Mapped[str] = mapped_column(Text, server_default=text("'discovered'"))
    verification_review_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.review_events.id",
            ondelete="RESTRICT",
            name="fk_platforms_verification_review",
            use_alter=True,
        ),
    )
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_interval_days: Mapped[int | None] = mapped_column(Integer)
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )


class Domain(Base):
    """Normalized official domain with reviewed ownership."""

    __tablename__ = "domains"
    __table_args__ = (
        UniqueConstraint("domain_name", name="uq_domains_domain_name"),
        UniqueConstraint("id", "domain_name", name="uq_domains_id_domain_name"),
        CheckConstraint(
            f"domain_name = lower(domain_name) AND domain_name ~ '{DOMAIN_PATTERN}'",
            name="domain_name_format",
        ),
        CheckConstraint(
            "domain_name !~ '(^-|-$|\\.\\.|\\.-|-\\.)'",
            name="domain_name_labels",
        ),
        CheckConstraint(f"domain_category IN ({enum_sql(DomainCategory)})", name="domain_category"),
        CheckConstraint(
            f"verification_status IN ({enum_sql(GovernanceStatus)})",
            name="verification_status",
        ),
        CheckConstraint(
            "verification_status <> 'approved' OR "
            "(verification_method IS NOT NULL AND btrim(verification_method) <> '')",
            name="approved_has_method",
        ),
        CheckConstraint(
            "(last_verified_at IS NULL AND review_interval_days IS NULL AND "
            "next_review_at IS NULL) OR (last_verified_at IS NOT NULL AND "
            "review_interval_days IS NOT NULL AND next_review_at IS NOT NULL AND "
            "next_review_at = last_verified_at + make_interval(days => review_interval_days))",
            name="freshness_order",
        ),
        CheckConstraint("review_interval_days BETWEEN 30 AND 180", name="review_interval"),
        Index("ix_domains_responsible_entity_id", "responsible_entity_id"),
        Index("ix_domains_platform_id", "platform_id"),
        Index("ix_domains_verification_status", "verification_status"),
        Index("ix_domains_next_review_at", "next_review_at"),
        Index("ix_domains_verification_review_event_id", "verification_review_event_id"),
        {"schema": NAVIGATOR_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    domain_name: Mapped[str] = mapped_column(Text)
    domain_category: Mapped[str] = mapped_column(Text)
    responsible_entity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.government_entities.id",
            ondelete="RESTRICT",
            name="fk_domains_responsible_entity",
        ),
    )
    platform_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.platforms.id",
            ondelete="RESTRICT",
            name="fk_domains_platform",
        ),
    )
    verification_status: Mapped[str] = mapped_column(Text, server_default=text("'discovered'"))
    verification_method: Mapped[str | None] = mapped_column(Text)
    redirect_target: Mapped[str | None] = mapped_column(Text)
    verification_review_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.review_events.id",
            ondelete="RESTRICT",
            name="fk_domains_verification_review",
            use_alter=True,
        ),
    )
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_interval_days: Mapped[int | None] = mapped_column(Integer)
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )


class Source(Base):
    """Stable identity for one continuing official resource."""

    __tablename__ = "sources"
    __table_args__ = (
        UniqueConstraint("code", name="uq_sources_code"),
        UniqueConstraint("canonical_url", name="uq_sources_canonical_url"),
        ForeignKeyConstraint(
            ["domain_id", "canonical_host"],
            [
                f"{NAVIGATOR_SCHEMA}.domains.id",
                f"{NAVIGATOR_SCHEMA}.domains.domain_name",
            ],
            ondelete="RESTRICT",
            name="fk_sources_domain_host",
        ),
        CheckConstraint(f"code ~ '{CODE_PATTERN}'", name="code_format"),
        CheckConstraint(f"source_type IN ({enum_sql(SourceType)})", name="source_type"),
        CheckConstraint(
            f"verification_status IN ({enum_sql(GovernanceStatus)})",
            name="verification_status",
        ),
        CheckConstraint("canonical_url ~ '^https://'", name="canonical_url_https"),
        CheckConstraint(
            f"canonical_host = lower(canonical_host) AND "
            f"canonical_host ~ '{DOMAIN_PATTERN}' AND "
            "canonical_host !~ '(^-|-$|\\.\\.|\\.-|-\\.)'",
            name="canonical_host_format",
        ),
        CheckConstraint(
            "(last_verified_at IS NULL AND review_interval_days IS NULL AND "
            "next_review_at IS NULL) OR (last_verified_at IS NOT NULL AND "
            "review_interval_days IS NOT NULL AND next_review_at IS NOT NULL AND "
            "next_review_at = last_verified_at + make_interval(days => review_interval_days))",
            name="freshness_order",
        ),
        CheckConstraint("review_interval_days BETWEEN 30 AND 180", name="review_interval"),
        Index("ix_sources_responsible_entity_id", "responsible_entity_id"),
        Index("ix_sources_domain_id", "domain_id"),
        Index("ix_sources_verification_status", "verification_status"),
        Index("ix_sources_next_review_at", "next_review_at"),
        Index("ix_sources_verification_review_event_id", "verification_review_event_id"),
        {"schema": NAVIGATOR_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(Text)
    responsible_entity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.government_entities.id",
            ondelete="RESTRICT",
            name="fk_sources_responsible_entity",
        ),
    )
    domain_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
    )
    canonical_url: Mapped[str] = mapped_column(Text)
    canonical_host: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(Text)
    official_title_ar: Mapped[str | None] = mapped_column(Text)
    official_title_en: Mapped[str | None] = mapped_column(Text)
    governance_purpose: Mapped[str | None] = mapped_column(Text)
    verification_status: Mapped[str] = mapped_column(Text, server_default=text("'discovered'"))
    verification_review_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.review_events.id",
            ondelete="RESTRICT",
            name="fk_sources_verification_review",
            use_alter=True,
        ),
    )
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_interval_days: Mapped[int | None] = mapped_column(Integer)
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )


class SourceVersion(Base):
    """Immutable reviewed document-level snapshot of a stable source."""

    __tablename__ = "source_versions"
    __table_args__ = (
        UniqueConstraint(
            "source_id",
            "version_number",
            name="uq_source_versions_source_version",
        ),
        CheckConstraint("version_number > 0", name="positive_version_number"),
        CheckConstraint("reviewed_url ~ '^https://'", name="reviewed_url_https"),
        CheckConstraint("resolved_url ~ '^https://'", name="resolved_url_https"),
        CheckConstraint(
            "(content_hash IS NULL AND hash_algorithm IS NULL) OR "
            "(content_hash IS NOT NULL AND hash_algorithm IS NOT NULL)",
            name="hash_pair",
        ),
        CheckConstraint(
            "effective_until IS NULL OR effective_from IS NULL OR "
            "effective_until >= effective_from",
            name="effective_date_order",
        ),
        CheckConstraint(f"review_status IN ({enum_sql(GovernanceStatus)})", name="review_status"),
        CheckConstraint(
            "review_status NOT IN ('expired', 'superseded', 'historical') OR NOT is_current",
            name="inactive_status_not_current",
        ),
        CheckConstraint(
            "(last_verified_at IS NULL AND review_interval_days IS NULL AND "
            "next_review_at IS NULL) OR (last_verified_at IS NOT NULL AND "
            "review_interval_days IS NOT NULL AND next_review_at IS NOT NULL AND "
            "next_review_at = last_verified_at + make_interval(days => review_interval_days))",
            name="freshness_order",
        ),
        CheckConstraint("review_interval_days BETWEEN 30 AND 180", name="review_interval"),
        Index(
            "uq_source_versions_one_current",
            "source_id",
            unique=True,
            postgresql_where=text("is_current"),
        ),
        Index("ix_source_versions_review_status", "review_status"),
        Index("ix_source_versions_next_review_at", "next_review_at"),
        Index("ix_source_versions_domain_id_at_review", "domain_id_at_review"),
        Index(
            "ix_source_versions_responsible_entity_id_at_review",
            "responsible_entity_id_at_review",
        ),
        Index("ix_source_versions_platform_id_at_review", "platform_id_at_review"),
        Index(
            "ix_source_versions_verification_review_event_id",
            "verification_review_event_id",
        ),
        {"schema": NAVIGATOR_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.sources.id",
            ondelete="RESTRICT",
            name="fk_source_versions_source",
        ),
    )
    version_number: Mapped[int] = mapped_column(Integer)
    reviewed_url: Mapped[str] = mapped_column(Text)
    resolved_url: Mapped[str] = mapped_column(Text)
    domain_id_at_review: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.domains.id",
            ondelete="RESTRICT",
            name="fk_source_versions_domain_at_review",
        ),
    )
    responsible_entity_id_at_review: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.government_entities.id",
            ondelete="RESTRICT",
            name="fk_source_versions_entity_at_review",
        ),
    )
    platform_id_at_review: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.platforms.id",
            ondelete="RESTRICT",
            name="fk_source_versions_platform_at_review",
        ),
    )
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    publication_date: Mapped[date | None] = mapped_column(Date)
    effective_from: Mapped[date | None] = mapped_column(Date)
    effective_until: Mapped[date | None] = mapped_column(Date)
    content_hash: Mapped[str | None] = mapped_column(Text)
    hash_algorithm: Mapped[str | None] = mapped_column(Text)
    review_status: Mapped[str] = mapped_column(Text, server_default=text("'pending_review'"))
    is_current: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    verification_review_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.review_events.id",
            ondelete="RESTRICT",
            name="fk_source_versions_verification_review",
            use_alter=True,
        ),
    )
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_interval_days: Mapped[int | None] = mapped_column(Integer)
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )


class ResearchEvent(Base):
    """Append-only research event with one real foreign-key target."""

    __tablename__ = "research_events"
    __table_args__ = (
        UniqueConstraint("event_code", name="uq_research_events_event_code"),
        CheckConstraint(f"event_code ~ '{CODE_PATTERN}'", name="event_code_format"),
        CheckConstraint(
            "num_nonnulls(government_entity_id, platform_id, domain_id, source_id, "
            "source_version_id, requirement_version_id, requirement_source_id, "
            "journey_topic_version_id, requirement_actionability_version_id) = 1",
            name="exactly_one_target",
        ),
        CheckConstraint(f"research_status IN ({enum_sql(ResearchStatus)})", name="research_status"),
        CheckConstraint(
            f"recommendation IS NULL OR recommendation IN ({enum_sql(ResearchRecommendation)})",
            name="recommendation",
        ),
        CheckConstraint(f"researched_by_role ~ '{ROLE_PATTERN}'", name="researcher_role"),
        Index("ix_research_events_research_status", "research_status"),
        Index("ix_research_events_government_entity_id", "government_entity_id"),
        Index("ix_research_events_platform_id", "platform_id"),
        Index("ix_research_events_domain_id", "domain_id"),
        Index("ix_research_events_source_id", "source_id"),
        Index("ix_research_events_source_version_id", "source_version_id"),
        Index("ix_research_events_requirement_version_id", "requirement_version_id"),
        Index("ix_research_events_requirement_source_id", "requirement_source_id"),
        Index("ix_research_events_journey_topic_version_id", "journey_topic_version_id"),
        Index(
            "ix_research_events_requirement_actionability_version_id",
            "requirement_actionability_version_id",
        ),
        {"schema": NAVIGATOR_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    event_code: Mapped[str] = mapped_column(Text)
    government_entity_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.government_entities.id",
            ondelete="RESTRICT",
            name="fk_research_events_government_entity",
        ),
    )
    platform_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.platforms.id",
            ondelete="RESTRICT",
            name="fk_research_events_platform",
        ),
    )
    domain_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.domains.id",
            ondelete="RESTRICT",
            name="fk_research_events_domain",
        ),
    )
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.sources.id",
            ondelete="RESTRICT",
            name="fk_research_events_source",
        ),
    )
    source_version_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.source_versions.id",
            ondelete="RESTRICT",
            name="fk_research_events_source_version",
        ),
    )
    requirement_version_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.requirement_versions.id",
            ondelete="RESTRICT",
            name="fk_research_events_requirement_version",
            use_alter=True,
        ),
    )
    requirement_source_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.requirement_sources.id",
            ondelete="RESTRICT",
            name="fk_research_events_requirement_source",
            use_alter=True,
        ),
    )
    journey_topic_version_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.journey_topic_versions.id",
            ondelete="RESTRICT",
            name="fk_research_events_journey_topic_version",
            use_alter=True,
        ),
    )
    requirement_actionability_version_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.requirement_actionability_versions.id",
            ondelete="RESTRICT",
            name="fk_research_events_requirement_actionability_version",
            use_alter=True,
        ),
    )
    research_status: Mapped[str] = mapped_column(Text)
    recommendation: Mapped[str | None] = mapped_column(Text)
    researched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    researched_by_role: Mapped[str] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )


class ResearchEventEvidence(Base):
    """Source-version evidence inspected by a research event."""

    __tablename__ = "research_event_evidence"
    __table_args__ = (
        PrimaryKeyConstraint("research_event_id", "source_version_id"),
        CheckConstraint(
            f"evidence_role IN ({enum_sql(ResearchEvidenceRole)})", name="evidence_role"
        ),
        Index("ix_research_event_evidence_source_version_id", "source_version_id"),
        {"schema": NAVIGATOR_SCHEMA},
    )

    research_event_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.research_events.id",
            ondelete="RESTRICT",
            name="fk_research_event_evidence_research_event",
        ),
    )
    source_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.source_versions.id",
            ondelete="RESTRICT",
            name="fk_research_event_evidence_source_version",
        ),
    )
    evidence_role: Mapped[str] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )


class ReviewEvent(Base):
    """Append-only human governance decision kept separate from research."""

    __tablename__ = "review_events"
    __table_args__ = (
        CheckConstraint(f"decision IN ({enum_sql(ReviewDecision)})", name="decision"),
        CheckConstraint(f"reviewed_by_role ~ '{ROLE_PATTERN}'", name="reviewer_role"),
        CheckConstraint("btrim(reason) <> ''", name="reason_nonblank"),
        CheckConstraint(
            "authorized_review_interval_days IS NULL OR "
            "authorized_review_interval_days BETWEEN 30 AND 180",
            name="authorized_review_interval",
        ),
        CheckConstraint(
            "authorized_review_interval_days IS NULL OR decision = 'approved'",
            name="review_interval_requires_approval",
        ),
        CheckConstraint(
            "(authorized_review_interval_days IS NULL AND review_interval_reason IS NULL) "
            "OR (authorized_review_interval_days IS NOT NULL AND "
            "review_interval_reason IS NOT NULL AND btrim(review_interval_reason) <> '')",
            name="review_interval_justification",
        ),
        Index("ix_review_events_research_event_id", "research_event_id"),
        Index("ix_review_events_decision_reviewed_at", "decision", "reviewed_at"),
        {"schema": NAVIGATOR_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    research_event_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.research_events.id",
            ondelete="RESTRICT",
            name="fk_review_events_research_event",
        ),
    )
    decision: Mapped[str] = mapped_column(Text)
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )
    reviewed_by_role: Mapped[str] = mapped_column(Text)
    independent_review: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    reason: Mapped[str] = mapped_column(Text)
    authorized_review_interval_days: Mapped[int | None] = mapped_column(Integer)
    review_interval_reason: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )
