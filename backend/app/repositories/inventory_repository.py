"""
Repository — Phase 11: Inventory Management
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import (
    InventoryCategory, Supplier, Store, Item,
    PurchaseOrder, PurchaseOrderItem, StockEntry, StockIssue,
)
from app.schemas.phase11 import (
    InventoryCategoryCreate, SupplierCreate, SupplierUpdate,
    StoreCreate, ItemCreate, ItemUpdate,
    PurchaseOrderCreate, PurchaseOrderUpdate,
    StockEntryCreate, StockIssueCreate,
)
import uuid
import datetime


# ─── Category ────────────────────────────────────────────────────────────────

async def list_categories(db: AsyncSession, school_id: str) -> List[InventoryCategory]:
    r = await db.execute(select(InventoryCategory).where(InventoryCategory.school_id == school_id))
    return list(r.scalars().all())


async def create_category(db: AsyncSession, school_id: str, data: InventoryCategoryCreate) -> InventoryCategory:
    obj = InventoryCategory(school_id=school_id, **data.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


# ─── Supplier ────────────────────────────────────────────────────────────────

async def list_suppliers(db: AsyncSession, school_id: str) -> List[Supplier]:
    r = await db.execute(select(Supplier).where(Supplier.school_id == school_id).order_by(Supplier.name))
    return list(r.scalars().all())


async def get_supplier(db: AsyncSession, school_id: str, supplier_id: str) -> Optional[Supplier]:
    r = await db.execute(select(Supplier).where(Supplier.id == supplier_id, Supplier.school_id == school_id))
    return r.scalar_one_or_none()


async def create_supplier(db: AsyncSession, school_id: str, data: SupplierCreate) -> Supplier:
    obj = Supplier(school_id=school_id, **data.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def update_supplier(db: AsyncSession, supplier: Supplier, data: SupplierUpdate) -> Supplier:
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(supplier, k, v)
    await db.flush()
    await db.refresh(supplier)
    return supplier


# ─── Store ───────────────────────────────────────────────────────────────────

async def list_stores(db: AsyncSession, school_id: str) -> List[Store]:
    r = await db.execute(select(Store).where(Store.school_id == school_id))
    return list(r.scalars().all())


async def create_store(db: AsyncSession, school_id: str, data: StoreCreate) -> Store:
    obj = Store(school_id=school_id, **data.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


# ─── Item ────────────────────────────────────────────────────────────────────

async def list_items(
    db: AsyncSession, school_id: str,
    category_id: Optional[str] = None,
    low_stock_only: bool = False
) -> List[Item]:
    q = select(Item).where(Item.school_id == school_id, Item.is_active == True)
    if category_id:
        q = q.where(Item.category_id == category_id)
    if low_stock_only:
        q = q.where(Item.current_stock <= Item.min_stock_level)
    r = await db.execute(q.order_by(Item.name))
    return list(r.scalars().all())


async def get_item(db: AsyncSession, school_id: str, item_id: str) -> Optional[Item]:
    r = await db.execute(select(Item).where(Item.id == item_id, Item.school_id == school_id))
    return r.scalar_one_or_none()


async def create_item(db: AsyncSession, school_id: str, data: ItemCreate) -> Item:
    obj = Item(school_id=school_id, **data.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def update_item(db: AsyncSession, item: Item, data: ItemUpdate) -> Item:
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(item, k, v)
    await db.flush()
    await db.refresh(item)
    return item


# ─── Purchase Order ──────────────────────────────────────────────────────────

async def _next_po_number(db: AsyncSession, school_id: str) -> str:
    r = await db.execute(
        select(func.count()).where(PurchaseOrder.school_id == school_id)
    )
    count = r.scalar_one() or 0
    return f"PO-{datetime.date.today().year}-{count + 1:04d}"


async def list_purchase_orders(db: AsyncSession, school_id: str) -> List[PurchaseOrder]:
    r = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.school_id == school_id)
        .order_by(PurchaseOrder.order_date.desc())
    )
    return list(r.scalars().all())


async def get_purchase_order(
    db: AsyncSession, school_id: str, po_id: str
) -> Optional[PurchaseOrder]:
    r = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.id == po_id, PurchaseOrder.school_id == school_id)
    )
    return r.scalar_one_or_none()


async def create_purchase_order(
    db: AsyncSession, school_id: str, data: PurchaseOrderCreate
) -> PurchaseOrder:
    po_number = await _next_po_number(db, school_id)
    items_data = data.items
    total = sum(i.quantity * i.unit_cost for i in items_data)
    po = PurchaseOrder(
        school_id=school_id,
        po_number=po_number,
        supplier_id=str(data.supplier_id),
        order_date=data.order_date,
        expected_delivery_date=data.expected_delivery_date,
        notes=data.notes,
        total_amount=total,
        status="draft",
    )
    db.add(po)
    await db.flush()
    for item in items_data:
        poi = PurchaseOrderItem(
            po_id=str(po.id),
            item_id=str(item.item_id),
            quantity=item.quantity,
            unit_cost=item.unit_cost,
        )
        db.add(poi)
    await db.flush()
    await db.refresh(po)
    return po


# ─── Stock Entry ─────────────────────────────────────────────────────────────

async def create_stock_entry(
    db: AsyncSession, school_id: str, data: StockEntryCreate
) -> StockEntry:
    entry = StockEntry(school_id=school_id, **data.model_dump())
    db.add(entry)
    # Update item stock
    await db.execute(
        update(Item)
        .where(Item.id == str(data.item_id))
        .values(current_stock=Item.current_stock + data.quantity)
    )
    await db.flush()
    await db.refresh(entry)
    return entry


async def list_stock_entries(db: AsyncSession, item_id: str) -> List[StockEntry]:
    r = await db.execute(
        select(StockEntry).where(StockEntry.item_id == item_id)
        .order_by(StockEntry.entry_date.desc())
    )
    return list(r.scalars().all())


# ─── Stock Issue ─────────────────────────────────────────────────────────────

async def create_stock_issue(
    db: AsyncSession, school_id: str, data: StockIssueCreate
) -> StockIssue:
    issue = StockIssue(school_id=school_id, **data.model_dump())
    db.add(issue)
    # Reduce item stock
    await db.execute(
        update(Item)
        .where(Item.id == str(data.item_id))
        .values(current_stock=Item.current_stock - data.quantity)
    )
    await db.flush()
    await db.refresh(issue)
    return issue


async def list_stock_issues(db: AsyncSession, item_id: str) -> List[StockIssue]:
    r = await db.execute(
        select(StockIssue).where(StockIssue.item_id == item_id)
        .order_by(StockIssue.issue_date.desc())
    )
    return list(r.scalars().all())

