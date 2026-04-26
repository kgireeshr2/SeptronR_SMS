from datetime import date, datetime
from enum import Enum as PyEnum
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, Index, String, Text, text
from app.models.compat import UUID, ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.auth import User
    from app.models.classes import Class, Section
    from app.models.academic import AcademicYear
    from app.models.school import School


class ParentRelation(str, PyEnum):
    father = "father"
    mother = "mother"
    guardian = "guardian"
    sibling = "sibling"
    other = "other"


class Student(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "students"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    admission_number: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    user_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True  # unique enforced via filtered index
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    blood_group: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    religion: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    nationality: Mapped[str] = mapped_column(String(60), nullable=False, default="Indian")
    photo_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    admission_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # Government IDs
    aadhaar_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    pan_number: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    apaar_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)  # APAAR / PEN
    # Contact & Address
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    pincode: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    # Additional Info
    caste: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    mother_tongue: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    previous_school: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    # Emergency Contact
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    emergency_contact_relation: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    deleted_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # Relationships
    parents: Mapped[list["StudentParent"]] = relationship(
        "StudentParent", back_populates="student", lazy="noload", cascade="all, delete-orphan"
    )
    enrollments: Mapped[list["StudentEnrollment"]] = relationship(
        "StudentEnrollment", back_populates="student", lazy="noload", cascade="all, delete-orphan"
    )
    documents: Mapped[list["StudentDocument"]] = relationship(
        "StudentDocument", back_populates="student", lazy="noload", cascade="all, delete-orphan"
    )

    __table_args__ = (
        # Filtered unique index on user_id — allows multiple NULLs (MSSQL unique constraint limitation)
        Index("ix_students_user_id_unique", "user_id", unique=True, mssql_where=text("user_id IS NOT NULL")),
    )


class StudentEnrollment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "student_enrollments"
    __table_args__ = ({"schema": None},)

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    student_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    academic_year_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False, index=True
    )
    class_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False
    )
    section_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sections.id"), nullable=True
    )
    roll_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="enrollments", lazy="noload")


class StudentParent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "student_parents"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    student_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    relation: Mapped[ParentRelation] = mapped_column(
        ENUM(ParentRelation, name="parent_relation", create_type=False),
        nullable=False,
        default=ParentRelation.father,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    occupation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_primary_contact: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    can_access_portal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # Government IDs
    aadhaar_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    pan_number: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    ration_card_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="parents", lazy="noload")


class StudentDocument(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "student_documents"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    student_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    doc_type: Mapped[str] = mapped_column(String(60), nullable=False)
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)

    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="documents", lazy="noload")


class StudentPromotion(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "student_promotions"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    student_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    from_class_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False
    )
    to_class_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False
    )
    from_year_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False
    )
    to_year_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False
    )
    promoted_by: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    promoted_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)


class StudentTransfer(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "student_transfers"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    student_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    transfer_certificate_no: Mapped[str] = mapped_column(String(50), nullable=False)
    leaving_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    issued_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    issued_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
