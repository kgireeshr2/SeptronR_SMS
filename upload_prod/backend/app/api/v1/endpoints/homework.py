"""API Endpoints — Phase 15: Homework & PTM."""
from __future__ import annotations
from typing import List, Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_school_id, get_current_user, permission_required
from app.schemas.phase15 import (
    HomeworkCreate, HomeworkUpdate, HomeworkResponse,
    HomeworkSubmissionCreate, HomeworkSubmissionGrade, HomeworkSubmissionResponse,
    LessonPlanCreate, LessonPlanUpdate, LessonPlanResponse,
    PTMEventCreate, PTMEventResponse,
    PTMSlotCreate, PTMSlotResponse,
    PTMBookingCreate, PTMBookingResponse,
)
import app.services.homework_service as svc

homework_router = APIRouter(prefix="/homework", tags=["homework"])
lesson_plans_router = APIRouter(prefix="/lesson-plans", tags=["homework"])
ptm_router = APIRouter(prefix="/ptm", tags=["ptm"])


# ── Homework ──────────────────────────────────────────────────────────────────

@homework_router.get("", response_model=List[HomeworkResponse])
async def list_homework(
    class_id: Optional[UUID] = None,
    school_id: str = Depends(get_school_id),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await svc.list_homework(
        db, school_id,
        class_id=str(class_id) if class_id else None,
    )


@homework_router.post("", response_model=HomeworkResponse, status_code=status.HTTP_201_CREATED)
async def create_homework(
    data: HomeworkCreate,
    school_id: str = Depends(get_school_id),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(permission_required("homework", "write")),
):
    return await svc.create_homework(db, school_id, current_user.id, data)


@homework_router.put("/{hw_id}", response_model=HomeworkResponse)
async def update_homework(
    hw_id: UUID,
    data: HomeworkUpdate,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(permission_required("homework", "write")),
):
    try:
        return await svc.update_homework(db, school_id, str(hw_id), data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@homework_router.get("/{hw_id}/submissions", response_model=List[HomeworkSubmissionResponse])
async def list_submissions(
    hw_id: UUID,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(permission_required("homework", "read")),
):
    return await svc.list_submissions(db, school_id, str(hw_id))


@homework_router.post("/{hw_id}/submissions", response_model=HomeworkSubmissionResponse, status_code=201)
async def submit_homework(
    hw_id: UUID,
    data: HomeworkSubmissionCreate,
    db: AsyncSession = Depends(get_db),
):
    return await svc.submit_homework(db, data)


@homework_router.put("/submissions/{sub_id}/grade", response_model=HomeworkSubmissionResponse)
async def grade_submission(
    sub_id: UUID,
    data: HomeworkSubmissionGrade,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(permission_required("homework", "write")),
):
    obj = await svc.grade_submission(db, str(sub_id), data)
    if not obj:
        raise HTTPException(status_code=404, detail="Submission not found")
    return obj


# ── Lesson Plans ──────────────────────────────────────────────────────────────

@lesson_plans_router.get("", response_model=List[LessonPlanResponse])
async def list_lesson_plans(
    class_id: Optional[UUID] = None,
    plan_date: Optional[date] = None,
    school_id: str = Depends(get_school_id),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await svc.list_lesson_plans(
        db, school_id,
        class_id=str(class_id) if class_id else None,
        teacher_id=str(current_user.id),
        plan_date=plan_date,
    )


@lesson_plans_router.post("", response_model=LessonPlanResponse, status_code=201)
async def create_lesson_plan(
    data: LessonPlanCreate,
    school_id: str = Depends(get_school_id),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(permission_required("homework", "write")),
):
    return await svc.create_lesson_plan(db, school_id, current_user.id, data)


# ── PTM ───────────────────────────────────────────────────────────────────────

@ptm_router.get("/events", response_model=List[PTMEventResponse])
async def list_ptm_events(
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
):
    return await svc.list_ptm_events(db, school_id)


@ptm_router.post("/events", response_model=PTMEventResponse, status_code=201)
async def create_ptm_event(
    data: PTMEventCreate,
    school_id: str = Depends(get_school_id),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(permission_required("ptm", "write")),
):
    return await svc.create_ptm_event(db, school_id, current_user.id, data)


@ptm_router.get("/events/{event_id}/slots", response_model=List[PTMSlotResponse])
async def list_slots(
    event_id: UUID,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
):
    return await svc.list_slots(db, school_id, str(event_id))


@ptm_router.post("/slots", response_model=PTMSlotResponse, status_code=201)
async def create_slot(
    data: PTMSlotCreate,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(permission_required("ptm", "write")),
):
    return await svc.create_slot(db, school_id, data)


@ptm_router.post("/bookings", response_model=PTMBookingResponse, status_code=201)
async def book_slot(
    data: PTMBookingCreate,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
):
    return await svc.book_slot(db, school_id, data)


@ptm_router.get("/events/{event_id}/bookings", response_model=List[PTMBookingResponse])
async def list_bookings(
    event_id: UUID,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(permission_required("ptm", "read")),
):
    return await svc.list_bookings(db, school_id, str(event_id))

