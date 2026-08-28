"""Versioned launch-journey coverage, evidence, routing, and release models."""

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
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from saudi_business_launch_navigator.db.base import NAVIGATOR_SCHEMA, Base
from saudi_business_launch_navigator.db.models.conditions import SHA256_PATTERN
from saudi_business_launch_navigator.db.models.governance import CODE_PATTERN, ROLE_PATTERN
from saudi_business_launch_navigator.db.statuses import (
    ContentReleaseStatus,
    JourneyCoverageState,
    JourneyDestinationKind,
    JourneyEvidenceRole,
    JourneyFactInputRole,
    JourneyLimitationType,
    JourneyRequirementLinkRole,
    JourneyRouteMatchKind,
    RequirementVerificationStatus,
    enum_sql,
)


class JourneyTopic(Base):
    """Immutable stable identity for one launch-journey topic."""

    __tablename__ = "journey_topics"
    __table_args__ = (
        UniqueConstraint("code", name="uq_journey_topics_code"),
        CheckConstraint(f"code ~ '{CODE_PATTERN}'", name="code_format"),
        {"schema": NAVIGATOR_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )


class JourneyTopicVersion(Base):
    """One reviewed coverage assessment for one topic/activity pair."""

    __tablename__ = "journey_topic_versions"
    __table_args__ = (
        UniqueConstraint(
            "journey_topic_id",
            "activity_id",
            "version_number",
            name="uq_journey_topic_versions_topic_activity_version",
        ),
        UniqueConstraint(
            "supersedes_journey_topic_version_id",
            name="uq_journey_topic_versions_supersedes",
        ),
        CheckConstraint("version_number > 0", name="positive_version_number"),
        CheckConstraint("btrim(title_ar) <> ''", name="title_ar_nonblank"),
        CheckConstraint(
            f"coverage_state IN ({enum_sql(JourneyCoverageState)})",
            name="coverage_state",
        ),
        CheckConstraint(
            f"limitation_type IS NULL OR limitation_type IN ({enum_sql(JourneyLimitationType)})",
            name="limitation_type",
        ),
        CheckConstraint(
            f"verification_status IN ({enum_sql(RequirementVerificationStatus)})",
            name="verification_status",
        ),
        CheckConstraint(
            "effective_until IS NULL OR effective_from IS NULL OR "
            "effective_until >= effective_from",
            name="effective_date_order",
        ),
        CheckConstraint(
            "(last_verified_at IS NULL AND review_interval_days IS NULL AND "
            "next_review_at IS NULL) OR (last_verified_at IS NOT NULL AND "
            "review_interval_days IS NOT NULL AND next_review_at IS NOT NULL AND "
            "next_review_at = last_verified_at + make_interval(days => review_interval_days))",
            name="freshness_order",
        ),
        CheckConstraint(
            "review_interval_days IS NULL OR review_interval_days BETWEEN 30 AND 180",
            name="review_interval",
        ),
        CheckConstraint(
            "verification_status <> 'approved' OR "
            "(approval_review_event_id IS NOT NULL AND last_verified_at IS NOT NULL)",
            name="approved_has_review",
        ),
        CheckConstraint(
            "NOT is_current OR verification_status = 'approved'",
            name="current_is_approved",
        ),
        CheckConstraint(
            "verification_status NOT IN ('expired', 'superseded', 'historical') OR NOT is_current",
            name="inactive_status_not_current",
        ),
        CheckConstraint(
            "supersedes_journey_topic_version_id IS DISTINCT FROM id",
            name="not_self_superseding",
        ),
        CheckConstraint(
            "(coverage_state <> 'VERIFIED' OR "
            "(verified_summary_ar IS NOT NULL AND btrim(verified_summary_ar) <> '')) AND "
            "(coverage_state <> 'PARTIALLY_VERIFIED' OR "
            "(verified_summary_ar IS NOT NULL AND btrim(verified_summary_ar) <> '' AND "
            "limitation_type IS NOT NULL AND limitation_summary_ar IS NOT NULL AND "
            "btrim(limitation_summary_ar) <> '')) AND "
            "(coverage_state <> 'REQUIRES_OFFICIAL_CONFIRMATION' OR "
            "(limitation_type IS NOT NULL AND limitation_summary_ar IS NOT NULL AND "
            "btrim(limitation_summary_ar) <> '' AND what_to_verify_ar IS NOT NULL AND "
            "btrim(what_to_verify_ar) <> '')) AND "
            "(coverage_state <> 'UNRESOLVED' OR "
            "(limitation_type IN ('insufficient_evidence', 'material_conflict', "
            "'unresolved_supersession') AND limitation_summary_ar IS NOT NULL AND "
            "btrim(limitation_summary_ar) <> ''))",
            name="state_content",
        ),
        CheckConstraint(
            "coverage_state <> 'NOT_RESEARCHED' OR "
            "(verification_status <> 'approved' AND approval_review_event_id IS NULL "
            "AND NOT is_current)",
            name="not_researched_internal_only",
        ),
        Index(
            "uq_journey_topic_versions_one_current",
            "journey_topic_id",
            "activity_id",
            unique=True,
            postgresql_where=text("is_current"),
        ),
        Index("ix_journey_topic_versions_activity_id", "activity_id"),
        Index("ix_journey_topic_versions_verification_status", "verification_status"),
        Index("ix_journey_topic_versions_next_review_at", "next_review_at"),
        Index("ix_journey_topic_versions_approval_review_event_id", "approval_review_event_id"),
        {"schema": NAVIGATOR_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    journey_topic_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.journey_topics.id",
            ondelete="RESTRICT",
            name="fk_journey_topic_versions_topic",
        ),
    )
    activity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.business_activities.id",
            ondelete="RESTRICT",
            name="fk_journey_topic_versions_activity",
        ),
    )
    version_number: Mapped[int] = mapped_column(Integer)
    title_ar: Mapped[str] = mapped_column(Text)
    title_en: Mapped[str | None] = mapped_column(Text)
    coverage_state: Mapped[str] = mapped_column(Text)
    limitation_type: Mapped[str | None] = mapped_column(Text)
    verified_summary_ar: Mapped[str | None] = mapped_column(Text)
    verified_summary_en: Mapped[str | None] = mapped_column(Text)
    limitation_summary_ar: Mapped[str | None] = mapped_column(Text)
    limitation_summary_en: Mapped[str | None] = mapped_column(Text)
    what_to_verify_ar: Mapped[str | None] = mapped_column(Text)
    what_to_verify_en: Mapped[str | None] = mapped_column(Text)
    verification_status: Mapped[str] = mapped_column(
        Text, server_default=text("'pending_source_verification'")
    )
    approval_review_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.review_events.id",
            ondelete="RESTRICT",
            name="fk_journey_topic_versions_approval_review",
            use_alter=True,
        ),
    )
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_interval_days: Mapped[int | None] = mapped_column(Integer)
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    effective_from: Mapped[date | None] = mapped_column(Date)
    effective_until: Mapped[date | None] = mapped_column(Date)
    is_current: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    supersedes_journey_topic_version_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.journey_topic_versions.id",
            ondelete="RESTRICT",
            name="fk_journey_topic_versions_supersedes",
        ),
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )


