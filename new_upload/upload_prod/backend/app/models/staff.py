from datetime import date, datetime
from enum import Enum as PyEnum
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, SmallInteger, String, Text, CheckConstraint
from app.models.compat import UUID, JSONB, ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.auth import User
    from app.models.school import School
    from app.models.academic import AcademicYear


class EmploymentType(str, PyEnum):
    permanent = "permanent"
    contract = "contract"
    part_time = "part_time"
    probation = "probation"


class SalaryType(str, PyEnum):
    monthly = "monthly"
    hourly = "hourly"
    daily = "daily"


class LeaveStatus(str, PyEnum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    cancelled = "cancelled"


class PaymentMethod(str, PyEnum):
    cash = "cash"
    cheque = "cheque"
    online = "online"
    card = "card"
    neft = "neft"
    upi = "upi"


class Department(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "departments"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    hod_id: Mapped[Optional[str]] = mapped_column(
        "head_id", UUID(as_uuid=True), ForeignKey("staff.id"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Designation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "designations"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Staff(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "staff"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    employee_id: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    photo_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    department_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True
    )
    designation_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("designations.id"), nullable=True
    )
    date_of_joining: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    employment_type: Mapped[EmploymentType] = mapped_column(
        ENUM(EmploymentType, name="employment_type", create_type=False),
        nullable=False,
        default=EmploymentType.permanent,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    salary_type: Mapped[SalaryType] = mapped_column(
        ENUM(SalaryType, name="salary_type", create_type=False),
        nullable=False,
        default=SalaryType.monthly,
    )
    monthly_salary: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # paise
    bank_account_no: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    bank_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ifsc_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    emergency_contact: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    qualifications: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    experience_years: Mapped[Optional[float]] = mapped_column(Numeric(4, 1), nullable=True)
    # Government IDs
    aadhaar_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    pan_number: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    driving_licence: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    deleted_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # Relationships
    documents: Mapped[list["StaffDocument"]] = relationship(
        "StaffDocument", back_populates="staff", lazy="noload", cascade="all, delete-orphan"
    )
    leaves: Mapped[list["StaffLeave"]] = relationship(
        "StaffLeave", back_populates="staff", lazy="noload", cascade="all, delete-orphan"
    )
    leave_balances: Mapped[list["StaffLeaveBalance"]] = relationship(
        "StaffLeaveBalance", back_populates="staff", lazy="noload", cascade="all, delete-orphan"
    )
    payroll: Mapped[list["StaffPayroll"]] = relationship(
        "StaffPayroll", back_populates="staff", lazy="noload", cascade="all, delete-orphan"
    )


class StaffDocument(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "staff_documents"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    staff_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("staff.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    doc_type: Mapped[str] = mapped_column(String(60), nullable=False)
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)

    # Relationships
    staff: Mapped["Staff"] = relationship("Staff", back_populates="documents", lazy="noload")


class LeaveType(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "leave_types"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    max_days_per_year: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    is_paid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)


class StaffLeave(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "staff_leaves"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    staff_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("staff.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    leave_type_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leave_types.id"), nullable=False
    )
    from_date: Mapped[date] = mapped_column(Date, nullable=False)
    to_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_days: Mapped[float] = mapped_column("days_count", Numeric(4, 1), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[LeaveStatus] = mapped_column(
        ENUM(LeaveStatus, name="leave_status", create_type=False),
        nullable=False,
        default=LeaveStatus.pending,
    )
    approved_by: Mapped[Optional[str]] = mapped_column(
        "reviewed_by", UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column("reviewed_at", nullable=True)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    staff: Mapped["Staff"] = relationship("Staff", back_populates="leaves", lazy="noload")


class StaffLeaveBalance(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "staff_leave_balances"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    staff_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("staff.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    leave_type_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leave_types.id"), nullable=False
    )
    academic_year_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False
    )
    entitled_days: Mapped[float] = mapped_column(Numeric(4, 1), nullable=False, default=0)
    used_days: Mapped[float] = mapped_column(Numeric(4, 1), nullable=False, default=0)
    # Note: remaining_days is GENERATED column in DB, not mapped here

    # Relationships
    staff: Mapped["Staff"] = relationship("Staff", back_populates="leave_balances", lazy="noload")


class StaffPayroll(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "staff_payrolls"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    staff_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("staff.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    academic_year_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False
    )
    month: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    basic_salary: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # paise
    allowances: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    deductions: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    gross_salary: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    net_salary: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    payment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    payment_method: Mapped[Optional[PaymentMethod]] = mapped_column(
        ENUM(PaymentMethod, name="payment_method", create_type=False), nullable=True
    )
    is_paid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    receipt_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    staff: Mapped["Staff"] = relationship("Staff", back_populates="payroll", lazy="noload")
