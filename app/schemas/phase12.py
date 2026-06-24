"""
Pydantic v2 schemas — Phase 12: Accounting
"""
from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class IncomeCategoryCreate(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None


class IncomeCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    name: str
    description: Optional[str]
    is_active: bool


class ExpenseCategoryCreate(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    budget_amount: int = 0


class ExpenseCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    budget_amount: Optional[int] = None
    is_active: Optional[bool] = None


class ExpenseCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    name: str
    description: Optional[str]
    budget_amount: int
    is_active: bool


class IncomeRecordCreate(BaseModel):
    category_id: UUID
    amount: int = Field(..., ge=1)
    income_date: date
    description: Optional[str] = None
    reference_number: Optional[str] = None
    received_by: Optional[str] = None


class IncomeRecordUpdate(BaseModel):
    amount: Optional[int] = None
    income_date: Optional[date] = None
    description: Optional[str] = None
    reference_number: Optional[str] = None


class IncomeRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    category_id: UUID
    amount: int
    income_date: date
    description: Optional[str]
    reference_number: Optional[str]
    received_by: Optional[str]


class ExpenseRecordCreate(BaseModel):
    category_id: UUID
    amount: int = Field(..., ge=1)
    expense_date: date
    description: Optional[str] = None
    vendor_name: Optional[str] = None
    payment_mode: str = "cash"
    reference_number: Optional[str] = None
    approved_by: Optional[str] = None


class ExpenseRecordUpdate(BaseModel):
    amount: Optional[int] = None
    expense_date: Optional[date] = None
    description: Optional[str] = None
    vendor_name: Optional[str] = None
    approved_by: Optional[str] = None


class ExpenseRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    category_id: UUID
    amount: int
    expense_date: date
    description: Optional[str]
    vendor_name: Optional[str]
    payment_mode: str
    reference_number: Optional[str]
    approved_by: Optional[str]


class BudgetHeadCreate(BaseModel):
    category_id: UUID
    academic_year_id: UUID
    allocated_amount: int = Field(0, ge=0)
    notes: Optional[str] = None


class BudgetHeadUpdate(BaseModel):
    allocated_amount: Optional[int] = None
    notes: Optional[str] = None


class BudgetHeadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    category_id: UUID
    academic_year_id: UUID
    allocated_amount: int
    notes: Optional[str]


class MonthlySummaryItem(BaseModel):
    month: int
    year: int
    income: int
    expense: int
    net: int
