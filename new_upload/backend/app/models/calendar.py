"""
SQLAlchemy models — Phase 16: Calendar
Table: calendar_events
⚠️ Cross-checked with Database_Schema.sql
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String, Text
from app.models.compat import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, func

from app.db.session import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class CalendarEvent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "calendar_events"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    academic_year_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # ⚠️ ENUM calendar_event_type: holiday|exam|meeting|sports|cultural|trip|other
    event_type: Mapped[str] = mapped_column(String(30), nullable=False, default="other")
    # ⚠️ start_datetime/end_datetime TIMESTAMPTZ (not start_date/end_date)
    start_datetime: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    end_datetime: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    all_day: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    location: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    # ⚠️ 'color_tag' not 'color'
    color_tag: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    # ⚠️ 'audience' not 'visibility': all|staff_only|students|parents
    audience: Mapped[str] = mapped_column(String(20), nullable=False, default="all")
    # ⚠️ audience_filter JSONB: {class_ids: [...], section_ids: [...]}
    audience_filter: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    recurrence_rule: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
