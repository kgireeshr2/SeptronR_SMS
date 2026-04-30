"""
Service — Phase 12: Accounting
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

import app.repositories.accounting_repository as repo
from app.core.exceptions import NotFoundError


async def list_income_categories(db, school_id):
    return await repo.list_income_categories(db, school_id)


async def create_income_category(db, school_id, data):
    return await repo.create_income_category(db, school_id, data)


async def list_expense_categories(db, school_id):
    return await repo.list_expense_categories(db, school_id)


async def create_expense_category(db, school_id, data):
    return await repo.create_expense_category(db, school_id, data)


async def update_expense_category(db, school_id, cat_id, data):
    cat = await repo.get_expense_category(db, school_id, cat_id)
    if not cat:
        raise NotFoundError("Expense category not found")
    return await repo.update_expense_category(db, cat, data)


# Income Records

async def list_income_records(db, school_id, month=None, year=None, category_id=None):
    return await repo.list_income_records(db, school_id, month, year, category_id)


async def create_income_record(db, school_id, data):
    return await repo.create_income_record(db, school_id, data)


async def update_income_record(db, school_id, record_id, data):
    record = await repo.get_income_record(db, school_id, record_id)
    if not record:
        raise NotFoundError("Income record not found")
    return await repo.update_income_record(db, record, data)


async def delete_income_record(db, school_id, record_id):
    record = await repo.get_income_record(db, school_id, record_id)
    if not record:
        raise NotFoundError("Income record not found")
    await repo.delete_income_record(db, record)


# Expense Records

async def list_expense_records(db, school_id, month=None, year=None, category_id=None):
    return await repo.list_expense_records(db, school_id, month, year, category_id)


async def create_expense_record(db, school_id, data):
    return await repo.create_expense_record(db, school_id, data)


async def update_expense_record(db, school_id, record_id, data):
    record = await repo.get_expense_record(db, school_id, record_id)
    if not record:
        raise NotFoundError("Expense record not found")
    return await repo.update_expense_record(db, record, data)


async def delete_expense_record(db, school_id, record_id):
    record = await repo.get_expense_record(db, school_id, record_id)
    if not record:
        raise NotFoundError("Expense record not found")
    await repo.delete_expense_record(db, record)


# Budget Heads

async def list_budget_heads(db, school_id, academic_year_id=None):
    return await repo.list_budget_heads(db, school_id, academic_year_id)


async def create_budget_head(db, school_id, data):
    return await repo.create_budget_head(db, school_id, data)


async def update_budget_head(db, school_id, bh_id, data):
    bhs = await repo.list_budget_heads(db, school_id)
    bh = next((b for b in bhs if str(b.id) == bh_id), None)
    if not bh:
        raise NotFoundError("Budget head not found")
    return await repo.update_budget_head(db, bh, data)


# Summary

async def monthly_summary(db, school_id, year: int):
    return await repo.get_monthly_summary(db, school_id, year)