class JourneyTopicEvidence(Base):
    """Exact reviewed source-version evidence for a topic assessment."""

    __tablename__ = "journey_topic_evidence"
    __table_args__ = (
        UniqueConstraint(
            "journey_topic_version_id",
            "source_version_id",
            name="uq_journey_topic_evidence_topic_source",
        ),
        UniqueConstraint(
            "id",
            "journey_topic_version_id",
            name="uq_journey_topic_evidence_id_topic",
        ),
        CheckConstraint(
            f"evidence_role IN ({enum_sql(JourneyEvidenceRole)})",
            name="evidence_role",
        ),
        CheckConstraint(
            "evidence_role = 'historical' OR "
            "(official_excerpt_ar IS NOT NULL AND btrim(official_excerpt_ar) <> '' "
            "AND excerpt_locator IS NOT NULL AND btrim(excerpt_locator) <> '')",
            name="relied_evidence_complete",
        ),
        Index(
            "uq_journey_topic_evidence_one_primary",
            "journey_topic_version_id",
            unique=True,
            postgresql_where=text("evidence_role = 'primary'"),
        ),
        Index("ix_journey_topic_evidence_source_version_id", "source_version_id"),
        {"schema": NAVIGATOR_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    journey_topic_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.journey_topic_versions.id",
            ondelete="RESTRICT",
            name="fk_journey_topic_evidence_topic_version",
        ),
    )
    source_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.source_versions.id",
            ondelete="RESTRICT",
            name="fk_journey_topic_evidence_source_version",
        ),
    )
    evidence_role: Mapped[str] = mapped_column(Text)
    official_excerpt_ar: Mapped[str | None] = mapped_column(Text)
    official_excerpt_en: Mapped[str | None] = mapped_column(Text)
    excerpt_locator: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )


