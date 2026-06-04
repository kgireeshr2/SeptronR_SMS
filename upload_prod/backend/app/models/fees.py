from datetime import date, datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import Boolean, Computed, Date, DateTime, ForeignKey, Integer, Numeric, SmallInteger, String, Text, UniqueConstraint
from app.models.compat import UUID, ENUM
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.staff import PaymentMethod


class FeeFrequency(str, PyEnum):
    monthly = "monthly"
    quarterly = "quarterly"
    annual = "annual"
    one_time = "one_time"
    semi_annual = "semi_annual"


class DiscountType(str, PyEnum):
    percentage = "percentage"
    fixed = "fixed"


class DiscountNature(str, PyEnum):
    merit = "merit"
    sibling = "sibling"
    scholarship = "scholarship"
    staff_child = "staff_child"
    armed_forces = "armed_forces"
    ews = "ews"
    early_payment = "early_payment"
    financial_aid = "financial_aid"
    loyalty = "loyalty"
    custom = "custom"


class DiscountApplicableTo(str, PyEnum):
    student = "student"
    category = "category"
    class_ = "class"


class InvoiceStatus(str, PyEnum):
    unpaid = "unpaid"
    partial = "partial"
    paid = "paid"
    overdue = "overdue"
    waived = "waived"
    cancelled = "cancelled"


class FineCalcType(str, PyEnum):
    fixed = "fixed"
    percentage_per_day = "percentage_per_day"


class FeeCategory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "fee_categories"
    __table_args__ = (UniqueConstraint("school_id", "name", name="fee_categories_school_id_name_key"),)

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class FeeStructure(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "fee_structures"
    __table_args__ = (
        UniqueConstraint(
            "school_id",
            "academic_year_id",
            "class_id",
            "fee_category_id",
            name="uq_fee_structures_school_year_class_cat",
        ),
    )

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    academic_year_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False, index=True
    )
    class_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False, index=True)
    fee_category_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fee_categories.id"), nullable=False, index=True
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    frequency: Mapped[FeeFrequency] = mapped_column(
        ENUM(FeeFrequency, name="fee_frequency", create_type=False),
        nullable=False,
        default=FeeFrequency.monthly,
    )
    due_day: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class FeeDiscount(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "fee_discounts"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[DiscountType] = mapped_column(
        ENUM(DiscountType, name="discount_type", create_type=False), nullable=False, default=DiscountType.percentage
    )
    value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    applicable_to: Mapped[DiscountApplicableTo] = mapped_column(
        ENUM(DiscountApplicableTo, name="discount_applicable_to", create_type=False),
        nullable=False,
        default=DiscountApplicableTo.student,
    )
    nature: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class StudentFeeAssignment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "student_fee_assignments"
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "fee_structure_id",
            "academic_year_id",
            name="uq_fee_assignments_student_structure_year",
        ),
    )

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    student_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    fee_structure_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fee_structures.id"), nullable=False, index=True
    )
    discount_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fee_discounts.id"), nullable=True
    )
    custom_amount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    academic_year_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False, index=True
    )


class FeeInvoice(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "fee_invoices"
    __table_args__ = (UniqueConstraint("school_id", "invoice_number", name="fee_invoices_school_id_invoice_number_key"),)

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    student_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    academic_year_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False, index=True
    )
    invoice_number: Mapped[str] = mapped_column(String(50), nullable=False)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[InvoiceStatus] = mapped_column(
        ENUM(InvoiceStatus, name="invoice_status", create_type=False), nullable=False, default=InvoiceStatus.unpaid
    )
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    paid_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    balance_amount: Mapped[int] = mapped_column(Integer, Computed('total_amount - paid_amount', persisted=True), nullable=False)


