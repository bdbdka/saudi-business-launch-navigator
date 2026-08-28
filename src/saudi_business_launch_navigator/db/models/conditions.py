"""Governed fact definitions and version-level deterministic conditions."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
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
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from saudi_business_launch_navigator.db.base import NAVIGATOR_SCHEMA, Base
from saudi_business_launch_navigator.db.models.governance import CODE_PATTERN
from saudi_business_launch_navigator.db.statuses import (
    ConditionVerificationStatus,
    FactDataType,
    FactPrivacyClass,
    enum_sql,
)

SHA256_PATTERN = r"^[0-9a-f]{64}$"


class FactDefinition(Base):
    """One evidence-bound version of a privacy-minimizing business fact."""

    __tablename__ = "fact_definitions"
    __table_args__ = (
        UniqueConstraint("code", "version_number", name="uq_fact_definitions_code_version"),
        UniqueConstraint(
            "supersedes_fact_definition_id",
            name="uq_fact_definitions_supersedes_fact_definition",
        ),
        CheckConstraint(f"code ~ '{CODE_PATTERN}'", name="code_format"),
        CheckConstraint("version_number > 0", name="positive_version_number"),
        CheckConstraint(f"data_type IN ({enum_sql(FactDataType)})", name="data_type"),
        CheckConstraint(
            f"privacy_class IN ({enum_sql(FactPrivacyClass)})",
            name="privacy_class",
        ),
        CheckConstraint(
            f"verification_status IN ({enum_sql(ConditionVerificationStatus)})",
            name="verification_status",
        ),
        CheckConstraint("btrim(meaning_ar) <> ''", name="meaning_ar_nonblank"),
        CheckConstraint(
            "(data_type = 'enum' AND jsonb_typeof(allowed_values) = 'array' "
            "AND jsonb_array_length(allowed_values) > 0) OR "
            "(data_type <> 'enum' AND allowed_values IS NULL)",
            name="enum_values_match_type",
        ),
        CheckConstraint(
            "verification_status <> 'approved' OR "
            "(approval_review_event_id IS NOT NULL AND official_excerpt_ar IS NOT NULL "
            "AND btrim(official_excerpt_ar) <> '' AND evidence_locator IS NOT NULL "
            "AND btrim(evidence_locator) <> '')",
            name="approved_has_governance_evidence",
        ),
        CheckConstraint(
            "supersedes_fact_definition_id IS DISTINCT FROM id",
            name="not_self_superseding",
        ),
        Index(
            "uq_fact_definitions_one_current",
            "code",
            unique=True,
            postgresql_where=text("is_current"),
        ),
        Index("ix_fact_definitions_source_version_id", "source_version_id"),
        Index("ix_fact_definitions_approval_review_event_id", "approval_review_event_id"),
        Index("ix_fact_definitions_verification_status", "verification_status"),
        {"schema": NAVIGATOR_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(Text)
    version_number: Mapped[int] = mapped_column(Integer)
    meaning_ar: Mapped[str] = mapped_column(Text)
    explanation_en: Mapped[str | None] = mapped_column(Text)
    data_type: Mapped[str] = mapped_column(Text)
    allowed_values: Mapped[list[str] | None] = mapped_column(JSONB)
    unit: Mapped[str | None] = mapped_column(Text)
    privacy_class: Mapped[str] = mapped_column(Text, server_default=text("'non_personal_business'"))
    validation_metadata: Mapped[dict[str, object]] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb")
    )
    source_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.source_versions.id",
            ondelete="RESTRICT",
            name="fk_fact_definitions_source_version",
        ),
    )
    official_excerpt_ar: Mapped[str] = mapped_column(Text)
    evidence_locator: Mapped[str] = mapped_column(Text)
    verification_status: Mapped[str] = mapped_column(
        Text, server_default=text("'pending_source_verification'")
    )
    approval_review_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.review_events.id",
            ondelete="RESTRICT",
            name="fk_fact_definitions_approval_review",
        ),
    )
    is_current: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    supersedes_fact_definition_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.fact_definitions.id",
            ondelete="RESTRICT",
            name="fk_fact_definitions_supersedes",
        ),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )


class RequirementConditionSet(Base):
    """Immutable canonical DSL expression for one requirement version."""

    __tablename__ = "requirement_condition_sets"
    __table_args__ = (
        UniqueConstraint(
            "requirement_version_id",
            name="uq_requirement_condition_sets_requirement_version",
        ),
        CheckConstraint("dsl_schema_version = 1", name="dsl_schema_version"),
        CheckConstraint("jsonb_typeof(expression) = 'object'", name="expression_object"),
        CheckConstraint(f"expression_sha256 ~ '{SHA256_PATTERN}'", name="expression_sha256"),
        CheckConstraint(
            f"verification_status IN ({enum_sql(ConditionVerificationStatus)})",
            name="verification_status",
        ),
        CheckConstraint(
            "verification_status <> 'approved' OR approval_review_event_id IS NOT NULL",
            name="approved_has_review",
        ),
        Index("ix_requirement_condition_sets_verification_status", "verification_status"),
        Index("ix_requirement_condition_sets_approval_review_event_id", "approval_review_event_id"),
        {"schema": NAVIGATOR_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    requirement_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.requirement_versions.id",
            ondelete="RESTRICT",
            name="fk_requirement_condition_sets_requirement_version",
        ),
    )
    dsl_schema_version: Mapped[int] = mapped_column(Integer, server_default=text("1"))
    expression: Mapped[dict[str, object]] = mapped_column(JSONB)
    expression_sha256: Mapped[str] = mapped_column(Text)
    verification_status: Mapped[str] = mapped_column(
        Text, server_default=text("'pending_source_verification'")
    )
    approval_review_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.review_events.id",
            ondelete="RESTRICT",
            name="fk_requirement_condition_sets_approval_review",
        ),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )


class RequirementConditionFact(Base):
    """Explicit governed fact dependency of a condition set."""

    __tablename__ = "requirement_condition_facts"
    __table_args__ = (
        PrimaryKeyConstraint("condition_set_id", "fact_definition_id"),
        Index("ix_requirement_condition_facts_fact_definition_id", "fact_definition_id"),
        {"schema": NAVIGATOR_SCHEMA},
    )

    condition_set_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.requirement_condition_sets.id",
            ondelete="RESTRICT",
            name="fk_requirement_condition_facts_condition_set",
        ),
    )
    fact_definition_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{NAVIGATOR_SCHEMA}.fact_definitions.id",
            ondelete="RESTRICT",
            name="fk_requirement_condition_facts_fact_definition",
        ),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )
