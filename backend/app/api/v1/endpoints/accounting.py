"""
API Endpoints — Phase 12: Accounting
"""
from __future__ import annotations

from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_school_id, permission_required
import app.services.accounting_service as svc
from app.schemas.phase12 import (
    IncomeCategoryCreate, IncomeCategoryResponse,
    ExpenseCategoryCreate, ExpenseCategoryUpdate, ExpenseCategoryResponse,
    IncomeRecordCreate, IncomeRecordUpdate, IncomeRecordResponse,
    ExpenseRecordCreate, ExpenseRecordUpdate, ExpenseRecordResponse,
    BudgetHeadCreate, BudgetHeadUpdate, BudgetHeadResponse,
    MonthlySummaryItem,
)

income_cat_router = APIRouter(prefix="/accounting/income-categories", tags=["Accounting"])
expense_cat_router = APIRouter(prefix="/accounting/expense-categories", tags=["Accounting"])
income_router = APIRouter(prefix="/accounting/income", tags=["Accounting"])
expense_router = APIRouter(prefix="/accounting/expenses", tags=["Accounting"])
budget_router = APIRouter(prefix="/accounting/budgets", tags=["Accounting"])
summary_router = APIRouter(prefix="/accounting/summary", tags=["Accounting"])


# ─── Income Categories ───────────────────────────────────────────────────────

@income_cat_router.get("", response_model=List[IncomeCategoryResponse])
async def list_income_cats(school_id=Depends(get_school_id), db=Depends(get_db),
                           _=Depends(permission_required("accounting", "view"))):
    return await svc.list_income_categories(db, school_id)


@income_cat_router.post("", response_model=IncomeCategoryResponse,
                        status_code=status.HTTP_201_CREATED)
async def create_income_cat(data: IncomeCategoryCreate, school_id=Depends(get_school_id),
                            db=Depends(get_db), _=Depends(permission_required("accounting", "manage"))):
    obj = await svc.create_income_category(db, school_id, data)
    await db.commit()
    await db.refresh(obj)
    return obj


# ─── Expense Categories ──────────────────────────────────────────────────────

@expense_cat_router.get("", response_model=List[ExpenseCategoryResponse])
async def list_expense_cats(school_id=Depends(get_school_id), db=Depends(get_db),
                            _=Depends(permission_required("accounting", "view"))):
    return await svc.list_expense_categories(db, school_id)


@expense_cat_router.post("", response_model=ExpenseCategoryResponse,
                         status_code=status.HTTP_201_CREATED)
async def create_expense_cat(data: ExpenseCategoryCreate, school_id=Depends(get_school_id),
                             db=Depends(get_db), _=Depends(permission_required("accounting", "manage"))):
    obj = await svc.create_expense_category(db, school_id, data)
    await db.commit()
    await db.refresh(obj)
    return obj


@expense_cat_router.put("/{cat_id}", response_model=ExpenseCategoryResponse)
async def update_expense_cat(cat_id: UUID, data: ExpenseCategoryUpdate,
                             school_id=Depends(get_school_id), db=Depends(get_db),
                             _=Depends(permission_required("accounting", "manage"))):
    obj = await svc.update_expense_category(db, school_id, str(cat_id), data)
    await db.commit()
    await db.refresh(obj)
    return obj


# ─── Income Records ──────────────────────────────────────────────────────────

@income_router.get("", response_model=List[IncomeRecordResponse])
async def list_income(
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None),
    category_id: Optional[UUID] = Query(None),
    school_id=Depends(get_school_id), db=Depends(get_db),
    _=Depends(permission_required("accounting", "view")),
):
    return await svc.list_income_records(db, school_id, month, year, str(category_id) if category_id else None)


