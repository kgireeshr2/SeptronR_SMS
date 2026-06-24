import csv
import io
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, permission_required
from app.core.rate_limit import rate_limit, verify_captcha
from app.db.session import get_db
from app.repositories.academic_repository import AcademicYearRepository
from app.repositories.admission_repository import AdmissionRepository
from app.repositories.school_repository import SchoolRepository
from app.schemas.phase3 import AdmissionBulkApproveRequest, AdmissionFormConfigCreate, AdmissionReviewRequest
from app.services.admission_service import AdmissionService
from app.utils.response import ok

router = APIRouter(prefix="/admissions", tags=["Admissions"])


def _school_id_from_request(request: Request) -> str:
    school_id = (
        getattr(request.state, "school_id", None)
        or request.headers.get("X-School-Id")
        or request.query_params.get("school_id")
    )
    if not school_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="School context not found")
    return str(school_id)


@router.get("/public-config/{school_slug}", response_model=dict)
async def get_public_config(
    school_slug: str,
    year_id: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    school = await SchoolRepository(db).get_by_slug(school_slug)
    if not school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="School not found")

    if not year_id:
        current = await AcademicYearRepository(db).get_current(str(school.id))
        if not current:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No current academic year")
        year_id = str(current.id)

    config = await AdmissionRepository(db).get_config(str(school.id), str(year_id))
    if not config or not config.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admission form is not active")
    return ok(config, "Public admission config")


