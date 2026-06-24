"""
SQLAlchemy models — Phase 21: Super Admin Panel
Tables: subscription_plans, school_subscriptions, school_feature_flags, impersonation_logs
⚠️ Cross-checked with Database_Schema.sql + Phase 21 prompt
"""
from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional
import uuid

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text, UniqueConstraint
from app.models.compat import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, func

from app.db.session import Base
from app.models.base import UUIDPrimaryKeyMixin


class SubscriptionPlan(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "subscription_plans"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    max_students: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_staff: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    enabled_modules: Mapped[List[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )
    price_monthly_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SchoolSubscription(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "school_subscriptions"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False
    )
    plan_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=False
    )
    starts_at: Mapped[date] = mapped_column(Date, nullable=False)
    ends_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SchoolFeatureFlag(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "school_feature_flags"
    __table_args__ = (
        UniqueConstraint("school_id", "feature_key", name="school_feature_flags_school_key_ux"),
    )

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False
    )
    feature_key: Mapped[str] = mapped_column(String(100), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ImpersonationLog(Base):
    __tablename__ = "impersonation_logs"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    super_admin_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    impersonated_school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    impersonated_user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    started_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ended_at: Mapped[Optional[object]] = mapped_column(DateTime(timezone=True), nullable=True)
