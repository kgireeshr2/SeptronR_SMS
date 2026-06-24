"""
SQLAlchemy models — Phase 11: Inventory Management
Tables: inventory_categories, suppliers, stores, items, purchase_orders,
        purchase_order_items, stock_entries, stock_issues
"""
from __future__ import annotations

from datetime import date
from enum import Enum as PyEnum
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    Boolean, Date, ForeignKey, Integer, String, Text, UniqueConstraint,
)
from app.models.compat import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.school import School
    from app.models.auth import User
    from app.models.staff import Staff


class POStatus(str, PyEnum):
    draft = "draft"
    sent = "sent"
    partial_received = "partial_received"
    received = "received"
    cancelled = "cancelled"


class InventoryCategory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "inventory_categories"
    __table_args__ = (UniqueConstraint("school_id", "name", name="inv_categories_school_name_ux"),)

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Supplier(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "suppliers"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    contact_person: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    gst_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Store(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "stores"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    custodian_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("staff.id"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Item(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "items"
    __table_args__ = (UniqueConstraint("school_id", "item_code", name="items_school_sku_ux"),)

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    store_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stores.id"), nullable=True
    )
    category_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inventory_categories.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    unit: Mapped[str] = mapped_column(String(50), nullable=False, default="pieces")
    item_code: Mapped[Optional[str]] = mapped_column("item_code", String(100), nullable=True)
    min_stock_level: Mapped[int] = mapped_column("min_stock_level", Integer, nullable=False, default=0)
    current_stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unit_cost: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_consumable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    stock_entries: Mapped[list["StockEntry"]] = relationship(
        "StockEntry", back_populates="item", lazy="noload"
    )


class PurchaseOrder(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "purchase_orders"
    __table_args__ = (UniqueConstraint("school_id", "po_number", name="po_school_number_ux"),)

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    po_number: Mapped[str] = mapped_column(String(50), nullable=False)
    supplier_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False
    )
    order_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expected_delivery: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    actual_delivery: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    order_items: Mapped[list["PurchaseOrderItem"]] = relationship(
        "PurchaseOrderItem", back_populates="purchase_order", lazy="noload", cascade="all, delete-orphan"
    )


class PurchaseOrderItem(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "purchase_order_items"

    po_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="NO ACTION"), nullable=False
    )
    item_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("items.id"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    received_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_price: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder", back_populates="order_items", lazy="noload"
    )


class StockEntry(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "stock_entries"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    item_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("items.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    entry_type: Mapped[str] = mapped_column(String(20), nullable=False, default="in")
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_cost: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    entry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    store_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=True)
    po_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=True)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reference_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=True), nullable=True)
    reference_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recorded_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    item: Mapped["Item"] = relationship("Item", back_populates="stock_entries", lazy="noload")


class StockIssue(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "stock_issues"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    item_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("items.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    issued_to: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    purpose: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    issued_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    returned_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    return_deadline: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="issued")