@router.get("/config", response_model=dict, dependencies=[Depends(permission_required("admissions", "view"))])
async def get_config(
    year_id: Optional[str] = Query(default=None),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    school_id = _school_id_from_request(request)
    repo = AdmissionRepository(db)
    if not year_id:
        current = await AcademicYearRepository(db).get_current(school_id)
        if not current:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No current academic year")
        year_id = str(current.id)
    config = await repo.get_config(school_id, year_id)
    return ok(config, "Admission config")


@router.put("/config", response_model=dict, dependencies=[Depends(permission_required("admissions", "update"))])
async def upsert_config(
    data: AdmissionFormConfigCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    school_id = _school_id_from_request(request)
    config = await AdmissionRepository(db).upsert_config(school_id, data.model_dump())
    return ok(config, "Admission config saved")


@router.post("/apply", response_model=dict, dependencies=[Depends(rate_limit("admission_apply", 10, 3600))])
async def submit_application(
    school_slug: str = Form(...),
    academic_year_id: UUID = Form(...),
    applicant_name: str = Form(...),
    date_of_birth: date = Form(...),
    gender: Optional[str] = Form(default=None),
    applying_for_class_id: Optional[UUID] = Form(default=None),
    parent_name: str = Form(...),
    parent_phone: str = Form(...),
    parent_email: Optional[str] = Form(default=None),
    address: Optional[str] = Form(default=None),
    previous_school: Optional[str] = Form(default=None),
    # Government IDs — student
    student_aadhaar: Optional[str] = Form(default=None),
    student_pan: Optional[str] = Form(default=None),
    student_apaar: Optional[str] = Form(default=None),
    # Government IDs — parent/guardian
    parent_aadhaar: Optional[str] = Form(default=None),
    parent_pan: Optional[str] = Form(default=None),
    parent_ration_card: Optional[str] = Form(default=None),
    # Father details
    father_name: Optional[str] = Form(default=None),
    father_aadhaar: Optional[str] = Form(default=None),
    father_pan: Optional[str] = Form(default=None),
    father_ration_card: Optional[str] = Form(default=None),
    # Mother details
    mother_name: Optional[str] = Form(default=None),
    mother_aadhaar: Optional[str] = Form(default=None),
    mother_pan: Optional[str] = Form(default=None),
    mother_ration_card: Optional[str] = Form(default=None),
    # Guardian details
    guardian_name: Optional[str] = Form(default=None),
    guardian_aadhaar: Optional[str] = Form(default=None),
    guardian_pan: Optional[str] = Form(default=None),
    guardian_ration_card: Optional[str] = Form(default=None),
    captcha_token: Optional[str] = Form(default=None),
    files: list[UploadFile] = File(default=[]),
    db: AsyncSession = Depends(get_db),
):
    # Anti-abuse: verify CAPTCHA when configured (no-op otherwise); per-IP rate limit
    # is enforced by the route dependency above.
    if not await verify_captcha(captcha_token):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CAPTCHA verification failed")
    service = AdmissionService(AdmissionRepository(db), SchoolRepository(db))
    # Build metadata dict from provided IDs
    metadata: dict = {}
    for key, val in {
        "student_aadhaar": student_aadhaar, "student_pan": student_pan, "student_apaar": student_apaar,
        "parent_aadhaar": parent_aadhaar, "parent_pan": parent_pan, "parent_ration_card": parent_ration_card,
        "father_name": father_name, "father_aadhaar": father_aadhaar, "father_pan": father_pan, "father_ration_card": father_ration_card,
        "mother_name": mother_name, "mother_aadhaar": mother_aadhaar, "mother_pan": mother_pan, "mother_ration_card": mother_ration_card,
        "guardian_name": guardian_name, "guardian_aadhaar": guardian_aadhaar, "guardian_pan": guardian_pan, "guardian_ration_card": guardian_ration_card,
    }.items():
        if val:
            metadata[key] = val

    form = await service.submit_application(
        {
            "school_slug": school_slug,
            "academic_year_id": academic_year_id,
            "applicant_name": applicant_name,
            "date_of_birth": date_of_birth,
            "gender": gender,
            "applying_for_class_id": str(applying_for_class_id) if applying_for_class_id else None,
            "parent_name": parent_name,
            "parent_phone": parent_phone,
            "parent_email": parent_email,
            "address": address,
            "previous_school": previous_school,
            "metadata": metadata or None,
        },
        files,
    )
    return ok(form, "Admission form submitted")


@router.get("/check/{reference}", response_model=dict)
async def check_status(reference: str, db: AsyncSession = Depends(get_db)):
    form = await AdmissionRepository(db).get_form_by_reference_global(reference)
    if not form:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return ok(
        {
            "reference_number": form.reference_number,
            "status": str(form.status),
            "applicant_name": form.applicant_name,
            "submitted_at": form.submitted_at,
            "reviewed_at": form.reviewed_at,
            "remarks": form.remarks,
        },
        "Application status",
    )


@router.get("", response_model=dict, dependencies=[Depends(permission_required("admissions", "view"))])
async def list_forms(
    request: Request,
    db: AsyncSession = Depends(get_db),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    academic_year_id: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    school_id = _school_id_from_request(request)
    rows, total = await AdmissionRepository(db).list_forms(
        school_id,
        {"status": status_filter, "academic_year_id": academic_year_id, "search": search},
        page,
        page_size,
    )
    return ok({"items": rows, "total": total, "page": page, "page_size": page_size}, "Admission forms")


@router.get("/stats", response_model=dict, dependencies=[Depends(permission_required("admissions", "view"))])
async def admission_stats(
    year_id: str = Query(...),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    school_id = _school_id_from_request(request)
    stats = await AdmissionRepository(db).count_by_status(school_id, year_id)
    return ok(stats, "Admission stats")


@router.get("/{form_id}", response_model=dict, dependencies=[Depends(permission_required("admissions", "view"))])
async def get_form(form_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    school_id = _school_id_from_request(request)
    form = await AdmissionRepository(db).get_form_by_id(form_id)
    if not form or str(form.school_id) != school_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admission form not found")
    return ok(form, "Admission form")


@router.put("/{form_id}/review", response_model=dict, dependencies=[Depends(permission_required("admissions", "approve"))])
async def review_form(
    form_id: str,
    data: AdmissionReviewRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    school_id = _school_id_from_request(request)
    form = await AdmissionRepository(db).get_form_by_id(form_id)
    if not form or str(form.school_id) != school_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admission form not found")
    service = AdmissionService(AdmissionRepository(db), SchoolRepository(db))
    updated = await service.review_application(form_id, str(current_user.id), data.model_dump())
    return ok(updated, "Admission review updated")


@router.post("/bulk-approve", response_model=dict, dependencies=[Depends(permission_required("admissions", "approve"))])
async def bulk_approve(
    data: AdmissionBulkApproveRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = AdmissionService(AdmissionRepository(db), SchoolRepository(db))
    count = await service.bulk_approve(data.form_ids, str(current_user.id), data.class_section_map)
    return ok({"approved_count": count}, "Bulk approval completed")


@router.get("/export", response_model=dict, dependencies=[Depends(permission_required("admissions", "view"))])
async def export_forms(
    request: Request,
    db: AsyncSession = Depends(get_db),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    academic_year_id: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
):
    school_id = _school_id_from_request(request)
    rows, _ = await AdmissionRepository(db).list_forms(
        school_id,
        {"status": status_filter, "academic_year_id": academic_year_id, "search": search},
        1,
        5000,
    )
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Reference Number",
        "Applicant Name",
        "Status",
        "Parent Name",
        "Parent Phone",
        "Submitted At",
    ])
    for row in rows:
        writer.writerow([
            row.reference_number,
            row.applicant_name,
            str(row.status),
            row.parent_name or "",
            row.parent_phone or "",
            row.submitted_at.isoformat() if row.submitted_at else "",
        ])

    output.seek(0)
    filename = f"admissions_export_{date.today().isoformat()}.csv"
    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers=headers)

