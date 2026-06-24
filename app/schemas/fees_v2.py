"""Pydantic schemas for the Advanced Fee Management (v2) feature."""
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.staff import PaymentMethod


# ─── Fee Type ───────────────────────────────────────────────

class FeeTypeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: bool = True


class FeeTypeUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class FeeTypeResponse(BaseModel):
    id: UUID
    school_id: UUID
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ─── Fee Group ───────────────────────────────────────────────

class FeeGroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None
    fee_type_ids: list[str] = Field(default_factory=list)
    is_active: bool = True


class FeeGroupUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = None
    fee_type_ids: Optional[list[str]] = None
    is_active: Optional[bool] = None


class FeeGroupResponse(BaseModel):
    id: UUID
    school_id: UUID
    name: str
    description: Optional[str] = None
    is_active: bool
    fee_types: list[FeeTypeResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ─── Fee Master ─────────────────────────────────────────────

class FeeMasterItemCreate(BaseModel):
    fee_type_id: str
    amount: int = Field(ge=0)


class FeeMasterCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    class_id: str
    academic_year_id: str
    fee_group_id: str
    items: list[FeeMasterItemCreate] = Field(default_factory=list)
    is_active: bool = True


class FeeMasterUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    is_active: Optional[bool] = None
    items: Optional[list[FeeMasterItemCreate]] = None


class FeeMasterItemResponse(BaseModel):
    id: UUID
    fee_type_id: UUID
    fee_type_name: Optional[str] = None
    amount: int
    model_config = ConfigDict(from_attributes=True)


class FeeMasterResponse(BaseModel):
    id: UUID
    school_id: UUID
    name: str
    class_id: UUID
    class_name: Optional[str] = None
    academic_year_id: UUID
    academic_year_name: Optional[str] = None
    fee_group_id: UUID
    fee_group_name: Optional[str] = None
    is_active: bool
    items: list[FeeMasterItemResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ─── Student Fee Assignment ──────────────────────────────────

class StudentFeeMasterAssignRequest(BaseModel):
    student_ids: list[str]
    fee_master_id: str
    academic_year_id: str


class StudentFeeMasterAssignResponse(BaseModel):
    id: UUID
    school_id: UUID
    student_id: UUID
    student_name: Optional[str] = None
    fee_master_id: UUID
    fee_master_name: Optional[str] = None
    academic_year_id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ─── Fee Ledger (per student summary) ────────────────────────

class FeeTypeLedgerEntry(BaseModel):
    fee_type_id: str
    fee_type_name: str
    amount_due: int
    amount_paid: int
    discount_given: int
    balance: int


class StudentFeeLedger(BaseModel):
    student_id: str
    student_name: str
    class_name: Optional[str] = None
    section_name: Optional[str] = None
    fee_master_id: str
    fee_master_name: str
    total_due: int
    total_paid: int
    total_discount: int
    total_balance: int
    entries: list[FeeTypeLedgerEntry] = Field(default_factory=list)


# ─── Fee Collection ──────────────────────────────────────────

class FeeCollectionItemCreate(BaseModel):
    fee_type_id: str
    amount_paid: int = Field(ge=0)
    discount_amount: int = Field(default=0, ge=0)
    discount_reason: Optional[str] = None


class FeeCollectionCreate(BaseModel):
    student_id: str
    fee_master_id: str
    academic_year_id: str
    payment_date: date
    payment_method: PaymentMethod
    transaction_ref: Optional[str] = None
    remarks: Optional[str] = None
    items: list[FeeCollectionItemCreate]


class FeeCollectionItemResponse(BaseModel):
    id: UUID
    fee_type_id: UUID
    fee_type_name: Optional[str] = None
    amount_paid: int
    discount_amount: int
    discount_reason: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class FeeCollectionResponse(BaseModel):
    id: UUID
    school_id: UUID
    student_id: UUID
    student_name: Optional[str] = None
    class_name: Optional[str] = None
    section_name: Optional[str] = None
    fee_master_id: UUID
    fee_master_name: Optional[str] = None
    academic_year_id: UUID
    receipt_number: str
    payment_date: date
    total_amount: int
    total_discount: int
    payment_method: PaymentMethod
    transaction_ref: Optional[str] = None
    collected_by: UUID
    collected_by_name: Optional[str] = None
    remarks: Optional[str] = None
    is_reversed: bool
    reversal_reason: Optional[str] = None
    reversed_at: Optional[datetime] = None
    items: list[FeeCollectionItemResponse] = Field(default_factory=list)
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ReverseCollectionRequest(BaseModel):
    reason: str = Field(min_length=3)
