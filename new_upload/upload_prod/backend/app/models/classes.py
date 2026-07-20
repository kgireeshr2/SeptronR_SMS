from datetime import time
from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, SmallInteger, String, Time, UniqueConstraint
from app.models.compat import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Class(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "classes"
    __table_args__ = (UniqueConstraint("school_id", "academic_year_id", "name", name="uq_class_per_school_year"),)

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    academic_year_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    numeric_level: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True, default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    sections: Mapped[list["Section"]] = relationship(
        "Section", back_populates="class_", lazy="noload", cascade="all, delete-orphan"
    )
    class_subjects: Mapped[list["ClassSubject"]] = relationship(
        "ClassSubject", back_populates="class_", lazy="noload", cascade="all, delete-orphan"
    )


class Section(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "sections"
    __table_args__ = (UniqueConstraint("class_id", "name", name="uq_section_name_per_class"),)

    school_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=True, index=True
    )
    class_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    capacity: Mapped[int] = mapped_column("max_students", SmallInteger, nullable=False, default=40)
    class_teacher_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="NO ACTION"), nullable=True, index=True
    )
    room_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    class_: Mapped["Class"] = relationship("Class", back_populates="sections", lazy="noload")
    timetable_entries: Mapped[list["Timetable"]] = relationship(
        "Timetable", back_populates="section", lazy="noload", cascade="all, delete-orphan"
    )


class Subject(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "subjects"
    __table_args__ = (UniqueConstraint("school_id", "code", name="uq_subject_code_per_school"),)

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_elective: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    full_marks: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=100)
    pass_marks: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=35)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ClassSubject(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "class_subjects"
    __table_args__ = (UniqueConstraint("class_id", "subject_id", name="uq_class_subject"),)

    class_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    subject_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    teacher_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="NO ACTION"), nullable=True
    )

    class_: Mapped["Class"] = relationship("Class", back_populates="class_subjects", lazy="noload")
    subject: Mapped["Subject"] = relationship("Subject", lazy="noload")


class Timetable(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "timetables"
    __table_args__ = (
        CheckConstraint("end_time > start_time", name="chk_timetable_end_after_start"),
        UniqueConstraint(
            "section_id",
            "academic_year_id",
            "day_of_week",
            "period_number",
            name="uq_timetable_slot",
        ),
    )

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    section_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sections.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    subject_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="NO ACTION"), nullable=False
    )
    teacher_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="NO ACTION"), nullable=True, index=True
    )
    academic_year_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    day_of_week: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    period_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)

    section: Mapped["Section"] = relationship("Section", back_populates="timetable_entries", lazy="noload")
    subject: Mapped["Subject"] = relationship("Subject", lazy="noload")
