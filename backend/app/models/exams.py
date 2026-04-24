"""
SQLAlchemy models for Phase 9 — Exam Management.
Tables: exam_types, exams, student_marks, grading_scales,
        report_card_templates, admit_card_configs
"""
from datetime import date, time
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    Boolean, Date, ForeignKey, Numeric, SmallInteger,
    String, Text, Time, UniqueConstraint,
)
from app.models.compat import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.school import School
    from app.models.academic import AcademicYear, AcademicTerm
    from app.models.classes import Class, Section, Subject
    from app.models.auth import User
    from app.models.students import Student


class ExamType(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Exam type catalogue: Unit Test 1, Half Yearly, Final, etc."""
    __tablename__ = "exam_types"
    __table_args__ = (UniqueConstraint("school_id", "name", name="exam_types_school_name_ux"),)

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"),
        nullable=False, index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    weightage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("100.00"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    exams: Mapped[list["Exam"]] = relationship("Exam", back_populates="exam_type", lazy="noload")


class Exam(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    One row = one subject exam for one class on one date.
    Group by exam_type_id to represent a 'batch/session'.
    """
    __tablename__ = "exams"
    __table_args__ = (
        UniqueConstraint(
            "school_id", "academic_year_id", "exam_type_id", "class_id", "subject_id",
            name="exams_school_year_type_class_subject_ux",
        ),
    )

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"),
        nullable=False, index=True,
    )
    academic_year_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False, index=True
    )
    term_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_terms.id"), nullable=True
    )
    exam_type_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exam_types.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    class_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False, index=True
    )
    subject_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False
    )
    section_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sections.id"), nullable=True
    )
    exam_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    start_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    end_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    room_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    invigilator_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    full_marks: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=100)
    pass_marks: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=35)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="scheduled"
    )  # scheduled | ongoing | completed | results_published
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # Relationships
    exam_type: Mapped["ExamType"] = relationship("ExamType", back_populates="exams", lazy="noload")
    marks: Mapped[list["StudentMark"]] = relationship(
        "StudentMark", back_populates="exam", lazy="noload", cascade="all, delete-orphan"
    )


class StudentMark(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Marks entered for one student in one exam (subject)."""
    __tablename__ = "student_marks"
    __table_args__ = (UniqueConstraint("exam_id", "student_id", name="student_marks_exam_student_ux"),)

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"),
        nullable=False, index=True,
    )
    exam_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exams.id", ondelete="NO ACTION"),
        nullable=False, index=True,
    )
    student_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=False, index=True
    )
    marks_obtained: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    is_absent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_exempted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    grade: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    entered_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    updated_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # Relationships
    exam: Mapped["Exam"] = relationship("Exam", back_populates="marks", lazy="noload")


class GradingScale(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    One row per school.
    ranges: JSONB array — [{grade, min_pct, max_pct, grade_point, description}]
    """
    __tablename__ = "grading_scales"
    __table_args__ = (UniqueConstraint("school_id", name="grading_scales_school_ux"),)

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"),
        nullable=False, unique=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, default="Default")
    ranges: Mapped[list] = mapped_column(JSONB, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ReportCardTemplate(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Template configuration for report cards."""
    __tablename__ = "report_card_templates"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"),
        nullable=False, index=True,
    )
    template_name: Mapped[str] = mapped_column(String(200), nullable=False)
    exam_type_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exam_types.id"), nullable=True
    )
    layout_config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class AdmitCardConfig(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Configuration for admit card generation."""
    __tablename__ = "admit_card_configs"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"),
        nullable=False, index=True,
    )
    template_name: Mapped[str] = mapped_column(String(200), nullable=False)
    show_photo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    show_instructions: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    header_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    footer_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
