"""Repository — Phase 16: Calendar Events."""
from __future__ import annotations
from typing import List, Optional
from uuid import UUID
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calendar import CalendarEvent
from app.schemas.phase16 import CalendarEventCreate, CalendarEventUpdate


async def list_events(
    db: AsyncSession,
    school_id: str,
    event_type: Optional[str] = None,
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
) -> List[CalendarEvent]:
    q = select(CalendarEvent).where(
        CalendarEvent.school_id == school_id,
        CalendarEvent.is_active == True,
    )
    if event_type:
        q = q.where(CalendarEvent.event_type == event_type)
    if from_dt:
        q = q.where(CalendarEvent.end_datetime >= from_dt)
    if to_dt:
        q = q.where(CalendarEvent.start_datetime <= to_dt)
    q = q.order_by(CalendarEvent.start_datetime)
    r = await db.execute(q)
    return list(r.scalars().all())


async def get_event(db: AsyncSession, school_id: str, event_id: str) -> Optional[CalendarEvent]:
    r = await db.execute(
        select(CalendarEvent).where(
            CalendarEvent.id == event_id,
            CalendarEvent.school_id == school_id,
        )
    )
    return r.scalar_one_or_none()


async def create_event(
    db: AsyncSession, school_id: str, created_by: UUID, data: CalendarEventCreate
) -> CalendarEvent:
    obj = CalendarEvent(
        id=uuid.uuid4(),
        school_id=school_id,
        created_by=created_by,
        **data.model_dump(),
    )
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def update_event(
    db: AsyncSession, school_id: str, event_id: str, data: CalendarEventUpdate
) -> Optional[CalendarEvent]:
    vals = {k: v for k, v in data.model_dump(exclude_none=True).items()}
    if vals:
        # Remove audience_filter if present (JSONB unsupported on MSSQL in some contexts)
        vals.pop("audience_filter", None)
        vals["updated_at"] = datetime.now(timezone.utc)
        await db.execute(
            update(CalendarEvent)
            .where(CalendarEvent.id == event_id, CalendarEvent.school_id == school_id)
            .values(**vals)
            .execution_options(synchronize_session="fetch")
        )
        await db.flush()
    return await get_event(db, school_id, event_id)


async def delete_event(db: AsyncSession, school_id: str, event_id: str) -> bool:
    obj = await get_event(db, school_id, event_id)
    if not obj:
        return False
    await db.delete(obj)
    return True

