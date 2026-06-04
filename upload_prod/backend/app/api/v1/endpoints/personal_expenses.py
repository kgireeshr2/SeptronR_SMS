"""
Personal Expenses API
Tracks student-level charges (stationery, materials, trips, etc.)
Completely independent from school fee accounts.
"""
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_school_id, permission_required
from app.db.session import get_db
from app.models.personal_expenses import PersonalExpense, PersonalExpenseCategory
from app.models.students import Student, StudentEnrollment
from app.utils.response import ok

router = APIRouter(prefix="/personal-expenses", tags=["Personal Expenses"])


# ─── Schemas ─────────────────────────────────────────────────────────────────

class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ExpenseCreate(BaseModel):
    student_id: UUID
    category_id: Optional[UUID] = None
    title: str
    amount: float
    expense_date: Optional[date] = None
    notes: Optional[str] = None


class ExpenseUpdate(BaseModel):
    category_id: Optional[UUID] = None
    title: Optional[str] = None
    amount: Optional[float] = None
    expense_date: Optional[date] = None
    notes: Optional[str] = None


class MarkPaidRequest(BaseModel):
    payment_method: Optional[str] = "cash"
    paid_at: Optional[date] = None
    amount_paid: Optional[float] = None  # custom amount; defaults to full remaining balance


class WaiveRequest(BaseModel):
    reason: Optional[str] = None


class BulkAssignRequest(BaseModel):
    title: str
    amount: float
    category_id: Optional[UUID] = None
    expense_date: Optional[date] = None
    notes: Optional[str] = None
    # Target: at least one of these is required
    class_id: Optional[UUID] = None
    section_id: Optional[UUID] = None
    academic_year_id: Optional[UUID] = None
    student_ids: Optional[list[UUID]] = None


# ─── Category endpoints ───────────────────────────────────────────────────────

@router.get("/categories")
async def list_categories(
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("fees", "view")),
):
    result = await db.execute(
        select(PersonalExpenseCategory)
        .where(PersonalExpenseCategory.school_id == school_id)
        .order_by(PersonalExpenseCategory.name)
    )
    cats = result.scalars().all()
    return ok([_cat_out(c) for c in cats], f"{len(cats)} categories")


@router.post("/categories", status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("fees", "create")),
):
    cat = PersonalExpenseCategory(
        school_id=school_id,
        name=data.name,
        description=data.description,
        is_active=data.is_active,
    )
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return ok(_cat_out(cat), "Category created")


@router.put("/categories/{cat_id}")
async def update_category(
    cat_id: UUID,
    data: CategoryUpdate,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("fees", "edit")),
):
    cat = await _get_cat(db, cat_id, school_id)
    if data.name is not None:
        cat.name = data.name
    if data.description is not None:
        cat.description = data.description
    if data.is_active is not None:
        cat.is_active = data.is_active
    await db.commit()
    await db.refresh(cat)
    return ok(_cat_out(cat), "Category updated")


@router.delete("/categories/{cat_id}")
async def delete_category(
    cat_id: UUID,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("fees", "delete")),
):
    cat = await _get_cat(db, cat_id, school_id)
    await db.delete(cat)
    await db.commit()
    return ok(None, "Category deleted")


# ─── Expense endpoints ────────────────────────────────────────────────────────

@router.get("")
async def list_expenses(
    student_id: Optional[UUID] = Query(None),
    class_id: Optional[UUID] = Query(None),
    section_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("fees", "view")),
):
    # Join with Student and latest enrollment for name/class info
    q = (
        select(PersonalExpense, Student)
        .join(Student, Student.id == PersonalExpense.student_id, isouter=True)
        .where(PersonalExpense.school_id == school_id)
    )
    if student_id:
        q = q.where(PersonalExpense.student_id == student_id)
    if status:
        q = q.where(PersonalExpense.status == status)
    if class_id or section_id:
        # Filter by class/section via enrollment
        enroll_sub = select(StudentEnrollment.student_id).where(
            StudentEnrollment.is_current == True
        )
        if class_id:
            enroll_sub = enroll_sub.where(StudentEnrollment.class_id == class_id)
        if section_id:
            enroll_sub = enroll_sub.where(StudentEnrollment.section_id == section_id)
        q = q.where(PersonalExpense.student_id.in_(enroll_sub))

    # Count total
    count_q = select(func.count()).select_from(q.subquery())
    total_count = (await db.execute(count_q)).scalar_one()

    q = q.order_by(PersonalExpense.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(q)
    rows = result.all()

    expenses = []
    for exp, student in rows:
        out = _exp_out(exp)
        out["student_name"] = f"{student.first_name} {student.last_name}".strip() if student else "Unknown"
        out["admission_number"] = student.admission_number if student else None
        expenses.append(out)

    # totals for the student
    summary = {}
    if student_id:
        summary = await _student_summary(db, school_id, student_id)

    return ok({"expenses": expenses, "summary": summary, "total": total_count}, f"{len(expenses)} expenses")


@router.post("/bulk-assign", status_code=status.HTTP_201_CREATED)
async def bulk_assign(
    data: BulkAssignRequest,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    _=Depends(permission_required("fees", "create")),
):
    """Assign a personal expense to many students at once (by class/section or explicit list)."""
    if not (data.class_id or data.section_id or data.student_ids):
        raise HTTPException(status_code=400, detail="Provide class_id, section_id, or student_ids")

    # Resolve student IDs
    if data.student_ids:
        student_ids = [str(sid) for sid in data.student_ids]
    else:
        enroll_q = select(StudentEnrollment.student_id).where(
            StudentEnrollment.is_current == True,
            StudentEnrollment.school_id == school_id,
        )
        if data.class_id:
            enroll_q = enroll_q.where(StudentEnrollment.class_id == data.class_id)
        if data.section_id:
            enroll_q = enroll_q.where(StudentEnrollment.section_id == data.section_id)
        if data.academic_year_id:
            enroll_q = enroll_q.where(StudentEnrollment.academic_year_id == data.academic_year_id)
        res = await db.execute(enroll_q)
        student_ids = [str(r[0]) for r in res.all()]

    if not student_ids:
        raise HTTPException(status_code=404, detail="No students found for the given criteria")

    created = []
    for sid in student_ids:
        exp = PersonalExpense(
            school_id=school_id,
            student_id=sid,
            category_id=data.category_id,
            title=data.title,
            amount=data.amount,
            expense_date=data.expense_date or date.today(),
            notes=data.notes,
            status="pending",
            collected_by=current_user.id,
        )
        db.add(exp)
        created.append(exp)

    await db.commit()
    return ok({"assigned_count": len(created)}, f"Assigned to {len(created)} students")


@router.get("/school-summary")
async def school_summary(
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("fees", "view")),
):
    """School-wide totals across all students."""
    result = await db.execute(
        select(
            func.count(PersonalExpense.id).label("total_count"),
            func.coalesce(func.sum(PersonalExpense.amount), 0).label("total_billed"),
            func.coalesce(func.sum(PersonalExpense.paid_amount), 0).label("total_collected"),
        ).where(
            and_(PersonalExpense.school_id == school_id,
                 PersonalExpense.status.in_(["pending", "partial", "paid"]))
        )
    )
    row = result.one()
    total_billed = float(row.total_billed)
    total_collected = float(row.total_collected)
    balance_due = round(total_billed - total_collected, 2)
    return ok({
        "total_count": row.total_count,
        "total_amount": total_billed,
        "paid_amount": total_collected,
        "pending_amount": balance_due,
        "balance_due": balance_due,
    }, "School summary")


@router.get("/student/{student_id}/summary")
async def student_summary(
    student_id: UUID,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("fees", "view")),
):
    summary = await _student_summary(db, school_id, student_id)
    return ok(summary, "Summary")


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_expense(
    data: ExpenseCreate,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    _=Depends(permission_required("fees", "create")),
):
    exp = PersonalExpense(
        school_id=school_id,
        student_id=data.student_id,
        category_id=data.category_id,
        title=data.title,
        amount=data.amount,
        expense_date=data.expense_date or date.today(),
        notes=data.notes,
        status="pending",
        collected_by=current_user.id,
    )
    db.add(exp)
    await db.commit()
    await db.refresh(exp)
    return ok(_exp_out(exp), "Expense created")


@router.put("/{expense_id}")
async def update_expense(
    expense_id: UUID,
    data: ExpenseUpdate,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("fees", "edit")),
):
    exp = await _get_exp(db, expense_id, school_id)
    if data.category_id is not None:
        exp.category_id = data.category_id
    if data.title is not None:
        exp.title = data.title
    if data.amount is not None:
        exp.amount = data.amount
    if data.expense_date is not None:
        exp.expense_date = data.expense_date
    if data.notes is not None:
        exp.notes = data.notes
    await db.commit()
    await db.refresh(exp)
    return ok(_exp_out(exp), "Expense updated")


