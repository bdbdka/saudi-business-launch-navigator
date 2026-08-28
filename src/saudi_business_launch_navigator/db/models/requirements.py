"""Canonical requirement, versioned evidence, and publication table models."""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
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
from saudi_business_launch_navigator.db.models.governance import CODE_PATTERN, ROLE_PATTERN
from saudi_business_launch_navigator.db.statuses import (
    PublicationStatus,
    RelationshipStatus,
    RequirementScope,
    RequirementVerificationStatus,
    SourceRole,
    enum_sql,
)


class Requirement(Base):
    """Immutable canonical identity for one unique requirement."""

    __tablename__ = "requirements"
    __table_args__ = (
        UniqueConstraint("code", name="uq_requirements_code"),
        CheckConstraint(f"code ~ '{CODE_PATTERN}'", name="code_format"),
        {"schema": NAVIGATOR_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )


class RequirementVersion(Base):
    """Versioned regulatory meaning, scope, authority, and effective state."""

    __tablename__ = "requirement_versions"
    __table_args__ = (
        UniqueConstraint(
            "requirement_id",
            "version_number",
            name="uq_requirement_versions_requirement_version",
        ),
        UniqueConstraint(
            "supersedes_requirement_version_id",
            name="uq_requirement_versions_supersedes_requirement_version",
        ),
        CheckConstraint("version_number > 0", name="positive_version_number"),
        CheckConstraint(f"scope_type IN ({enum_sql(RequirementScope)})", name="scope_type"),
        CheckConstraint("btrim(canonical_title_ar) <> ''", name="title_ar_nonblank"),
        CheckConstraint("btrim(canonical_description_ar) <> ''", name="description_ar_nonblank"),
        CheckConstraint(
            "effective_until IS NULL OR effective_from IS NULL OR "
            "effective_until >= effective_from",
            name="effective_date_order",
        ),
        CheckConstraint(
            f"verification_status IN ({enum_sql(RequirementVerificationStatus)})",
            name="verification_status",
        ),
        CheckConstraint(
            "verification_status NOT IN ('expired', 'superseded', 'historical') OR NOT is_current",
            name="inactive_status_not_current",
        ),
        CheckConstraint(
            "supersedes_requirement_version_id IS DISTINCT FROM id",
            name="not_self_superseding",
        ),
        Index(
            "uq_requirement_versions_one_current",
            "requirement_id",
            unique=True,
            postgresql_where=text("is_current"),
        ),
        Index("ix_requirement_versions_responsible_entity_id", "responsible_entity_id"),
        Index("ix_requirement_versions_verification_status", "verification_status"),
        Index("ix_requirement_versions_effective_until", "effective_until"),
        {"schema": NAVIGATOR_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    requirement_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.requirements.id",
            ondelete="RESTRICT",
            name="fk_requirement_versions_requirement",
        ),
    )
    version_number: Mapped[int] = mapped_column(Integer)
    scope_type: Mapped[str] = mapped_column(Text)
    responsible_entity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.government_entities.id",
            ondelete="RESTRICT",
            name="fk_requirement_versions_responsible_entity",
        ),
    )
    canonical_title_ar: Mapped[str] = mapped_column(Text)
    canonical_description_ar: Mapped[str] = mapped_column(Text)
    canonical_title_en: Mapped[str | None] = mapped_column(Text)
    canonical_description_en: Mapped[str | None] = mapped_column(Text)
    simplified_explanation_ar: Mapped[str | None] = mapped_column(Text)
    simplified_explanation_en: Mapped[str | None] = mapped_column(Text)
    effective_from: Mapped[date | None] = mapped_column(Date)
    effective_until: Mapped[date | None] = mapped_column(Date)
    verification_status: Mapped[str] = mapped_column(
        Text, server_default=text("'pending_source_verification'")
    )
    is_current: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    supersedes_requirement_version_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.requirement_versions.id",
            ondelete="RESTRICT",
            name="fk_requirement_versions_supersedes",
        ),
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )


class RequirementActivity(Base):
    """Version-level many-to-many requirement/activity applicability."""

    __tablename__ = "requirement_activities"
    __table_args__ = (
        PrimaryKeyConstraint("requirement_version_id", "activity_id"),
        Index("ix_requirement_activities_activity_id", "activity_id"),
        {"schema": NAVIGATOR_SCHEMA},
    )

    requirement_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.requirement_versions.id",
            ondelete="RESTRICT",
            name="fk_requirement_activities_requirement_version",
        ),
    )
    activity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.business_activities.id",
            ondelete="RESTRICT",
            name="fk_requirement_activities_activity",
        ),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )


