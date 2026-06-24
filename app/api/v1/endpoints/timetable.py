from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import permission_required
from app.db.session import get_db
from app.repositories.class_repository import SectionRepository
from app.repositories.subject_repository import SubjectRepository
from app.repositories.timetable_repository import TimetableRepository
from app.schemas.phase4 import TimetableBulkUpsertRequest, TimetableEntryCreate
from app.services.timetable_service import TimetableService
from app.utils.response import ok

router = APIRouter(prefix="/timetable", tags=["Timetable"])


def _school_id_from_request(request: Request) -> str:
    school_id = (
        getattr(request.state, "school_id", None)
        or request.headers.get("X-School-Id")
        or request.query_params.get("school_id")
    )
    if not school_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="School context not found")
    return str(school_id)


@router.get("/section/{section_id}", dependencies=[Depends(permission_required("timetable", "view"))])
async def get_section_timetable(
    section_id: str,
    request: Request,
    academic_year_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    school_id = _school_id_from_request(request)
    grid = await TimetableRepository(db).get_grid_for_section(section_id, academic_year_id, school_id)
    return ok(grid, "Timetable grid")


@router.put("/section/{section_id}/slot", dependencies=[Depends(permission_required("timetable", "update"))])
async def upsert_slot(
    section_id: str,
    data: TimetableEntryCreate,
    request: Request,
    academic_year_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    school_id = _school_id_from_request(request)
    service = TimetableService(TimetableRepository(db), SectionRepository(db), SubjectRepository(db))
    entry = await service.upsert_timetable_entry(
        section_id,
        academic_year_id,
        school_id,
        {
            "subject_id": data.subject_id,
            "teacher_id": data.teacher_id,
            "day_of_week": data.day_of_week,
            "period_number": data.period_number,
            "start_time": data.start_time,
            "end_time": data.end_time,
        },
    )
    return ok(entry, "Timetable slot saved")


@router.delete("/{timetable_id}", dependencies=[Depends(permission_required("timetable", "delete"))])
async def delete_slot(timetable_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    school_id = _school_id_from_request(request)
    await TimetableRepository(db).delete_entry(timetable_id, school_id)
    return ok(None, "Timetable slot deleted")


@router.post("/section/{section_id}/bulk", dependencies=[Depends(permission_required("timetable", "update"))])
async def bulk_upsert(
    section_id: str,
    payload: TimetableBulkUpsertRequest,
    request: Request,
    academic_year_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    school_id = _school_id_from_request(request)
    service = TimetableService(TimetableRepository(db), SectionRepository(db), SubjectRepository(db))
    count = 0
    for entry in payload.entries:
        await service.upsert_timetable_entry(
            section_id,
            academic_year_id,
            school_id,
            {
                "subject_id": entry.subject_id,
                "teacher_id": entry.teacher_id,
                "day_of_week": entry.day_of_week,
                "period_number": entry.period_number,
                "start_time": entry.start_time,
                "end_time": entry.end_time,
            },
        )
        count += 1
    return ok({"updated": count}, "Timetable bulk upsert complete")


@router.get("/teacher/{teacher_id}", dependencies=[Depends(permission_required("timetable", "view"))])
async def get_teacher_schedule(
    teacher_id: str,
    request: Request,
    academic_year_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    school_id = _school_id_from_request(request)
    schedule = await TimetableRepository(db).get_teacher_schedule(teacher_id, academic_year_id, school_id)
    return ok(schedule, "Teacher timetable")


@router.get("/section/{section_id}/export", dependencies=[Depends(permission_required("timetable", "view"))])
async def export_section_timetable(
    section_id: str,
    request: Request,
    academic_year_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    school_id = _school_id_from_request(request)
    service = TimetableService(TimetableRepository(db), SectionRepository(db), SubjectRepository(db))
    pdf_data = await service.get_timetable_pdf(section_id, academic_year_id, school_id)
    return Response(
        content=pdf_data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="timetable_{section_id}.pdf"'},
    )


@router.post("/section/{section_id}/import", dependencies=[Depends(permission_required("timetable", "create"))])
async def import_section_timetable(
    section_id: str,
    request: Request,
    academic_year_id: str = Query(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    school_id = _school_id_from_request(request)
    service = TimetableService(TimetableRepository(db), SectionRepository(db), SubjectRepository(db))
    result = await service.import_timetable_from_csv(section_id, academic_year_id, school_id, file)
    return ok(result, "Timetable import complete")

