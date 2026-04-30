"""
SQLAlchemy models — Phase 12: Accounting (Income & Expense)
Tables: income_categories, expense_categories, income_records, expense_records, budget_heads
"""
from __future__ import annotations

from datetime import date
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    BigInteger, Boolean, Date, ForeignKey, Integer, String, Text, UniqueConstraint,
)
from app.models.compat import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.school import School
    from app.models.auth import User
    from app.models.academic import AcademicYear


class IncomeCategory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "income_categories"
    __table_args__ = (UniqueConstraint("school_id", "name", name="income_categories_school_name_ux"),)

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ExpenseCategory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "expense_categories"
    __table_args__ = (UniqueConstraint("school_id", "name", name="expense_categories_school_name_ux"),)

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    budget_amount: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class IncomeRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "income_records"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    academic_year_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=True, index=True
    )
    category_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("income_categories.id"), nullable=False
    )
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    income_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_mode: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    transaction_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    reference_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    received_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    is_fee_income: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    fee_payment_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fee_payments.id"), nullable=True
    )
    created_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )


class ExpenseRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "expense_records"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    academic_year_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=True, index=True
    )
    category_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("expense_categories.id"), nullable=False
    )
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_mode: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    vendor_name: Mapped[Optional[str]] = mapped_column("vendor_name", String(200), nullable=True)
    invoice_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    invoice_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reference_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="approved")
    created_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )


class BudgetHead(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "budget_heads"
    __table_args__ = (
        UniqueConstraint("school_id", "academic_year_id", "category_id", name="budget_heads_school_year_cat_ux"),
    )

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    academic_year_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False
    )
    category_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("expense_categories.id"), nullable=False
    )
    allocated_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    spent_amount: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