@income_router.post("", response_model=IncomeRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_income(data: IncomeRecordCreate, school_id=Depends(get_school_id),
                        db=Depends(get_db), _=Depends(permission_required("accounting", "manage"))):
    obj = await svc.create_income_record(db, school_id, data)
    await db.commit()
    await db.refresh(obj)
    return obj


@income_router.put("/{record_id}", response_model=IncomeRecordResponse)
async def update_income(record_id: UUID, data: IncomeRecordUpdate,
                        school_id=Depends(get_school_id), db=Depends(get_db),
                        _=Depends(permission_required("accounting", "manage"))):
    obj = await svc.update_income_record(db, school_id, str(record_id), data)
    await db.commit()
    await db.refresh(obj)
    return obj


@income_router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_income(record_id: UUID, school_id=Depends(get_school_id), db=Depends(get_db),
                        _=Depends(permission_required("accounting", "manage"))):
    await svc.delete_income_record(db, school_id, str(record_id))
    await db.commit()


# ─── Expense Records ─────────────────────────────────────────────────────────

@expense_router.get("", response_model=List[ExpenseRecordResponse])
async def list_expense(
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None),
    category_id: Optional[UUID] = Query(None),
    school_id=Depends(get_school_id), db=Depends(get_db),
    _=Depends(permission_required("accounting", "view")),
):
    return await svc.list_expense_records(db, school_id, month, year, str(category_id) if category_id else None)


@expense_router.post("", response_model=ExpenseRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(data: ExpenseRecordCreate, school_id=Depends(get_school_id),
                         db=Depends(get_db), _=Depends(permission_required("accounting", "manage"))):
    obj = await svc.create_expense_record(db, school_id, data)
    await db.commit()
    await db.refresh(obj)
    return obj


@expense_router.put("/{record_id}", response_model=ExpenseRecordResponse)
async def update_expense(record_id: UUID, data: ExpenseRecordUpdate,
                         school_id=Depends(get_school_id), db=Depends(get_db),
                         _=Depends(permission_required("accounting", "manage"))):
    obj = await svc.update_expense_record(db, school_id, str(record_id), data)
    await db.commit()
    await db.refresh(obj)
    return obj


@expense_router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(record_id: UUID, school_id=Depends(get_school_id), db=Depends(get_db),
                         _=Depends(permission_required("accounting", "manage"))):
    await svc.delete_expense_record(db, school_id, str(record_id))
    await db.commit()


# ─── Budget Heads ─────────────────────────────────────────────────────────────

@budget_router.get("", response_model=List[BudgetHeadResponse])
async def list_budgets(
    year_id: Optional[UUID] = Query(None),
    school_id=Depends(get_school_id), db=Depends(get_db),
    _=Depends(permission_required("accounting", "view")),
):
    return await svc.list_budget_heads(db, school_id, str(year_id) if year_id else None)


@budget_router.post("", response_model=BudgetHeadResponse, status_code=status.HTTP_201_CREATED)
async def create_budget(data: BudgetHeadCreate, school_id=Depends(get_school_id),
                        db=Depends(get_db), _=Depends(permission_required("accounting", "manage"))):
    obj = await svc.create_budget_head(db, school_id, data)
    await db.commit()
    await db.refresh(obj)
    return obj


@budget_router.put("/{bh_id}", response_model=BudgetHeadResponse)
async def update_budget(bh_id: UUID, data: BudgetHeadUpdate, school_id=Depends(get_school_id),
                        db=Depends(get_db), _=Depends(permission_required("accounting", "manage"))):
    obj = await svc.update_budget_head(db, school_id, str(bh_id), data)
    await db.commit()
    await db.refresh(obj)
    return obj


# ─── Summary ─────────────────────────────────────────────────────────────────

@summary_router.get("/monthly", response_model=List[MonthlySummaryItem])
async def monthly_summary(
    year: int = Query(...),
    school_id=Depends(get_school_id), db=Depends(get_db),
    _=Depends(permission_required("accounting", "view")),
):
    return await svc.monthly_summary(db, school_id, year)

