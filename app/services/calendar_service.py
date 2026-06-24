"""Service — Phase 16: Calendar Events."""
from __future__ import annotations
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

import app.repositories.calendar_repository as repo
from app.schemas.phase16 import CalendarEventCreate, CalendarEventUpdate


async def list_events(
    db: AsyncSession,
    school_id: str,
    event_type: Optional[str] = None,
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
):
    return await repo.list_events(db, school_id, event_type, from_dt, to_dt)


async def create_event(
    db: AsyncSession, school_id: str, created_by: UUID, data: CalendarEventCreate
):
    if data.end_datetime <= data.start_datetime:
        raise ValueError("end_datetime must be after start_datetime")
    return await repo.create_event(db, school_id, created_by, data)


async def update_event(
    db: AsyncSession, school_id: str, event_id: str, data: CalendarEventUpdate
):
    obj = await repo.get_event(db, school_id, event_id)
    if not obj:
        raise ValueError("Event not found")
    return await repo.update_event(db, school_id, event_id, data)


async def delete_event(db: AsyncSession, school_id: str, event_id: str) -> bool:
    return await repo.delete_event(db, school_id, event_id)