class FeeInvoiceItem(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "fee_invoice_items"

    invoice_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fee_invoices.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    fee_category_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fee_categories.id"), nullable=False, index=True
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    discount_amt: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fine_applied: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class FeePayment(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "fee_payments"
    __table_args__ = (UniqueConstraint("school_id", "receipt_number", name="fee_payments_school_id_receipt_number_key"),)

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    invoice_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fee_invoices.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_method: Mapped[PaymentMethod] = mapped_column(
        ENUM(PaymentMethod, name="payment_method", create_type=False), nullable=False
    )
    transaction_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    receipt_number: Mapped[str] = mapped_column(String(50), nullable=False)
    collected_by: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_reversed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reversal_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)


class StudentDiscountAssignment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "student_discount_assignments"
    __table_args__ = (
        UniqueConstraint(
            "school_id", "student_id", "discount_id", "academic_year_id",
            name="uq_student_discount_year",
        ),
    )

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    student_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    discount_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fee_discounts.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    academic_year_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False, index=True
    )
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class FineConfiguration(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "fine_configurations"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[FineCalcType] = mapped_column(
        ENUM(FineCalcType, name="fine_calc_type", create_type=False), nullable=False, default=FineCalcType.fixed
    )
    value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    applicable_after_days: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


# ============================================================
#  Advanced Fee Management (v2) Models
# ============================================================

class FeeType(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Named fee head: School Fee, Bus Fee, Library Fee, etc."""
    __tablename__ = "v2_fee_types"
    __table_args__ = (UniqueConstraint("school_id", "name", name="uq_v2_fee_type_school_name"),)

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class FeeGroup(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Bundle of one or more FeeTypes, e.g. 'Day Scholars' = School + Bus."""
    __tablename__ = "v2_fee_groups"
    __table_args__ = (UniqueConstraint("school_id", "name", name="uq_v2_fee_group_school_name"),)

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class FeeGroupItem(Base, UUIDPrimaryKeyMixin):
    """Junction: which FeeTypes belong to a FeeGroup."""
    __tablename__ = "v2_fee_group_items"
    __table_args__ = (UniqueConstraint("fee_group_id", "fee_type_id", name="uq_v2_fee_group_item"),)

    fee_group_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("v2_fee_groups.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fee_type_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("v2_fee_types.id", ondelete="CASCADE"), nullable=False, index=True
    )


class FeeMaster(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Class-level fee master: ties a FeeGroup + per-type amounts to a class/year."""
    __tablename__ = "v2_fee_masters"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    class_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    academic_year_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    fee_group_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("v2_fee_groups.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class FeeMasterItem(Base, UUIDPrimaryKeyMixin):
    """Per-type amount inside a FeeMaster."""
    __tablename__ = "v2_fee_master_items"
    __table_args__ = (UniqueConstraint("fee_master_id", "fee_type_id", name="uq_v2_fee_master_item"),)

    fee_master_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("v2_fee_masters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fee_type_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("v2_fee_types.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class StudentFeeMasterAssignment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Assigns a specific FeeMaster to a student for an academic year."""
    __tablename__ = "v2_student_fee_assignments"
    __table_args__ = (
        UniqueConstraint("student_id", "fee_master_id", "academic_year_id", name="uq_v2_student_fee_master"),
    )

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    student_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    fee_master_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("v2_fee_masters.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    academic_year_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    assigned_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="NO ACTION"), nullable=True
    )


class FeeCollection(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """One payment receipt / collection session for a student."""
    __tablename__ = "v2_fee_collections"
    __table_args__ = (UniqueConstraint("school_id", "receipt_number", name="uq_v2_collection_receipt"),)

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    student_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    fee_master_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("v2_fee_masters.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    academic_year_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    receipt_number: Mapped[str] = mapped_column(String(60), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_discount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    payment_method: Mapped[PaymentMethod] = mapped_column(
        ENUM(PaymentMethod, name="payment_method", create_type=False), nullable=False
    )
    transaction_ref: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    collected_by: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="NO ACTION"), nullable=False
    )
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_reversed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reversal_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reversed_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="NO ACTION"), nullable=True
    )
    reversed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)


class FeeCollectionItem(Base, UUIDPrimaryKeyMixin):
    """Per-fee-type breakdown inside a FeeCollection receipt."""
    __tablename__ = "v2_fee_collection_items"

    collection_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("v2_fee_collections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fee_type_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("v2_fee_types.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    amount_paid: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    discount_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    discount_reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
