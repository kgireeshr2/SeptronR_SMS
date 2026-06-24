"""Service — Phase 15: Homework & PTM."""
from __future__ import annotations
from typing import List, Optional
from uuid import UUID
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

import app.repositories.homework_repository as repo
from app.schemas.phase15 import (
    HomeworkCreate, HomeworkUpdate,
    HomeworkSubmissionCreate, HomeworkSubmissionGrade,
    LessonPlanCreate, LessonPlanUpdate,
    PTMEventCreate, PTMSlotCreate, PTMBookingCreate,
)


async def list_homework(
    db: AsyncSession, school_id: str,
    class_id: Optional[str] = None,
    teacher_id: Optional[str] = None,
):
    return await repo.list_homework(db, school_id, class_id, teacher_id)


async def create_homework(db: AsyncSession, school_id: str, teacher_id: UUID, data: HomeworkCreate):
    obj = await repo.create_homework(db, school_id, teacher_id, data)
    try:
        from app.services.notifications.notify import notify_event
        notify_event(
            school_id, "homework_assigned", audience="class",
            class_id=str(obj.class_id),
            section_id=str(obj.section_id) if getattr(obj, "section_id", None) else None,
            default_channels=["in_app", "whatsapp"],
            title="New Homework",
            body=f"New homework assigned: {obj.title} (due {obj.due_date}).",
            context={"title": obj.title, "due_date": str(obj.due_date)},
            link="/homework",
        )
    except Exception:
        pass
    return obj


async def update_homework(db: AsyncSession, school_id: str, hw_id: str, data: HomeworkUpdate):
    obj = await repo.get_homework(db, school_id, hw_id)
    if not obj:
        raise ValueError("Homework not found")
    return await repo.update_homework(db, school_id, hw_id, data)


async def list_submissions(db: AsyncSession, school_id: str, homework_id: str):
    return await repo.list_submissions(db, school_id, homework_id)


async def submit_homework(db: AsyncSession, school_id: str, data: HomeworkSubmissionCreate):
    return await repo.create_submission(db, school_id, data)


async def grade_submission(db: AsyncSession, school_id: str, submission_id: str, data: HomeworkSubmissionGrade):
    return await repo.grade_submission(db, school_id, submission_id, data)


async def list_lesson_plans(
    db: AsyncSession, school_id: str,
    class_id: Optional[str] = None,
    teacher_id: Optional[str] = None,
    plan_date: Optional[date] = None,
):
    return await repo.list_lesson_plans(db, school_id, class_id, teacher_id, plan_date)


async def create_lesson_plan(
    db: AsyncSession, school_id: str, teacher_id: UUID, data: LessonPlanCreate
):
    return await repo.create_lesson_plan(db, school_id, teacher_id, data)


async def list_ptm_events(db: AsyncSession, school_id: str):
    return await repo.list_ptm_events(db, school_id)


async def create_ptm_event(db: AsyncSession, school_id: str, created_by: UUID, data: PTMEventCreate):
    return await repo.create_ptm_event(db, school_id, created_by, data)


async def list_slots(db: AsyncSession, school_id: str, event_id: str):
    return await repo.list_slots(db, school_id, event_id)


async def create_slot(db: AsyncSession, school_id: str, data: PTMSlotCreate):
    return await repo.create_slot(db, school_id, data)


async def book_slot(db: AsyncSession, school_id: str, data: PTMBookingCreate):
    # Check slot availability
    slots = await repo.list_slots(db, school_id, str(data.slot_id))
    # slot is identified individually — check is_booked via direct query would be cleaner
    # For now, attempt create; DB-level constraint handles duplicates
    return await repo.create_booking(db, school_id, data)


async def list_bookings(db: AsyncSession, school_id: str, event_id: str):
    return await repo.list_bookings(db, school_id, event_id)

