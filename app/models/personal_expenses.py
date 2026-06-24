"""
Personal Expenses – independent student-level charges
(stationery, materials, trips, etc.)
These are completely separate from school fee accounts.
"""
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.compat import UUID, ENUM


class PersonalExpenseStatus(str, PyEnum):
    pending = "pending"
    partial = "partial"
    paid = "paid"
    waived = "waived"


class PersonalExpenseCategory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "personal_expense_categories"

    school_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")


class PersonalExpense(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "personal_expenses"

    school_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False, index=True)
    student_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("personal_expense_categories.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    paid_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, server_default='0')
    expense_date: Mapped[Optional[str]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        ENUM(PersonalExpenseStatus, name="personal_expense_status", create_type=True),
        nullable=False,
        server_default="pending",
    )
    paid_at: Mapped[Optional[str]] = mapped_column(Date, nullable=True)
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    collected_by: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