class RequirementSource(Base):
    """One exact source-version evidence bundle for a requirement version."""

    __tablename__ = "requirement_sources"
    __table_args__ = (
        UniqueConstraint(
            "requirement_version_id",
            "source_version_id",
            name="uq_requirement_sources_requirement_source",
        ),
        CheckConstraint(f"source_role IN ({enum_sql(SourceRole)})", name="source_role"),
        CheckConstraint(
            f"relationship_status IN ({enum_sql(RelationshipStatus)})",
            name="relationship_status",
        ),
        CheckConstraint(
            "relationship_status <> 'active' OR source_role = 'historical' OR "
            "(official_excerpt_ar IS NOT NULL AND "
            "btrim(official_excerpt_ar) <> '' AND excerpt_locator IS NOT NULL AND "
            "btrim(excerpt_locator) <> '')",
            name="relied_evidence_complete",
        ),
        CheckConstraint(
            "relationship_status <> 'active' OR role_review_event_id IS NOT NULL",
            name="active_has_review",
        ),
        CheckConstraint(
            "(relationship_status = 'resolved' AND resolved_at IS NOT NULL) OR "
            "(relationship_status <> 'resolved' AND resolved_at IS NULL)",
            name="resolution_timestamp",
        ),
        Index(
            "uq_requirement_sources_one_active_primary",
            "requirement_version_id",
            unique=True,
            postgresql_where=text("source_role = 'primary' AND relationship_status = 'active'"),
        ),
        Index("ix_requirement_sources_source_version_id", "source_version_id"),
        Index("ix_requirement_sources_role_review_event_id", "role_review_event_id"),
        Index(
            "ix_requirement_sources_requirement_status",
            "requirement_version_id",
            "relationship_status",
        ),
        {"schema": NAVIGATOR_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    requirement_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.requirement_versions.id",
            ondelete="RESTRICT",
            name="fk_requirement_sources_requirement_version",
        ),
    )
    source_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.source_versions.id",
            ondelete="RESTRICT",
            name="fk_requirement_sources_source_version",
        ),
    )
    source_role: Mapped[str] = mapped_column(Text)
    official_excerpt_ar: Mapped[str | None] = mapped_column(Text)
    official_excerpt_en: Mapped[str | None] = mapped_column(Text)
    excerpt_locator: Mapped[str | None] = mapped_column(Text)
    relationship_status: Mapped[str] = mapped_column(Text, server_default=text("'pending_review'"))
    role_review_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.review_events.id",
            ondelete="RESTRICT",
            name="fk_requirement_sources_role_review",
        ),
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )


class RequirementPublication(Base):
    """Append-preserving numbered publication cycle."""

    __tablename__ = "requirement_publications"
    __table_args__ = (
        UniqueConstraint(
            "requirement_version_id",
            "publication_number",
            name="uq_requirement_publications_publication_number",
        ),
        UniqueConstraint(
            "approval_review_event_id",
            name="uq_requirement_publications_approval_review_event",
        ),
        CheckConstraint("publication_number > 0", name="positive_publication_number"),
        CheckConstraint(
            f"publication_status IN ({enum_sql(PublicationStatus)})",
            name="publication_status",
        ),
        CheckConstraint(
            "(publication_status = 'published' AND withdrawn_at IS NULL AND "
            "withdrawn_by_role IS NULL AND withdrawal_reason IS NULL) OR "
            "(publication_status = 'withdrawn' AND withdrawn_at IS NOT NULL AND "
            "withdrawn_at >= published_at AND "
            "withdrawn_by_role IS NOT NULL AND "
            f"withdrawn_by_role ~ '{ROLE_PATTERN}' AND withdrawal_reason IS NOT NULL "
            "AND btrim(withdrawal_reason) <> '')",
            name="withdrawal_state",
        ),
        Index(
            "uq_requirement_publications_one_active",
            "requirement_version_id",
            unique=True,
            postgresql_where=text("publication_status = 'published'"),
        ),
        Index(
            "ix_requirement_publications_primary_source",
            "primary_requirement_source_id",
        ),
        Index("ix_requirement_publications_status", "publication_status"),
        {"schema": NAVIGATOR_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    requirement_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.requirement_versions.id",
            ondelete="RESTRICT",
            name="fk_requirement_publications_requirement_version",
        ),
    )
    publication_number: Mapped[int] = mapped_column(Integer)
    primary_requirement_source_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.requirement_sources.id",
            ondelete="RESTRICT",
            name="fk_requirement_publications_primary_source",
        ),
    )
    approval_review_event_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.review_events.id",
            ondelete="RESTRICT",
            name="fk_requirement_publications_approval_review",
        ),
    )
    publication_status: Mapped[str] = mapped_column(Text, server_default=text("'published'"))
    published_at: Mapped[datetime] = mapped_column(
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


class RequirementPublicationSource(Base):
    """Immutable evidence and role snapshot for one publication cycle."""

    __tablename__ = "requirement_publication_sources"
    __table_args__ = (
        PrimaryKeyConstraint("publication_id", "requirement_source_id"),
        CheckConstraint(
            f"source_role_at_publication IN ({enum_sql(SourceRole)})",
            name="source_role",
        ),
        CheckConstraint(
            "source_role_at_publication = 'historical' OR "
            "(official_excerpt_ar_at_publication IS NOT NULL AND "
            "btrim(official_excerpt_ar_at_publication) <> '' AND "
            "excerpt_locator_at_publication IS NOT NULL AND "
            "btrim(excerpt_locator_at_publication) <> '')",
            name="relied_evidence_complete",
        ),
        Index(
            "uq_publication_sources_one_primary",
            "publication_id",
            unique=True,
            postgresql_where=text("source_role_at_publication = 'primary'"),
        ),
        Index(
            "ix_requirement_publication_sources_requirement_source_id",
            "requirement_source_id",
        ),
        {"schema": NAVIGATOR_SCHEMA},
    )

    publication_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.requirement_publications.id",
            ondelete="RESTRICT",
            name="fk_publication_sources_publication",
        ),
    )
    requirement_source_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.requirement_sources.id",
            ondelete="RESTRICT",
            name="fk_publication_sources_requirement_source",
        ),
    )
    source_role_at_publication: Mapped[str] = mapped_column(Text)
    official_excerpt_ar_at_publication: Mapped[str | None] = mapped_column(Text)
    official_excerpt_en_at_publication: Mapped[str | None] = mapped_column(Text)
    excerpt_locator_at_publication: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )
