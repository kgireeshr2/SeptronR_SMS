"""
Service — Phase 11: Inventory Management
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

import app.repositories.inventory_repository as repo
from app.schemas.phase11 import (
    InventoryCategoryCreate, InventoryCategoryResponse,
    SupplierCreate, SupplierUpdate, SupplierResponse,
    StoreCreate, StoreResponse,
    ItemCreate, ItemUpdate, ItemResponse,
    PurchaseOrderCreate, PurchaseOrderUpdate, PurchaseOrderResponse,
    StockEntryCreate, StockEntryResponse,
    StockIssueCreate, StockIssueResponse,
)
from app.core.exceptions import NotFoundError


async def list_categories(db, school_id):
    return await repo.list_categories(db, school_id)


async def create_category(db, school_id, data):
    return await repo.create_category(db, school_id, data)


# Suppliers

async def list_suppliers(db, school_id):
    return await repo.list_suppliers(db, school_id)


async def get_supplier_or_404(db, school_id, supplier_id):
    s = await repo.get_supplier(db, school_id, supplier_id)
    if not s:
        raise NotFoundError("Supplier not found")
    return s


async def create_supplier(db, school_id, data):
    return await repo.create_supplier(db, school_id, data)


async def update_supplier(db, school_id, supplier_id, data):
    s = await get_supplier_or_404(db, school_id, supplier_id)
    return await repo.update_supplier(db, s, data)


# Stores

async def list_stores(db, school_id):
    return await repo.list_stores(db, school_id)


async def create_store(db, school_id, data):
    return await repo.create_store(db, school_id, data)


# Items

async def list_items(db, school_id, category_id=None, low_stock_only=False):
    items = await repo.list_items(db, school_id, category_id, low_stock_only)
    # Compute is_low_stock
    for item in items:
        item.is_low_stock = item.current_stock <= item.min_stock_level
    return items


async def get_item_or_404(db, school_id, item_id):
    item = await repo.get_item(db, school_id, item_id)
    if not item:
        raise NotFoundError("Item not found")
    return item


async def create_item(db, school_id, data):
    return await repo.create_item(db, school_id, data)


async def update_item(db, school_id, item_id, data):
    item = await get_item_or_404(db, school_id, item_id)
    return await repo.update_item(db, item, data)


# Purchase Orders

async def list_purchase_orders(db, school_id):
    return await repo.list_purchase_orders(db, school_id)


async def get_po_or_404(db, school_id, po_id):
    po = await repo.get_purchase_order(db, school_id, po_id)
    if not po:
        raise NotFoundError("Purchase order not found")
    return po


async def create_purchase_order(db, school_id, data):
    return await repo.create_purchase_order(db, school_id, data)


# Stock Entry / Issue

async def record_stock_entry(db, school_id, data):
    return await repo.create_stock_entry(db, school_id, data)


async def record_stock_issue(db, school_id, data):
    item = await get_item_or_404(db, school_id, str(data.item_id))
    if item.current_stock < data.quantity:
        raise ValueError(f"Insufficient stock. Available: {item.current_stock}")
    return await repo.create_stock_issue(db, school_id, data)


async def get_stock_history(db, school_id, item_id):
    await get_item_or_404(db, school_id, item_id)
    entries = await repo.list_stock_entries(db, item_id)
    issues = await repo.list_stock_issues(db, item_id)
    return {"entries": entries, "issues": issues}

