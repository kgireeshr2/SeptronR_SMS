"""
Pydantic v2 schemas — Phase 11: Inventory Management
"""
from __future__ import annotations

from datetime import date
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class InventoryCategoryCreate(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None


class InventoryCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    name: str
    description: Optional[str]
    is_active: bool


class SupplierCreate(BaseModel):
    name: str = Field(..., max_length=200)
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None


class SupplierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    name: str
    contact_person: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    address: Optional[str]
    is_active: bool


class StoreCreate(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    location: Optional[str] = None


class StoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    name: str
    description: Optional[str]
    location: Optional[str]
    is_active: bool


class ItemCreate(BaseModel):
    name: str = Field(..., max_length=200)
    item_code: Optional[str] = None
    category_id: Optional[UUID] = None
    store_id: Optional[UUID] = None
    unit: str = Field("pcs", max_length=50)
    description: Optional[str] = None
    min_stock_level: int = 0
    current_stock: int = 0
    unit_cost: int = 0


class ItemUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[UUID] = None
    store_id: Optional[UUID] = None
    unit: Optional[str] = None
    description: Optional[str] = None
    min_stock_level: Optional[int] = None
    unit_cost: Optional[int] = None
    is_active: Optional[bool] = None


class ItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    name: str
    item_code: Optional[str]
    category_id: Optional[UUID]
    store_id: Optional[UUID]
    unit: str
    description: Optional[str]
    min_stock_level: int
    current_stock: int
    unit_cost: int
    is_active: bool
    is_low_stock: bool = False


class PurchaseOrderItemCreate(BaseModel):
    item_id: UUID
    quantity: int = Field(..., ge=1)
    unit_cost: int = Field(0, ge=0)


class PurchaseOrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    item_id: UUID
    quantity: int
    received_quantity: int
    unit_cost: int


class PurchaseOrderCreate(BaseModel):
    supplier_id: UUID
    order_date: date
    expected_delivery_date: Optional[date] = None
    notes: Optional[str] = None
    items: List[PurchaseOrderItemCreate] = []


class PurchaseOrderUpdate(BaseModel):
    expected_delivery_date: Optional[date] = None
    notes: Optional[str] = None


class PurchaseOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    supplier_id: UUID
    po_number: str
    status: str
    order_date: date
    expected_delivery_date: Optional[date]
    total_amount: int
    notes: Optional[str]
    items: List[PurchaseOrderItemResponse] = []


class StockEntryCreate(BaseModel):
    item_id: UUID
    store_id: Optional[UUID] = None
    po_id: Optional[UUID] = None
    quantity: int = Field(..., ge=1)
    unit_cost: int = Field(0, ge=0)
    entry_date: date
    notes: Optional[str] = None


class StockEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    item_id: UUID
    quantity: int
    unit_cost: int
    entry_date: date
    notes: Optional[str]


class StockIssueCreate(BaseModel):
    item_id: UUID
    issued_to: Optional[str] = None
    issued_to_dept: Optional[str] = None
    quantity: int = Field(..., ge=1)
    issue_date: date
    purpose: Optional[str] = None
    notes: Optional[str] = None


class StockIssueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    item_id: UUID
    issued_to: Optional[str]
    issued_to_dept: Optional[str]
    quantity: int
    issue_date: date
    purpose: Optional[str]
    notes: Optional[str]
