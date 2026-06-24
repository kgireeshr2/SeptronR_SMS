from datetime import date, datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import Boolean, Date, ForeignKey, SmallInteger, Text, UniqueConstraint
from app.models.compat import UUID, ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class SessionType(str, PyEnum):
    morning = "morning"
    afternoon = "afternoon"
    full_day = "full_day"


class StudentAttendanceStatus(str, PyEnum):
    present = "present"
    absent = "absent"
    late = "late"
    half_day = "half_day"
    leave = "leave"
    holiday = "holiday"


class HolidayType(str, PyEnum):
    national = "national"
    state = "state"
    school = "school"
    religious = "religious"
    other = "other"


class AttendanceSource(str, PyEnum):
    manual = "manual"
    biometric = "biometric"
    qr = "qr"


class StaffAttendanceStatus(str, PyEnum):
    present = "present"
    absent = "absent"
    late = "late"
    half_day = "half_day"
    on_leave = "on_leave"
    holiday = "holiday"


class Holiday(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "holidays"
    __table_args__ = (UniqueConstraint("school_id", "date", name="holidays_school_id_date_key"),)

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    academic_year_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    holiday_type: Mapped[HolidayType] = mapped_column(
        "type", ENUM(HolidayType, name="holiday_type", create_type=False), nullable=False, default=HolidayType.school
    )
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)


class AttendanceSession(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "attendance_sessions"
    __table_args__ = (
        UniqueConstraint("section_id", "date", "session_type", name="attendance_sessions_section_id_date_session_type_key"),
    )

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    session_type: Mapped[SessionType] = mapped_column(
        ENUM(SessionType, name="session_type", create_type=False), nullable=False, default=SessionType.full_day
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    class_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False, index=True
    )
    section_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sections.id"), nullable=False, index=True
    )
    taken_by: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    is_finalized: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)

    entries: Mapped[list["StudentAttendance"]] = relationship(
        "StudentAttendance", back_populates="session", lazy="noload", cascade="all, delete-orphan"
    )


class StudentAttendance(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "student_attendance"
    __table_args__ = (UniqueConstraint("session_id", "student_id", name="student_attendance_session_id_student_id_key"),)

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    session_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("attendance_sessions.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    student_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    status: Mapped[StudentAttendanceStatus] = mapped_column(
        ENUM(StudentAttendanceStatus, name="student_attendance_status", create_type=False),
        nullable=False,
        default=StudentAttendanceStatus.present,
    )
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notified_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    session: Mapped["AttendanceSession"] = relationship("AttendanceSession", back_populates="entries", lazy="noload")


class StaffAttendance(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "staff_attendance"
    __table_args__ = (UniqueConstraint("staff_id", "date", name="staff_attendance_staff_id_date_key"),)

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    staff_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("staff.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    check_in: Mapped[Optional[datetime]] = mapped_column("check_in_time", nullable=True)
    check_out: Mapped[Optional[datetime]] = mapped_column("check_out_time", nullable=True)
    status: Mapped[StaffAttendanceStatus] = mapped_column(
        ENUM(StaffAttendanceStatus, name="staff_attendance_status", create_type=False),
        nullable=False,
        default=StaffAttendanceStatus.present,
    )
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[AttendanceSource] = mapped_column(
        ENUM(AttendanceSource, name="attendance_source", create_type=False),
        nullable=False,
        default=AttendanceSource.manual,
    )
