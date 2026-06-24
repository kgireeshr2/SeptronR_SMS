"""
SQLAlchemy models — Phase 15: Homework, Lesson Plans & PTM
Tables: homework, homework_submissions, lesson_plans, ptm_events, ptm_slots, ptm_bookings
⚠️ Cross-checked with Database_Schema.sql
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy import (
    Boolean, Date, ForeignKey, SmallInteger, String, Text, UniqueConstraint,
)
from app.models.compat import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, func

from app.db.session import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Homework(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "homework"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    academic_year_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False
    )
    class_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False, index=True
    )
    section_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sections.id"), nullable=True
    )
    subject_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False
    )
    # ⚠️ teacher_id references users table, NOT staff table
    teacher_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    # ⚠️ JSONB attachments array (not attachment_url)
    attachments: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    submissions: Mapped[list["HomeworkSubmission"]] = relationship(
        "HomeworkSubmission", back_populates="homework", lazy="noload", cascade="all, delete-orphan"
    )


class HomeworkSubmission(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "homework_submissions"
    __table_args__ = (UniqueConstraint("homework_id", "student_id", name="hw_submissions_hw_student_ux"),)

    homework_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("homework.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    student_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=False, index=True
    )
    submitted_at: Mapped[Optional[object]] = mapped_column(DateTime(timezone=True), nullable=True)
    # ⚠️ 'content' not 'submission_text'
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # ⚠️ JSONB attachments array
    attachments: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    # ⚠️ 'marks_given' not 'grade', 'remarks' not 'feedback' — no status column
    marks_given: Mapped[Optional[float]] = mapped_column(nullable=True)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    homework: Mapped["Homework"] = relationship("Homework", back_populates="submissions", lazy="noload")


class LessonPlan(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "lesson_plans"
    __table_args__ = (
        UniqueConstraint("class_id", "subject_id", "plan_date", "period_number",
                         name="lesson_plans_cls_subj_date_period_ux"),
    )

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    class_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False
    )
    section_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sections.id"), nullable=True
    )
    subject_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False
    )
    # ⚠️ teacher_id references users table
    teacher_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    academic_year_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    # ⚠️ plan_date + period_number (not week_number + topic)
    plan_date: Mapped[date] = mapped_column(Date, nullable=False)
    period_number: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    objectives: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # ⚠️ 'content' not 'methodology'
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resources: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


# ── PTM ─────────────────────────────────────────────────────────────────────

class PTMEvent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ptm_events"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    academic_year_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # ⚠️ 'ptm_date' not 'event_date'
    ptm_date: Mapped[date] = mapped_column(Date, nullable=False)
    slot_duration_minutes: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=10)
    venue: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # ⚠️ created_by references users table
    created_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    slots: Mapped[list["PTMSlot"]] = relationship(
        "PTMSlot", back_populates="ptm_event", lazy="noload", cascade="all, delete-orphan"
    )


class PTMSlot(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "ptm_slots"

    # ⚠️ 'ptm_event_id' not 'event_id'
    ptm_event_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ptm_events.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    # ⚠️ teacher_id references users table
    teacher_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    # ⚠️ slot_start/slot_end are TIMESTAMPTZ (not TIME)
    slot_start: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    slot_end: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    is_booked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    ptm_event: Mapped["PTMEvent"] = relationship("PTMEvent", back_populates="slots", lazy="noload")
    booking: Mapped[Optional["PTMBooking"]] = relationship(
        "PTMBooking", back_populates="slot", lazy="noload", uselist=False
    )


class PTMBooking(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ptm_bookings"

    slot_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ptm_slots.id", ondelete="NO ACTION"), nullable=False, unique=True
    )
    student_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=False
    )
    parent_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="confirmed")

    slot: Mapped["PTMSlot"] = relationship("PTMSlot", back_populates="booking", lazy="noload")