class JourneyTopicRequirementLink(Base):
    """Traceability link that never participates in requirement applicability."""

    __tablename__ = "journey_topic_requirement_links"
    __table_args__ = (
        PrimaryKeyConstraint("journey_topic_version_id", "requirement_version_id"),
        CheckConstraint(
            f"link_role IN ({enum_sql(JourneyRequirementLinkRole)})",
            name="link_role",
        ),
        Index(
            "ix_journey_topic_requirement_links_requirement_version_id",
            "requirement_version_id",
        ),
        {"schema": NAVIGATOR_SCHEMA},
    )

    journey_topic_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.journey_topic_versions.id",
            ondelete="RESTRICT",
            name="fk_journey_topic_requirement_links_topic_version",
        ),
    )
    requirement_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.requirement_versions.id",
            ondelete="RESTRICT",
            name="fk_journey_topic_requirement_links_requirement_version",
        ),
    )
    link_role: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )


class JourneyTopicFactLink(Base):
    """Navigation-only dependency kept outside the applicability graph."""

    __tablename__ = "journey_topic_fact_links"
    __table_args__ = (
        PrimaryKeyConstraint("journey_topic_version_id", "fact_definition_id"),
        CheckConstraint(
            f"input_role IN ({enum_sql(JourneyFactInputRole)})",
            name="input_role",
        ),
        Index("ix_journey_topic_fact_links_fact_definition_id", "fact_definition_id"),
        {"schema": NAVIGATOR_SCHEMA},
    )

    journey_topic_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.journey_topic_versions.id",
            ondelete="RESTRICT",
            name="fk_journey_topic_fact_links_topic_version",
        ),
    )
    fact_definition_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.fact_definitions.id",
            ondelete="RESTRICT",
            name="fk_journey_topic_fact_links_fact_definition",
        ),
    )
    input_role: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )


class JourneyTopicDestination(Base):
    """A deterministic route to an already governed official source version."""

    __tablename__ = "journey_topic_destinations"
    __table_args__ = (
        UniqueConstraint(
            "journey_topic_version_id",
            "code",
            name="uq_journey_topic_destinations_topic_code",
        ),
        UniqueConstraint(
            "journey_topic_version_id",
            "display_order",
            name="uq_journey_topic_destinations_topic_display_order",
        ),
        ForeignKeyConstraint(
            ["journey_topic_evidence_id", "journey_topic_version_id"],
            [
                f"{NAVIGATOR_SCHEMA}.journey_topic_evidence.id",
                f"{NAVIGATOR_SCHEMA}.journey_topic_evidence.journey_topic_version_id",
            ],
            ondelete="RESTRICT",
            name="fk_journey_topic_destinations_evidence_topic",
        ),
        CheckConstraint(f"code ~ '{CODE_PATTERN}'", name="code_format"),
        CheckConstraint(
            f"destination_kind IN ({enum_sql(JourneyDestinationKind)})",
            name="destination_kind",
        ),
        CheckConstraint(
            f"route_match_kind IN ({enum_sql(JourneyRouteMatchKind)})",
            name="route_match_kind",
        ),
        CheckConstraint("btrim(guidance_ar) <> ''", name="guidance_ar_nonblank"),
        CheckConstraint("btrim(what_to_verify_ar) <> ''", name="what_to_verify_ar_nonblank"),
        CheckConstraint("display_order > 0", name="positive_display_order"),
        CheckConstraint(
            "(route_match_kind = 'always' AND route_fact_definition_id IS NULL AND "
            "route_match_value IS NULL) OR "
            "(route_match_kind = 'equals' AND route_fact_definition_id IS NOT NULL AND "
            "route_match_value IS NOT NULL)",
            name="route_shape",
        ),
        Index("ix_journey_topic_destinations_route_fact_id", "route_fact_definition_id"),
        Index(
            "uq_journey_topic_destinations_primary_always",
            "journey_topic_version_id",
            unique=True,
            postgresql_where=text("is_primary AND route_match_kind = 'always'"),
        ),
        Index(
            "uq_journey_topic_destinations_primary_equals",
            "journey_topic_version_id",
            "route_fact_definition_id",
            "route_match_value",
            unique=True,
            postgresql_where=text("is_primary AND route_match_kind = 'equals'"),
        ),
        {"schema": NAVIGATOR_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(Text)
    journey_topic_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.journey_topic_versions.id",
            ondelete="RESTRICT",
            name="fk_journey_topic_destinations_topic_version",
        ),
    )
    journey_topic_evidence_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    destination_kind: Mapped[str] = mapped_column(Text)
    guidance_ar: Mapped[str] = mapped_column(Text)
    guidance_en: Mapped[str | None] = mapped_column(Text)
    what_to_verify_ar: Mapped[str] = mapped_column(Text)
    what_to_verify_en: Mapped[str | None] = mapped_column(Text)
    route_fact_definition_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.fact_definitions.id",
            ondelete="RESTRICT",
            name="fk_journey_topic_destinations_route_fact",
        ),
    )
    route_match_kind: Mapped[str] = mapped_column(Text)
    route_match_value: Mapped[object | None] = mapped_column(JSONB)
    display_order: Mapped[int] = mapped_column(Integer)
    is_primary: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )


