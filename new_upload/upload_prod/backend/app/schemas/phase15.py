"""Schemas for Phase 15 — Homework & PTM."""
from __future__ import annotations
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import date, datetime


# ── Homework ──────────────────────────────────────────────────────────────────
class HomeworkCreate(BaseModel):
    class_id: UUID
    section_id: Optional[UUID] = None
    subject_id: UUID
    academic_year_id: Optional[UUID] = None
    title: str
    description: Optional[str] = None
    attachments: Optional[List[Any]] = None
    due_date: date
    max_marks: Optional[int] = None


class HomeworkUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    attachments: Optional[List[Any]] = None
    due_date: Optional[date] = None
    max_marks: Optional[int] = None
    is_active: Optional[bool] = None


class HomeworkResponse(HomeworkCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    school_id: UUID
    teacher_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ── Homework Submission ───────────────────────────────────────────────────────
class HomeworkSubmissionCreate(BaseModel):
    homework_id: UUID
    student_id: UUID
    content: Optional[str] = None
    attachments: Optional[List[Any]] = None


class HomeworkSubmissionGrade(BaseModel):
    marks_given: Optional[int] = None
    remarks: Optional[str] = None


class HomeworkSubmissionResponse(HomeworkSubmissionCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    marks_given: Optional[int] = None
    remarks: Optional[str] = None
    submitted_at: Optional[datetime] = None


# ── Lesson Plan ───────────────────────────────────────────────────────────────
class LessonPlanCreate(BaseModel):
    class_id: UUID
    section_id: Optional[UUID] = None
    subject_id: UUID
    academic_year_id: Optional[UUID] = None
    title: Optional[str] = None
    plan_date: date
    period_number: int
    content: str
    learning_objectives: Optional[str] = None
    resources: Optional[str] = None


class LessonPlanUpdate(BaseModel):
    content: Optional[str] = None
    learning_objectives: Optional[str] = None
    resources: Optional[str] = None


class LessonPlanResponse(LessonPlanCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    school_id: UUID
    teacher_id: UUID
    created_at: datetime
    updated_at: datetime


# ── PTM Event ─────────────────────────────────────────────────────────────────
class PTMEventCreate(BaseModel):
    title: str
    ptm_date: date
    academic_year_id: Optional[UUID] = None
    description: Optional[str] = None
    slot_duration_minutes: int = 15


class PTMEventResponse(PTMEventCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    school_id: UUID
    created_by: UUID
    is_active: bool
    created_at: datetime


# ── PTM Slot ──────────────────────────────────────────────────────────────────
class PTMSlotCreate(BaseModel):
    ptm_event_id: UUID
    teacher_id: UUID
    slot_start: datetime
    slot_end: datetime


class PTMSlotResponse(PTMSlotCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    is_booked: bool


# ── PTM Booking ───────────────────────────────────────────────────────────────
class PTMBookingCreate(BaseModel):
    slot_id: UUID
    student_id: UUID
    parent_notes: Optional[str] = None


class PTMBookingResponse(PTMBookingCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    status: Optional[str] = None
    created_at: datetime

    created_at: datetime
