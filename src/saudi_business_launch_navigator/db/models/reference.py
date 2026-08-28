"""Supported activity and location reference table models."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, Text, UniqueConstraint, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from saudi_business_launch_navigator.db.base import NAVIGATOR_SCHEMA, Base
from saudi_business_launch_navigator.db.models.governance import CODE_PATTERN
from saudi_business_launch_navigator.db.statuses import LocationType, enum_sql


class BusinessActivity(Base):
    """Version-one supported business activity identity."""

    __tablename__ = "business_activities"
    __table_args__ = (
        UniqueConstraint("code", name="uq_business_activities_code"),
        CheckConstraint(f"code ~ '{CODE_PATTERN}'", name="code_format"),
        CheckConstraint("btrim(name_ar) <> ''", name="name_ar_nonblank"),
        CheckConstraint("btrim(name_en) <> ''", name="name_en_nonblank"),
        Index("ix_business_activities_is_active", "is_active"),
        {"schema": NAVIGATOR_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(Text)
    name_ar: Mapped[str] = mapped_column(Text)
    name_en: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )


class SupportedLocation(Base):
    """Product context location with no regulatory applicability relationship."""

    __tablename__ = "supported_locations"
    __table_args__ = (
        UniqueConstraint("code", name="uq_supported_locations_code"),
        CheckConstraint(f"code ~ '{CODE_PATTERN}'", name="code_format"),
        CheckConstraint(f"location_type IN ({enum_sql(LocationType)})", name="location_type"),
        CheckConstraint("country_code = 'SA'", name="saudi_country"),
        CheckConstraint("btrim(name_ar) <> ''", name="name_ar_nonblank"),
        CheckConstraint("btrim(name_en) <> ''", name="name_en_nonblank"),
        Index("ix_supported_locations_active_pilot", "is_active", "is_pilot"),
        {"schema": NAVIGATOR_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(Text)
    location_type: Mapped[str] = mapped_column(Text)
    name_ar: Mapped[str] = mapped_column(Text)
    name_en: Mapped[str] = mapped_column(Text)
    country_code: Mapped[str] = mapped_column(Text, server_default=text("'SA'"))
    is_pilot: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )
