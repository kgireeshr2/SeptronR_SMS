"""Repository — Phase 15: Homework & PTM."""
from __future__ import annotations
from typing import List, Optional
from uuid import UUID
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.homework_ptm import (
    Homework, HomeworkSubmission, LessonPlan,
    PTMEvent, PTMSlot, PTMBooking,
)
from app.schemas.phase15 import (
    HomeworkCreate, HomeworkUpdate,
    HomeworkSubmissionCreate, HomeworkSubmissionGrade,
    LessonPlanCreate, LessonPlanUpdate,
    PTMEventCreate, PTMSlotCreate, PTMBookingCreate,
)


# ── Homework ──────────────────────────────────────────────────────────────────

async def list_homework(
    db: AsyncSession,
    school_id: str,
    class_id: Optional[str] = None,
    teacher_id: Optional[str] = None,
) -> List[Homework]:
    q = select(Homework).where(Homework.school_id == school_id, Homework.is_active == True)
    if class_id:
        q = q.where(Homework.class_id == class_id)
    if teacher_id:
        q = q.where(Homework.teacher_id == teacher_id)
    q = q.order_by(Homework.due_date.desc())
    r = await db.execute(q)
    return list(r.scalars().all())


async def get_homework(db: AsyncSession, school_id: str, hw_id: str) -> Optional[Homework]:
    r = await db.execute(
        select(Homework).where(Homework.id == hw_id, Homework.school_id == school_id)
    )
    return r.scalar_one_or_none()


async def create_homework(
    db: AsyncSession, school_id: str, teacher_id: UUID, data: HomeworkCreate
) -> Homework:
    vals = data.model_dump()
    vals.pop("max_marks", None)  # model has no max_marks column
    obj = Homework(
        id=uuid.uuid4(),
        school_id=school_id,
        teacher_id=teacher_id,
        **vals,
    )
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj

async def update_homework(
    db: AsyncSession, school_id: str, hw_id: str, data: HomeworkUpdate
) -> Optional[Homework]:
    vals = {k: v for k, v in data.model_dump(exclude_none=True).items()}
    vals.pop("max_marks", None)  # model has no max_marks column
    if vals:
        vals["updated_at"] = datetime.now(timezone.utc)
        await db.execute(
            update(Homework)
            .where(Homework.id == hw_id, Homework.school_id == school_id)
            .values(**vals)
            .execution_options(synchronize_session="fetch")
        )
        await db.flush()
    return await get_homework(db, school_id, hw_id)


# ── Homework Submissions ──────────────────────────────────────────────────────

async def list_submissions(
    db: AsyncSession, school_id: str, homework_id: str
) -> List[HomeworkSubmission]:
    r = await db.execute(
        select(HomeworkSubmission).where(HomeworkSubmission.homework_id == homework_id)
    )
    return list(r.scalars().all())


async def create_submission(
    db: AsyncSession, data: HomeworkSubmissionCreate
) -> HomeworkSubmission:
    obj = HomeworkSubmission(id=uuid.uuid4(), **data.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def grade_submission(
    db: AsyncSession, submission_id: str, data: HomeworkSubmissionGrade
) -> Optional[HomeworkSubmission]:
    await db.execute(
        update(HomeworkSubmission)
        .where(HomeworkSubmission.id == submission_id)
        .values(**data.model_dump(exclude_none=True))
    )
    r = await db.execute(
        select(HomeworkSubmission).where(HomeworkSubmission.id == submission_id)
    )
    return r.scalar_one_or_none()


# ── Lesson Plans ──────────────────────────────────────────────────────────────

async def list_lesson_plans(
    db: AsyncSession,
    school_id: str,
    class_id: Optional[str] = None,
    teacher_id: Optional[str] = None,
    plan_date: Optional[date] = None,
) -> List[LessonPlan]:
    q = select(LessonPlan).where(LessonPlan.school_id == school_id)
    if class_id:
        q = q.where(LessonPlan.class_id == class_id)
    if teacher_id:
        q = q.where(LessonPlan.teacher_id == teacher_id)
    if plan_date:
        q = q.where(LessonPlan.plan_date == plan_date)
    q = q.order_by(LessonPlan.plan_date.desc(), LessonPlan.period_number)
    r = await db.execute(q)
    return list(r.scalars().all())


async def create_lesson_plan(
    db: AsyncSession, school_id: str, teacher_id: UUID, data: LessonPlanCreate
) -> LessonPlan:
    vals = data.model_dump()
    # Map schema fields to model fields
    vals["objectives"] = vals.pop("learning_objectives", None)
    # title is required by model — use content snippet if not provided
    if not vals.get("title"):
        vals["title"] = (vals.get("content") or "Lesson Plan")[:100]
    obj = LessonPlan(
        id=uuid.uuid4(),
        school_id=school_id,
        teacher_id=teacher_id,
        **vals,
    )
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


# ── PTM Events ────────────────────────────────────────────────────────────────

async def list_ptm_events(db: AsyncSession, school_id: str) -> List[PTMEvent]:
    r = await db.execute(
        select(PTMEvent)
        .where(PTMEvent.school_id == school_id)
        .order_by(PTMEvent.ptm_date.desc())
    )
    return list(r.scalars().all())


async def get_ptm_event(db: AsyncSession, school_id: str, event_id: str) -> Optional[PTMEvent]:
    r = await db.execute(
        select(PTMEvent).where(PTMEvent.id == event_id, PTMEvent.school_id == school_id)
    )
    return r.scalar_one_or_none()


async def create_ptm_event(
    db: AsyncSession, school_id: str, created_by: UUID, data: PTMEventCreate
) -> PTMEvent:
    obj = PTMEvent(
        id=uuid.uuid4(),
        school_id=school_id,
        created_by=created_by,
        **data.model_dump(),
    )
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


# ── PTM Slots ─────────────────────────────────────────────────────────────────

async def list_slots(db: AsyncSession, school_id: str, event_id: str) -> List[PTMSlot]:
    r = await db.execute(
        select(PTMSlot)
        .where(PTMSlot.ptm_event_id == event_id)
        .order_by(PTMSlot.slot_start)
    )
    return list(r.scalars().all())


async def create_slot(db: AsyncSession, school_id: str, data: PTMSlotCreate) -> PTMSlot:
    obj = PTMSlot(id=uuid.uuid4(), **data.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


# ── PTM Bookings ──────────────────────────────────────────────────────────────

async def create_booking(
    db: AsyncSession, school_id: str, data: PTMBookingCreate
) -> PTMBooking:
    # mark slot as booked
    await db.execute(
        update(PTMSlot).where(PTMSlot.id == data.slot_id).values(is_booked=True)
    )
    await db.flush()  # flush update before insert to avoid busy connection
    vals = data.model_dump()
    vals["notes"] = vals.pop("parent_notes", None)  # model uses 'notes' not 'parent_notes'
    # PTMBooking has no school_id column
    obj = PTMBooking(id=uuid.uuid4(), **vals)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def list_bookings(db: AsyncSession, school_id: str, event_id: str) -> List[PTMBooking]:
    r = await db.execute(
        select(PTMBooking)
        .join(PTMSlot, PTMBooking.slot_id == PTMSlot.id)
        .where(PTMSlot.ptm_event_id == event_id)  # PTMBooking has no school_id
    )
    return list(r.scalars().all())

