import enum
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from app.models.compat import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class AdmissionStatus(str, enum.Enum):
    draft = "draft"
    submitted = "submitted"
    under_review = "under_review"
    approved = "approved"
    rejected = "rejected"
    waitlisted = "waitlisted"


class AdmissionFormConfig(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "admission_form_configs"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    academic_year_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    fields_config: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    required_documents: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    open_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    close_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class AdmissionForm(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "admission_forms"
    __table_args__ = (UniqueConstraint("school_id", "reference_number", name="uq_admission_ref_per_school"),)

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    academic_year_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    reference_number: Mapped[str] = mapped_column(String(60), nullable=False)
    applicant_name: Mapped[str] = mapped_column(String(200), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    applying_for_class_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=True), nullable=True)
    parent_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    parent_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    parent_email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    previous_school: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    documents: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    extra_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # extra IDs captured at intake
    status: Mapped[AdmissionStatus] = mapped_column(
        Enum(AdmissionStatus, name="admission_status"), nullable=False, default=AdmissionStatus.draft
    )
    assigned_admission_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="NO ACTION"), nullable=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    school = relationship("School", lazy="noload")