@router.post("/{expense_id}/mark-paid")
async def mark_paid(
    expense_id: UUID,
    data: MarkPaidRequest,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    _=Depends(permission_required("fees", "collect")),
):
    exp = await _get_exp(db, expense_id, school_id)
    remaining = float(exp.amount) - float(exp.paid_amount or 0)
    collecting = float(data.amount_paid) if data.amount_paid is not None else remaining
    collecting = max(0.0, min(collecting, remaining))  # clamp to valid range
    exp.paid_amount = float(exp.paid_amount or 0) + collecting
    exp.paid_at = data.paid_at or date.today()
    exp.payment_method = data.payment_method or "cash"
    exp.collected_by = current_user.id
    if float(exp.paid_amount) >= float(exp.amount):
        exp.status = "paid"
    else:
        exp.status = "partial"
    await db.commit()
    await db.refresh(exp)
    return ok(_exp_out(exp), "Marked as paid")


@router.post("/{expense_id}/waive")
async def waive_expense(
    expense_id: UUID,
    data: WaiveRequest = None,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("fees", "edit")),
):
    exp = await _get_exp(db, expense_id, school_id)
    exp.status = "waived"
    await db.commit()
    await db.refresh(exp)
    return ok(_exp_out(exp), "Expense waived")


@router.delete("/{expense_id}")
async def delete_expense(
    expense_id: UUID,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("fees", "delete")),
):
    exp = await _get_exp(db, expense_id, school_id)
    await db.delete(exp)
    await db.commit()
    return ok(None, "Expense deleted")


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _cat_out(c: PersonalExpenseCategory) -> dict:
    return {
        "id": str(c.id),
        "school_id": str(c.school_id),
        "name": c.name,
        "description": c.description,
        "is_active": c.is_active,
        "created_at": c.created_at,
    }


def _exp_out(e: PersonalExpense) -> dict:
    amount = float(e.amount)
    paid = float(e.paid_amount or 0)
    return {
        "id": str(e.id),
        "school_id": str(e.school_id),
        "student_id": str(e.student_id),
        "category_id": str(e.category_id) if e.category_id else None,
        "title": e.title,
        "amount": amount,
        "paid_amount": paid,
        "balance": round(amount - paid, 2),
        "expense_date": str(e.expense_date) if e.expense_date else None,
        "notes": e.notes,
        "status": e.status,
        "paid_at": str(e.paid_at) if e.paid_at else None,
        "payment_method": e.payment_method,
        "collected_by": str(e.collected_by) if e.collected_by else None,
        "created_at": e.created_at,
        "updated_at": e.updated_at,
    }


async def _get_cat(db: AsyncSession, cat_id: UUID, school_id: UUID) -> PersonalExpenseCategory:
    result = await db.execute(
        select(PersonalExpenseCategory).where(
            and_(PersonalExpenseCategory.id == cat_id, PersonalExpenseCategory.school_id == school_id)
        )
    )
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return cat


async def _get_exp(db: AsyncSession, expense_id: UUID, school_id: UUID) -> PersonalExpense:
    result = await db.execute(
        select(PersonalExpense).where(
            and_(PersonalExpense.id == expense_id, PersonalExpense.school_id == school_id)
        )
    )
    exp = result.scalar_one_or_none()
    if not exp:
        raise HTTPException(status_code=404, detail="Expense not found")
    return exp


async def _student_summary(db: AsyncSession, school_id: UUID, student_id: UUID) -> dict:
    result = await db.execute(
        select(
            func.count(PersonalExpense.id).label("total_count"),
            func.coalesce(func.sum(PersonalExpense.amount), 0).label("total_billed"),
            func.coalesce(func.sum(PersonalExpense.paid_amount), 0).label("total_collected"),
        ).where(
            and_(PersonalExpense.school_id == school_id, PersonalExpense.student_id == student_id,
                 PersonalExpense.status.in_(["pending", "partial", "paid"]))
        )
    )
    row = result.one()
    total_billed = float(row.total_billed)
    total_collected = float(row.total_collected)
    balance_due = round(total_billed - total_collected, 2)
    return {
        "total_count": row.total_count,
        "total_amount": total_billed,
        "paid_amount": total_collected,
        "pending_amount": balance_due,
        "balance_due": balance_due,
    }
