from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_school_id, permission_required
from app.db.session import get_db
from app.models.auth import User
from app.repositories.attendance_repository import AttendanceRepository
from app.schemas.phase7 import HolidayCreate, HolidayResponse, HolidayUpdate

router = APIRouter()


@router.get("", response_model=List[HolidayResponse])
async def list_holidays(
    year_id: Optional[str] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("holidays", "view")),
    db: AsyncSession = Depends(get_db),
):
    rows = await AttendanceRepository.get_holidays(
        db,
        school_id,
        academic_year_id=year_id,
        from_date=from_date,
        to_date=to_date,
    )
    return rows


@router.post("", response_model=HolidayResponse, status_code=status.HTTP_201_CREATED)
async def create_holiday(
    payload: HolidayCreate,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("holidays", "manage")),
    db: AsyncSession = Depends(get_db),
):
    existing = await AttendanceRepository.get_holiday_by_date(db, school_id, payload.date)
    if existing:
        raise HTTPException(status_code=400, detail="Holiday already exists on this date")
    row = await AttendanceRepository.create_holiday(db, school_id, payload.model_dump())
    return row


@router.put("/{holiday_id}", response_model=HolidayResponse)
async def update_holiday(
    holiday_id: str,
    payload: HolidayUpdate,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("holidays", "manage")),
    db: AsyncSession = Depends(get_db),
):
    row = await AttendanceRepository.get_holiday_by_id(db, school_id, holiday_id)
    if not row:
        raise HTTPException(status_code=404, detail="Holiday not found")
    updated = await AttendanceRepository.update_holiday(db, row, payload.model_dump(exclude_unset=True))
    return updated


@router.delete("/{holiday_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_holiday(
    holiday_id: str,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("holidays", "manage")),
    db: AsyncSession = Depends(get_db),
):
    row = await AttendanceRepository.get_holiday_by_id(db, school_id, holiday_id)
    if not row:
        raise HTTPException(status_code=404, detail="Holiday not found")
    await AttendanceRepository.delete_holiday(db, row)


@router.post("/bulk", response_model=dict)
async def bulk_holiday_create(
    payload: List[HolidayCreate],
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("holidays", "manage")),
    db: AsyncSession = Depends(get_db),
):
    created = 0
    skipped = 0
    for item in payload:
        existing = await AttendanceRepository.get_holiday_by_date(db, school_id, item.date)
        if existing:
            skipped += 1
            continue
        await AttendanceRepository.create_holiday(db, school_id, item.model_dump())
        created += 1
    return {"created": created, "skipped": skipped}

