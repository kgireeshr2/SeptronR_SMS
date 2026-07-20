"""
SQLAlchemy models — Vendor Inventory
Tables (school-scoped vendor system):
  vendors, vendor_products, vendor_stock,
  vendor_invoices, vendor_invoice_items,
  vendor_sales, vendor_sale_items,
  vendor_payments
"""
from __future__ import annotations

from enum import Enum as PyEnum
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import (
    BigInteger, Boolean, Date, DateTime, ForeignKey,
    Integer, String, Text, UniqueConstraint, Numeric,
)
from app.models.compat import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.school import School
    from app.models.auth import User
    from app.models.students import Student


class VendorInvoiceStatus(str, PyEnum):
    unpaid = "unpaid"
    partial = "partial"
    paid = "paid"
    cancelled = "cancelled"


class PaymentDirection(str, PyEnum):
    to_vendor = "to_vendor"       # school pays vendor
    from_vendor = "from_vendor"   # vendor refunds school


class Vendor(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Third-party vendor — scoped to a school."""
    __tablename__ = "vendors"

    school_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    contact_person: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    gst_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    bank_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    bank_account: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    bank_ifsc: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    # Optional link to a system user with role=vendor
    user_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    products: Mapped[List["VendorProduct"]] = relationship(back_populates="vendor", lazy="noload")


class VendorProduct(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Product catalog for a vendor. Prices in paise (integer)."""
    __tablename__ = "vendor_products"

    vendor_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    sku: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    unit: Mapped[str] = mapped_column(String(50), nullable=False, default="pcs")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Prices stored as integer paise/cents
    purchase_price: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    selling_price: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    vendor: Mapped["Vendor"] = relationship(back_populates="products", lazy="noload")


class VendorStock(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Per-school stock levels for a vendor product."""
    __tablename__ = "vendor_stock"
    __table_args__ = (
        UniqueConstraint("vendor_id", "school_id", "product_id", name="vs_vendor_school_product_ux"),
    )

    vendor_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vendor_products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    qty_available: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    qty_reserved: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class VendorInvoice(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Goods-in invoice from vendor to school (vendor supplies products)."""
    __tablename__ = "vendor_invoices"

    vendor_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vendors.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    invoice_number: Mapped[str] = mapped_column(String(100), nullable=False)
    invoice_date: Mapped[str] = mapped_column(Date, nullable=False)
    # Amount due to vendor for this invoice (paise)
    total_amount: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    paid_amount: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=VendorInvoiceStatus.unpaid)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    items: Mapped[List["VendorInvoiceItem"]] = relationship(back_populates="invoice", lazy="noload")


class VendorInvoiceItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Line items for a vendor invoice — each item increases stock."""
    __tablename__ = "vendor_invoice_items"

    invoice_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vendor_invoices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vendor_products.id", ondelete="RESTRICT"), nullable=False
    )
    qty: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[int] = mapped_column(BigInteger, nullable=False)  # paise
    total: Mapped[int] = mapped_column(BigInteger, nullable=False)        # paise

    invoice: Mapped["VendorInvoice"] = relationship(back_populates="items", lazy="noload")


class VendorSale(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Sale of vendor product(s) to a student."""
    __tablename__ = "vendor_sales"

    vendor_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vendors.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    student_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="SET NULL"), nullable=True, index=True
    )
    sale_date: Mapped[str] = mapped_column(Date, nullable=False)
    total_amount: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)  # paise
    payment_mode: Mapped[str] = mapped_column(String(50), nullable=False, default="cash")
    # user who processed the sale
    received_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    items: Mapped[List["VendorSaleItem"]] = relationship(back_populates="sale", lazy="noload")


class VendorSaleItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Line items for a vendor sale — each item decreases stock."""
    __tablename__ = "vendor_sale_items"

    sale_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vendor_sales.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vendor_products.id", ondelete="RESTRICT"), nullable=False
    )
    qty: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[int] = mapped_column(BigInteger, nullable=False)  # paise (selling price at time of sale)
    total: Mapped[int] = mapped_column(BigInteger, nullable=False)        # paise

    sale: Mapped["VendorSale"] = relationship(back_populates="items", lazy="noload")


class VendorPayment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Money transfers between school and vendor."""
    __tablename__ = "vendor_payments"

    vendor_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vendors.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    payment_date: Mapped[str] = mapped_column(Date, nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)  # paise
    direction: Mapped[str] = mapped_column(String(20), nullable=False, default=PaymentDirection.to_vendor)
    payment_mode: Mapped[str] = mapped_column(String(50), nullable=False, default="bank_transfer")
    reference: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recorded_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
