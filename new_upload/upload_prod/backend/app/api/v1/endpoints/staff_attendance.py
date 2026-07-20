from datetime import date
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_school_id, permission_required
from app.db.session import get_db
from app.models.auth import User
from app.repositories.attendance_repository import StaffAttendanceRepository
from app.schemas.phase7 import StaffAttendanceMarkRequest, StaffAttendanceRecord
from app.services.attendance_service import AttendanceService

router = APIRouter()


@router.get("", response_model=List[StaffAttendanceRecord])
async def list_staff_attendance(
    date_: date = Query(..., alias="date"),
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("staff_attendance", "view")),
    db: AsyncSession = Depends(get_db),
):
    rows = await StaffAttendanceRepository.list_for_date(db, school_id, date_)
    return [StaffAttendanceRecord(**row) for row in rows]


@router.post("", response_model=dict)
async def mark_staff_attendance(
    payload: List[StaffAttendanceMarkRequest],
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("staff_attendance", "mark")),
    db: AsyncSession = Depends(get_db),
):
    service = AttendanceService(db)
    affected = await service.mark_staff_attendance(school_id, payload)
    return {"message": "Staff attendance updated", "affected": affected}


@router.post("/biometric-import", response_model=dict)
async def import_biometric(
    file: UploadFile = File(...),
    date_: date = Query(..., alias="date"),
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("staff_attendance", "mark")),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    raw = await file.read()
    service = AttendanceService(db)
    result = await service.import_biometric_csv(
        school_id=school_id,
        date_=date_,
        file_content=raw,
    )
    return result


@router.get("/report", response_model=dict)
async def monthly_report(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2000, le=2100),
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("staff_attendance", "report")),
    db: AsyncSession = Depends(get_db),
):
    rows = await StaffAttendanceRepository.monthly_summary(db, school_id, month, year)
    return {
        "month": month,
        "year": year,
        "rows": rows,
    }