class JourneyTopicRelease(Base):
    """Append-preserving public-display authorization for a topic version."""

    __tablename__ = "journey_topic_releases"
    __table_args__ = (
        UniqueConstraint(
            "journey_topic_version_id",
            "release_number",
            name="uq_journey_topic_releases_release_number",
        ),
        UniqueConstraint(
            "approval_review_event_id",
            name="uq_journey_topic_releases_approval_review_event",
        ),
        CheckConstraint("release_number > 0", name="positive_release_number"),
        CheckConstraint(
            f"topic_graph_sha256 ~ '{SHA256_PATTERN}'",
            name="topic_graph_sha256",
        ),
        CheckConstraint(
            f"release_status IN ({enum_sql(ContentReleaseStatus)})",
            name="release_status",
        ),
        CheckConstraint(
            "(release_status = 'released' AND withdrawn_at IS NULL AND "
            "withdrawn_by_role IS NULL AND withdrawal_reason IS NULL) OR "
            "(release_status = 'withdrawn' AND withdrawn_at IS NOT NULL AND "
            "withdrawn_at >= released_at AND withdrawn_by_role IS NOT NULL AND "
            f"withdrawn_by_role ~ '{ROLE_PATTERN}' AND withdrawal_reason IS NOT NULL "
            "AND btrim(withdrawal_reason) <> '')",
            name="withdrawal_state",
        ),
        Index(
            "uq_journey_topic_releases_one_active",
            "journey_topic_version_id",
            unique=True,
            postgresql_where=text("release_status = 'released'"),
        ),
        Index("ix_journey_topic_releases_status", "release_status"),
        {"schema": NAVIGATOR_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    journey_topic_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.journey_topic_versions.id",
            ondelete="RESTRICT",
            name="fk_journey_topic_releases_topic_version",
        ),
    )
    release_number: Mapped[int] = mapped_column(Integer)
    approval_review_event_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.review_events.id",
            ondelete="RESTRICT",
            name="fk_journey_topic_releases_approval_review",
        ),
    )
    topic_graph_sha256: Mapped[str] = mapped_column(Text)
    release_status: Mapped[str] = mapped_column(Text, server_default=text("'released'"))
    released_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    withdrawn_by_role: Mapped[str | None] = mapped_column(Text)
    withdrawal_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )


__all__ = [
    "JourneyTopic",
    "JourneyTopicDestination",
    "JourneyTopicEvidence",
    "JourneyTopicFactLink",
    "JourneyTopicRelease",
    "JourneyTopicRequirementLink",
    "JourneyTopicVersion",
]
