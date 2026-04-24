"""API Endpoints — Phase 16: Calendar Events."""
from __future__ import annotations
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_school_id, get_current_user, permission_required
from app.schemas.phase16 import CalendarEventCreate, CalendarEventUpdate, CalendarEventResponse
import app.services.calendar_service as svc

calendar_router = APIRouter(prefix="/calendar", tags=["calendar"])


@calendar_router.get("", response_model=List[CalendarEventResponse])
async def list_events(
    event_type: Optional[str] = None,
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
):
    return await svc.list_events(db, school_id, event_type, from_dt, to_dt)


@calendar_router.post("", response_model=CalendarEventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    data: CalendarEventCreate,
    school_id: str = Depends(get_school_id),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(permission_required("calendar", "write")),
):
    try:
        return await svc.create_event(db, school_id, current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@calendar_router.put("/{event_id}", response_model=CalendarEventResponse)
async def update_event(
    event_id: UUID,
    data: CalendarEventUpdate,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(permission_required("calendar", "write")),
):
    try:
        obj = await svc.update_event(db, school_id, str(event_id), data)
        return obj
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@calendar_router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: UUID,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(permission_required("calendar", "delete")),
):
    ok = await svc.delete_event(db, school_id, str(event_id))
    if not ok:
        raise HTTPException(status_code=404, detail="Event not found")

