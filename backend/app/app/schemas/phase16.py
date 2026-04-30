"""Schemas for Phase 16 — Calendar Events."""
from __future__ import annotations
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime


class CalendarEventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    event_type: str = "other"
    start_datetime: datetime
    end_datetime: datetime
    all_day: bool = False
    color_tag: Optional[str] = None
    audience: str = "all"
    audience_filter: Optional[Any] = None
    academic_year_id: Optional[UUID] = None
    recurrence_rule: Optional[str] = None
    is_active: bool = True


class CalendarEventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    event_type: Optional[str] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    all_day: Optional[bool] = None
    color_tag: Optional[str] = None
    audience: Optional[str] = None
    audience_filter: Optional[Any] = None
    recurrence_rule: Optional[str] = None
    is_active: Optional[bool] = None


class CalendarEventResponse(CalendarEventCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    school_id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: datetime
