"""
Repository — Phase 12: Accounting
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.accounting import (
    IncomeCategory, ExpenseCategory, IncomeRecord, ExpenseRecord, BudgetHead,
)
from app.schemas.phase12 import (
    IncomeCategoryCreate, ExpenseCategoryCreate, ExpenseCategoryUpdate,
    IncomeRecordCreate, IncomeRecordUpdate,
    ExpenseRecordCreate, ExpenseRecordUpdate,
    BudgetHeadCreate, BudgetHeadUpdate,
)


# ─── Income Categories ───────────────────────────────────────────────────────

async def list_income_categories(db: AsyncSession, school_id: str) -> List[IncomeCategory]:
    r = await db.execute(select(IncomeCategory).where(IncomeCategory.school_id == school_id))
    return list(r.scalars().all())


async def create_income_category(
    db: AsyncSession, school_id: str, data: IncomeCategoryCreate
) -> IncomeCategory:
    obj = IncomeCategory(school_id=school_id, **data.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


# ─── Expense Categories ──────────────────────────────────────────────────────

async def list_expense_categories(db: AsyncSession, school_id: str) -> List[ExpenseCategory]:
    r = await db.execute(
        select(ExpenseCategory).where(ExpenseCategory.school_id == school_id)
    )
    return list(r.scalars().all())


async def get_expense_category(
    db: AsyncSession, school_id: str, cat_id: str
) -> Optional[ExpenseCategory]:
    r = await db.execute(
        select(ExpenseCategory).where(
            ExpenseCategory.id == cat_id, ExpenseCategory.school_id == school_id
        )
    )
    return r.scalar_one_or_none()


async def create_expense_category(
    db: AsyncSession, school_id: str, data: ExpenseCategoryCreate
) -> ExpenseCategory:
    obj = ExpenseCategory(school_id=school_id, **data.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def update_expense_category(
    db: AsyncSession, cat: ExpenseCategory, data: ExpenseCategoryUpdate
) -> ExpenseCategory:
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(cat, k, v)
    await db.flush()
    await db.refresh(cat)
    return cat


# ─── Income Records ──────────────────────────────────────────────────────────

async def list_income_records(
    db: AsyncSession, school_id: str,
    month: Optional[int] = None, year: Optional[int] = None,
    category_id: Optional[str] = None,
) -> List[IncomeRecord]:
    q = select(IncomeRecord).where(IncomeRecord.school_id == school_id)
    if month:
        q = q.where(extract("month", IncomeRecord.income_date) == month)
    if year:
        q = q.where(extract("year", IncomeRecord.income_date) == year)
    if category_id:
        q = q.where(IncomeRecord.category_id == category_id)
    r = await db.execute(q.order_by(IncomeRecord.income_date.desc()))
    return list(r.scalars().all())


async def get_income_record(
    db: AsyncSession, school_id: str, record_id: str
) -> Optional[IncomeRecord]:
    r = await db.execute(
        select(IncomeRecord).where(
            IncomeRecord.id == record_id, IncomeRecord.school_id == school_id
        )
    )
    return r.scalar_one_or_none()


async def create_income_record(
    db: AsyncSession, school_id: str, data: IncomeRecordCreate
) -> IncomeRecord:
    obj = IncomeRecord(school_id=school_id, **data.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def update_income_record(
    db: AsyncSession, record: IncomeRecord, data: IncomeRecordUpdate
) -> IncomeRecord:
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(record, k, v)
    await db.flush()
    await db.refresh(record)
    return record


async def delete_income_record(db: AsyncSession, record: IncomeRecord) -> None:
    await db.delete(record)
    await db.flush()


# ─── Expense Records ─────────────────────────────────────────────────────────

async def list_expense_records(
    db: AsyncSession, school_id: str,
    month: Optional[int] = None, year: Optional[int] = None,
    category_id: Optional[str] = None,
) -> List[ExpenseRecord]:
    q = select(ExpenseRecord).where(ExpenseRecord.school_id == school_id)
    if month:
        q = q.where(extract("month", ExpenseRecord.expense_date) == month)
    if year:
        q = q.where(extract("year", ExpenseRecord.expense_date) == year)
    if category_id:
        q = q.where(ExpenseRecord.category_id == category_id)
    r = await db.execute(q.order_by(ExpenseRecord.expense_date.desc()))
    return list(r.scalars().all())


async def get_expense_record(
    db: AsyncSession, school_id: str, record_id: str
) -> Optional[ExpenseRecord]:
    r = await db.execute(
        select(ExpenseRecord).where(
            ExpenseRecord.id == record_id, ExpenseRecord.school_id == school_id
        )
    )
    return r.scalar_one_or_none()


async def create_expense_record(
    db: AsyncSession, school_id: str, data: ExpenseRecordCreate
) -> ExpenseRecord:
    obj = ExpenseRecord(school_id=school_id, **data.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def update_expense_record(
    db: AsyncSession, record: ExpenseRecord, data: ExpenseRecordUpdate
) -> ExpenseRecord:
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(record, k, v)
    await db.flush()
    await db.refresh(record)
    return record


async def delete_expense_record(db: AsyncSession, record: ExpenseRecord) -> None:
    await db.delete(record)
    await db.flush()


# ─── Budget Heads ────────────────────────────────────────────────────────────

async def list_budget_heads(
    db: AsyncSession, school_id: str, academic_year_id: Optional[str] = None
) -> List[BudgetHead]:
    q = select(BudgetHead).where(BudgetHead.school_id == school_id)
    if academic_year_id:
        q = q.where(BudgetHead.academic_year_id == academic_year_id)
    r = await db.execute(q)
    return list(r.scalars().all())


async def create_budget_head(
    db: AsyncSession, school_id: str, data: BudgetHeadCreate
) -> BudgetHead:
    obj = BudgetHead(school_id=school_id, **data.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def update_budget_head(
    db: AsyncSession, bh: BudgetHead, data: BudgetHeadUpdate
) -> BudgetHead:
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(bh, k, v)
    await db.flush()
    await db.refresh(bh)
    return bh


# ─── Summary ─────────────────────────────────────────────────────────────────

async def get_monthly_summary(db: AsyncSession, school_id: str, year: int) -> list:
    income_q = await db.execute(
        select(
            extract("month", IncomeRecord.income_date).label("month"),
            func.sum(IncomeRecord.amount).label("income"),
        )
        .where(
            IncomeRecord.school_id == school_id,
            extract("year", IncomeRecord.income_date) == year,
        )
        .group_by(extract("month", IncomeRecord.income_date))
    )
    expense_q = await db.execute(
        select(
            extract("month", ExpenseRecord.expense_date).label("month"),
            func.sum(ExpenseRecord.amount).label("expense"),
        )
        .where(
            ExpenseRecord.school_id == school_id,
            extract("year", ExpenseRecord.expense_date) == year,
        )
        .group_by(extract("month", ExpenseRecord.expense_date))
    )
    income_map = {int(r.month): int(r.income) for r in income_q}
    expense_map = {int(r.month): int(r.expense) for r in expense_q}
    result = []
    for m in range(1, 13):
        inc = income_map.get(m, 0)
        exp = expense_map.get(m, 0)
        result.append({"month": m, "year": year, "income": inc, "expense": exp, "net": inc - exp})
    return result

