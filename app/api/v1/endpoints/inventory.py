"""
API Endpoints — Phase 11: Inventory Management
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_school_id, permission_required
import app.services.inventory_service as svc
from app.schemas.phase11 import (
    InventoryCategoryCreate, InventoryCategoryResponse,
    SupplierCreate, SupplierUpdate, SupplierResponse,
    StoreCreate, StoreResponse,
    ItemCreate, ItemUpdate, ItemResponse,
    PurchaseOrderCreate, PurchaseOrderResponse,
    StockEntryCreate, StockEntryResponse,
    StockIssueCreate, StockIssueResponse,
)

categories_router = APIRouter(prefix="/inventory/categories", tags=["Inventory - Categories"])
suppliers_router = APIRouter(prefix="/inventory/suppliers", tags=["Inventory - Suppliers"])
stores_router = APIRouter(prefix="/inventory/stores", tags=["Inventory - Stores"])
items_router = APIRouter(prefix="/inventory/items", tags=["Inventory - Items"])
po_router = APIRouter(prefix="/inventory/purchase-orders", tags=["Inventory - PO"])


# ─── Categories ──────────────────────────────────────────────────────────────

@categories_router.get("", response_model=List[InventoryCategoryResponse])
async def list_categories(school_id=Depends(get_school_id), db=Depends(get_db),
                          _=Depends(permission_required("inventory", "view"))):
    return await svc.list_categories(db, school_id)


@categories_router.post("", response_model=InventoryCategoryResponse,
                        status_code=status.HTTP_201_CREATED)
async def create_category(data: InventoryCategoryCreate, school_id=Depends(get_school_id),
                          db=Depends(get_db), _=Depends(permission_required("inventory", "manage"))):
    obj = await svc.create_category(db, school_id, data)
    await db.commit()
    await db.refresh(obj)
    return obj


# ─── Suppliers ───────────────────────────────────────────────────────────────

@suppliers_router.get("", response_model=List[SupplierResponse])
async def list_suppliers(school_id=Depends(get_school_id), db=Depends(get_db),
                         _=Depends(permission_required("inventory", "view"))):
    return await svc.list_suppliers(db, school_id)


@suppliers_router.post("", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier(data: SupplierCreate, school_id=Depends(get_school_id),
                          db=Depends(get_db), _=Depends(permission_required("inventory", "manage"))):
    obj = await svc.create_supplier(db, school_id, data)
    await db.commit()
    await db.refresh(obj)
    return obj


@suppliers_router.put("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(supplier_id: UUID, data: SupplierUpdate,
                          school_id=Depends(get_school_id), db=Depends(get_db),
                          _=Depends(permission_required("inventory", "manage"))):
    obj = await svc.update_supplier(db, school_id, str(supplier_id), data)
    await db.commit()
    await db.refresh(obj)
    return obj


# ─── Stores ──────────────────────────────────────────────────────────────────

@stores_router.get("", response_model=List[StoreResponse])
async def list_stores(school_id=Depends(get_school_id), db=Depends(get_db),
                      _=Depends(permission_required("inventory", "view"))):
    return await svc.list_stores(db, school_id)


@stores_router.post("", response_model=StoreResponse, status_code=status.HTTP_201_CREATED)
async def create_store(data: StoreCreate, school_id=Depends(get_school_id),
                       db=Depends(get_db), _=Depends(permission_required("inventory", "manage"))):
    obj = await svc.create_store(db, school_id, data)
    await db.commit()
    await db.refresh(obj)
    return obj


# ─── Items ───────────────────────────────────────────────────────────────────

@items_router.get("", response_model=List[ItemResponse])
async def list_items(
    category_id: Optional[UUID] = Query(None),
    low_stock_only: bool = Query(False),
    school_id=Depends(get_school_id), db=Depends(get_db),
    _=Depends(permission_required("inventory", "view")),
):
    return await svc.list_items(db, school_id, str(category_id) if category_id else None, low_stock_only)


@items_router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(data: ItemCreate, school_id=Depends(get_school_id),
                      db=Depends(get_db), _=Depends(permission_required("inventory", "manage"))):
    obj = await svc.create_item(db, school_id, data)
    await db.commit()
    await db.refresh(obj)
    return obj


@items_router.put("/{item_id}", response_model=ItemResponse)
async def update_item(item_id: UUID, data: ItemUpdate, school_id=Depends(get_school_id),
                      db=Depends(get_db), _=Depends(permission_required("inventory", "manage"))):
    obj = await svc.update_item(db, school_id, str(item_id), data)
    await db.commit()
    await db.refresh(obj)
    return obj


@items_router.post("/{item_id}/stock-entries", response_model=StockEntryResponse,
                   status_code=status.HTTP_201_CREATED)
async def add_stock_entry(item_id: UUID, data: StockEntryCreate,
                          school_id=Depends(get_school_id), db=Depends(get_db),
                          _=Depends(permission_required("inventory", "manage"))):
    obj = await svc.record_stock_entry(db, school_id, data)
    await db.commit()
    await db.refresh(obj)
    return obj


@items_router.post("/{item_id}/stock-issues", response_model=StockIssueResponse,
                   status_code=status.HTTP_201_CREATED)
async def add_stock_issue(item_id: UUID, data: StockIssueCreate,
                          school_id=Depends(get_school_id), db=Depends(get_db),
                          _=Depends(permission_required("inventory", "manage"))):
    obj = await svc.record_stock_issue(db, school_id, data)
    await db.commit()
    await db.refresh(obj)
    return obj


@items_router.get("/{item_id}/history")
async def stock_history(item_id: UUID, school_id=Depends(get_school_id), db=Depends(get_db),
                        _=Depends(permission_required("inventory", "view"))):
    return await svc.get_stock_history(db, school_id, str(item_id))


# ─── Purchase Orders ─────────────────────────────────────────────────────────

@po_router.get("", response_model=List[PurchaseOrderResponse])
async def list_pos(school_id=Depends(get_school_id), db=Depends(get_db),
                   _=Depends(permission_required("inventory", "view"))):
    return await svc.list_purchase_orders(db, school_id)


@po_router.post("", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_po(data: PurchaseOrderCreate, school_id=Depends(get_school_id),
                    db=Depends(get_db), _=Depends(permission_required("inventory", "manage"))):
    obj = await svc.create_purchase_order(db, school_id, data)
    await db.commit()
    await db.refresh(obj)
    return obj

