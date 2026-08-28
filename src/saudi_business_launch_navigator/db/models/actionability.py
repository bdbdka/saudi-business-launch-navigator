"""Versioned requirement actionability claims and display releases."""

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
    ActionabilityDetailType,
    ActionabilityValueState,
    ContentReleaseStatus,
    RequirementVerificationStatus,
    enum_sql,
)


class RequirementActionabilityVersion(Base):
    """One atomic, reviewed operational detail for a requirement version."""

    __tablename__ = "requirement_actionability_versions"
    __table_args__ = (
        UniqueConstraint(
            "code",
            "version_number",
            name="uq_requirement_actionability_versions_code_version",
        ),
        UniqueConstraint(
            "supersedes_actionability_version_id",
            name="uq_requirement_actionability_versions_supersedes",
        ),
        CheckConstraint(f"code ~ '{CODE_PATTERN}'", name="code_format"),
        CheckConstraint("version_number > 0", name="positive_version_number"),
        CheckConstraint(
            f"detail_type IN ({enum_sql(ActionabilityDetailType)})",
            name="detail_type",
        ),
        CheckConstraint(
            f"value_state IN ({enum_sql(ActionabilityValueState)})",
            name="value_state",
        ),
        CheckConstraint("value_schema_version = 1", name="value_schema_version"),
        CheckConstraint(
            "(value_payload IS NULL AND value_sha256 IS NULL) OR "
            "(value_payload IS NOT NULL AND value_sha256 IS NOT NULL)",
            name="payload_hash_pair",
        ),
        CheckConstraint(
            f"value_sha256 IS NULL OR value_sha256 ~ '{SHA256_PATTERN}'",
            name="value_sha256",
        ),
        CheckConstraint(
            "(value_state = 'VERIFIED' AND value_payload IS NOT NULL "
            "AND jsonb_typeof(value_payload) = 'object' AND value_sha256 IS NOT NULL) OR "
            "(value_state = 'NOT_APPLICABLE' AND value_payload IS NULL "
            "AND value_sha256 IS NULL)",
            name="value_state_shape",
        ),
        CheckConstraint(
            "value_state <> 'VERIFIED' OR ("
            "(detail_type IN ('prerequisite', 'document', 'sequence', 'validity') "
            "AND value_payload ->> 'kind' = 'text' "
            "AND jsonb_typeof(value_payload -> 'text_ar') = 'string' "
            "AND btrim(value_payload ->> 'text_ar') <> '' "
            "AND (value_payload - ARRAY['kind', 'text_ar', 'text_en']::text[]) = '{}'::jsonb "
            "AND (NOT value_payload ? 'text_en' OR ("
            "jsonb_typeof(value_payload -> 'text_en') = 'string' "
            "AND btrim(value_payload ->> 'text_en') <> ''))) OR "
            "(detail_type = 'official_start' "
            "AND value_payload ->> 'kind' = 'official_destination' "
            "AND jsonb_typeof(value_payload -> 'label_ar') = 'string' "
            "AND btrim(value_payload ->> 'label_ar') <> '' "
            "AND (value_payload - ARRAY['kind', 'label_ar', 'label_en']::text[]) = '{}'::jsonb "
            "AND (NOT value_payload ? 'label_en' OR ("
            "jsonb_typeof(value_payload -> 'label_en') = 'string' "
            "AND btrim(value_payload ->> 'label_en') <> ''))) OR "
            "(detail_type = 'fee' AND value_payload ->> 'kind' IN ('money', 'fee_calculator')) OR "
            "(detail_type IN ('processing_time', 'validity') "
            "AND value_payload ->> 'kind' = 'duration'))",
            name="verified_payload_kind",
        ),
        CheckConstraint(
            "value_state <> 'VERIFIED' OR detail_type <> 'fee' "
            "OR (value_payload ->> 'kind' = 'money' "
            "AND jsonb_typeof(value_payload -> 'amount_minor') = 'number' "
            "AND (value_payload ->> 'amount_minor') ~ '^(0|[1-9][0-9]*)$' "
            "AND value_payload ->> 'currency' = 'SAR' "
            "AND jsonb_typeof(value_payload -> 'label_ar') = 'string' "
            "AND btrim(value_payload ->> 'label_ar') <> '' "
            "AND (value_payload - ARRAY["
            "'kind', 'amount_minor', 'currency', 'label_ar', 'label_en']::text[]) = '{}'::jsonb "
            "AND (NOT value_payload ? 'label_en' OR ("
            "jsonb_typeof(value_payload -> 'label_en') = 'string' "
            "AND btrim(value_payload ->> 'label_en') <> ''))) "
            "OR (value_payload ->> 'kind' = 'fee_calculator' "
            "AND jsonb_typeof(value_payload -> 'label_ar') = 'string' "
            "AND btrim(value_payload ->> 'label_ar') <> '' "
            "AND (value_payload - ARRAY['kind', 'label_ar', 'label_en']::text[]) = '{}'::jsonb "
            "AND (NOT value_payload ? 'label_en' OR ("
            "jsonb_typeof(value_payload -> 'label_en') = 'string' "
            "AND btrim(value_payload ->> 'label_en') <> ''))))",
            name="money_payload_shape",
        ),
        CheckConstraint(
            "value_state <> 'VERIFIED' OR detail_type NOT IN ('processing_time', 'validity') "
            "OR value_payload ->> 'kind' <> 'duration' OR "
            "(value_payload ->> 'unit' IN ('minute', 'hour', 'day', 'week', 'month', 'year') "
            "AND jsonb_typeof(value_payload -> 'label_ar') = 'string' "
            "AND btrim(value_payload ->> 'label_ar') <> '' "
            "AND (value_payload - ARRAY['kind', 'value', 'minimum', 'maximum', "
            "'unit', 'label_ar', 'label_en']::text[]) = '{}'::jsonb "
            "AND (NOT value_payload ? 'label_en' OR ("
            "jsonb_typeof(value_payload -> 'label_en') = 'string' "
            "AND btrim(value_payload ->> 'label_en') <> '')) "
            "AND (NOT value_payload ? 'value' OR ("
            "jsonb_typeof(value_payload -> 'value') = 'number' "
            "AND (value_payload ->> 'value') ~ '^(0|[1-9][0-9]*)$')) "
            "AND (NOT value_payload ? 'minimum' OR ("
            "jsonb_typeof(value_payload -> 'minimum') = 'number' "
            "AND (value_payload ->> 'minimum') ~ '^(0|[1-9][0-9]*)$')) "
            "AND (NOT value_payload ? 'maximum' OR ("
            "jsonb_typeof(value_payload -> 'maximum') = 'number' "
            "AND (value_payload ->> 'maximum') ~ '^(0|[1-9][0-9]*)$')) "
            "AND ((value_payload ? 'value' AND NOT value_payload ? 'minimum' "
            "AND NOT value_payload ? 'maximum') OR (NOT value_payload ? 'value' "
            "AND value_payload ? 'minimum')) "
            "AND (NOT value_payload ? 'maximum' OR (value_payload ->> 'maximum')::numeric "
            ">= (value_payload ->> 'minimum')::numeric))",
            name="duration_payload_shape",
        ),
        CheckConstraint("btrim(official_excerpt_ar) <> ''", name="official_excerpt_ar_nonbl"),
        CheckConstraint("btrim(excerpt_locator) <> ''", name="excerpt_locator_nonblank"),
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
            name="inactive_status_not_curre",
        ),
        CheckConstraint(
            "supersedes_actionability_version_id IS DISTINCT FROM id",
            name="not_self_superseding",
        ),
        CheckConstraint("display_order > 0", name="positive_display_order"),
        Index(
            "uq_requirement_actionability_versions_one_current",
            "code",
            unique=True,
            postgresql_where=text("is_current"),
        ),
        Index(
            "ix_requirement_actionability_versions_requirement_version_id",
            "requirement_version_id",
        ),
        Index(
            "ix_requirement_actionability_versions_primary_source_version_id",
            "primary_source_version_id",
        ),
        Index(
            "ix_requirement_actionability_versions_approval_review_event_id",
            "approval_review_event_id",
        ),
        Index(
            "ix_requirement_actionability_versions_verification_status",
            "verification_status",
        ),
        Index("ix_requirement_actionability_versions_next_review_at", "next_review_at"),
        {"schema": NAVIGATOR_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(Text)
    version_number: Mapped[int] = mapped_column(Integer)
    requirement_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.requirement_versions.id",
            ondelete="RESTRICT",
            name="fk_requirement_actionability_versions_requirement_version",
        ),
    )
    detail_type: Mapped[str] = mapped_column(Text)
    value_state: Mapped[str] = mapped_column(Text)
    value_schema_version: Mapped[int] = mapped_column(Integer, server_default=text("1"))
    value_payload: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    value_sha256: Mapped[str | None] = mapped_column(Text)
    primary_source_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.source_versions.id",
            ondelete="RESTRICT",
            name="fk_requirement_actionability_versions_primary_source_version",
        ),
    )
    official_excerpt_ar: Mapped[str] = mapped_column(Text)
    official_excerpt_en: Mapped[str | None] = mapped_column(Text)
    excerpt_locator: Mapped[str] = mapped_column(Text)
    verification_status: Mapped[str] = mapped_column(
        Text, server_default=text("'pending_source_verification'")
    )
    approval_review_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.review_events.id",
            ondelete="RESTRICT",
            name="fk_requirement_actionability_versions_approval_review",
            use_alter=True,
        ),
    )
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_interval_days: Mapped[int | None] = mapped_column(Integer)
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    effective_from: Mapped[date | None] = mapped_column(Date)
    effective_until: Mapped[date | None] = mapped_column(Date)
    display_order: Mapped[int] = mapped_column(Integer)
    is_current: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    supersedes_actionability_version_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.requirement_actionability_versions.id",
            ondelete="RESTRICT",
            name="fk_requirement_actionability_versions_supersedes",
        ),
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )


