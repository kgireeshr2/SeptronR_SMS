from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_school_id, permission_required
from app.db.session import get_db
from app.models.auth import User
from app.models.attendance import SessionType, StudentAttendance
from app.repositories.attendance_repository import AttendanceRepository
from app.schemas.phase7 import (
    AttendanceMarkRequest,
    AttendanceReportParams,
    AttendanceUpdateRequest,
    SectionAttendanceSummary,
    StudentAttendanceSummary,
)
from app.services.attendance_service import AttendanceService

router = APIRouter()


@router.get("/section/{section_id}", response_model=SectionAttendanceSummary)
async def get_section_attendance(
    section_id: str,
    date_: date = Query(..., alias="date"),
    session: SessionType = Query(SessionType.full_day),
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("attendance", "view")),
    db: AsyncSession = Depends(get_db),
):
    attendance_session = await AttendanceRepository.get_section_session(db, school_id, section_id, date_, session)
    if not attendance_session:
        return SectionAttendanceSummary(
            section_id=section_id,
            date=date_,
            session=session,
            total=0,
            present=0,
            absent=0,
            late=0,
            half_day=0,
            leave=0,
            attendance_pct=0.0,
            entries=[],
        )

    entries = await AttendanceRepository.get_session_entries(db, school_id, str(attendance_session.id))
    present = sum(1 for e in entries if getattr(e["status"], "value", e["status"]) == "present")
    absent = sum(1 for e in entries if getattr(e["status"], "value", e["status"]) == "absent")
    late = sum(1 for e in entries if getattr(e["status"], "value", e["status"]) == "late")
    half_day = sum(1 for e in entries if getattr(e["status"], "value", e["status"]) == "half_day")
    leave = sum(1 for e in entries if getattr(e["status"], "value", e["status"]) == "leave")
    total = len(entries)
    pct = round(((present + late + (half_day * 0.5)) / total * 100), 2) if total else 0.0

    from app.schemas.phase7 import AttendanceRecord

    return SectionAttendanceSummary(
        section_id=section_id,
        date=date_,
        session=session,
        total=total,
        present=present,
        absent=absent,
        late=late,
        half_day=half_day,
        leave=leave,
        attendance_pct=pct,
        entries=[
            AttendanceRecord(
                id=e["id"],
                student_id=e["student_id"],
                student_name=e["student_name"],
                admission_number=e["admission_number"],
                date=date_,
                status=e["status"],
                session=session,
                remarks=e.get("remarks"),
                marked_at=e.get("marked_at"),
            )
            for e in entries
        ],
    )


@router.post("/section/{section_id}", response_model=SectionAttendanceSummary)
async def mark_section_attendance(
    section_id: str,
    payload: AttendanceMarkRequest,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("attendance", "mark")),
    db: AsyncSession = Depends(get_db),
):
    if payload.section_id != section_id:
        raise HTTPException(status_code=400, detail="Path section_id must match payload section_id")

    service = AttendanceService(db)
    try:
        summary = await service.mark_section_attendance(school_id, payload, str(current_user.id))
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))

    # Notify parents of students marked absent.
    try:
        absent_ids = [
            str(e.student_id) for e in payload.entries
            if getattr(e.status, "value", e.status) == "absent"
        ]
        if absent_ids:
            from app.services.notifications.notify import notify_event
            notify_event(
                school_id, "attendance_absent", audience="student_parents", student_ids=absent_ids,
                default_channels=["in_app", "sms", "whatsapp"],
                title="Absence Alert",
                body="Dear Parent, your ward was marked ABSENT today. "
                     "Please contact the school if this is unexpected.",
                link="/attendance",
            )
    except Exception:
        pass
    return summary


@router.put("/{attendance_id}", response_model=dict)
async def update_single_record(
    attendance_id: str,
    payload: AttendanceUpdateRequest,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("attendance", "mark")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(StudentAttendance).where(
            StudentAttendance.id == attendance_id,
            StudentAttendance.school_id == school_id,
        )
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    row.status = payload.status
    row.remarks = payload.remarks
    await db.flush()

    return {"message": "Attendance record updated", "id": attendance_id}


@router.get("/student/{student_id}", response_model=StudentAttendanceSummary)
async def get_student_attendance_summary(
    student_id: str,
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("attendance", "view")),
    db: AsyncSession = Depends(get_db),
):
    service = AttendanceService(db)
    return await service.get_student_summary(school_id, student_id, from_date, to_date)


@router.get("/low-attendance", response_model=List[StudentAttendanceSummary])
async def get_low_attendance(
    academic_year_id: str = Query(..., alias="year_id"),
    threshold: float = Query(75.0),
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("attendance", "report")),
    db: AsyncSession = Depends(get_db),
):
    rows = await AttendanceRepository.get_low_attendance(
        db,
        school_id,
        academic_year_id,
        threshold,
        from_date=from_date,
        to_date=to_date,
    )
    return [StudentAttendanceSummary(**row) for row in rows]


@router.get("/report", response_model=List[StudentAttendanceSummary])
async def get_attendance_report(
    academic_year_id: str,
    from_date: date,
    to_date: date,
    section_id: str | None = None,
    class_id: str | None = None,
    student_id: str | None = None,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("attendance", "report")),
    db: AsyncSession = Depends(get_db),
):
    service = AttendanceService(db)
    params = AttendanceReportParams(
        academic_year_id=academic_year_id,
        from_date=from_date,
        to_date=to_date,
        section_id=section_id,
        class_id=class_id,
        student_id=student_id,
    )
    return await service.get_attendance_report(school_id, params)


@router.get("/export")
async def export_attendance(
    academic_year_id: str,
    from_date: date,
    to_date: date,
    section_id: str | None = None,
    class_id: str | None = None,
    student_id: str | None = None,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("attendance", "export")),
    db: AsyncSession = Depends(get_db),
):
    service = AttendanceService(db)
    params = AttendanceReportParams(
        academic_year_id=academic_year_id,
        from_date=from_date,
        to_date=to_date,
        section_id=section_id,
        class_id=class_id,
        student_id=student_id,
    )
    blob = await service.export_report_excel(school_id, params)
    filename = f"attendance_report_{date.today().isoformat()}.xlsx"
    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    return StreamingResponse(
        iter([blob]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


@router.get("/section/{section_id}/monthly-sheet")
async def monthly_sheet(
    section_id: str,
    academic_year_id: str,
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2000, le=2100),
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("attendance", "export")),
    db: AsyncSession = Depends(get_db),
):
    service = AttendanceService(db)
    pdf_data = await service.generate_monthly_sheet_pdf(
        school_id=school_id,
        section_id=section_id,
        academic_year_id=academic_year_id,
        month=month,
        year=year,
    )
    return Response(
        content=pdf_data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="attendance_{section_id}_{year}_{month}.pdf"'},
    )