class RequirementActionabilityRelease(Base):
    """Append-preserving display authorization for an actionability version."""

    __tablename__ = "requirement_actionability_releases"
    __table_args__ = (
        UniqueConstraint(
            "requirement_actionability_version_id",
            "release_number",
            name="uq_requirement_actionability_releases_release_number",
        ),
        UniqueConstraint(
            "approval_review_event_id",
            name="uq_requirement_actionability_releases_approval_review_event",
        ),
        CheckConstraint("release_number > 0", name="positive_release_number"),
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
            "uq_requirement_actionability_releases_one_active",
            "requirement_actionability_version_id",
            unique=True,
            postgresql_where=text("release_status = 'released'"),
        ),
        Index("ix_requirement_actionability_releases_status", "release_status"),
        {"schema": NAVIGATOR_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    requirement_actionability_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.requirement_actionability_versions.id",
            ondelete="RESTRICT",
            name="fk_requirement_actionability_releases_actionability_version",
        ),
    )
    release_number: Mapped[int] = mapped_column(Integer)
    approval_review_event_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.review_events.id",
            ondelete="RESTRICT",
            name="fk_requirement_actionability_releases_approval_review",
        ),
    )
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
    "RequirementActionabilityRelease",
    "RequirementActionabilityVersion",
]
