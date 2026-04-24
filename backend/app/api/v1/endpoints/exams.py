"""
API Endpoints — Phase 9: Exam Management
Exam types, grading scales, exams, marks, results, publish, templates.
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_school_id, permission_required
from app.db.session import get_db
from app.models.auth import User
from app.repositories.exam_repository import ExamRepository
from app.schemas.phase9 import (
    AdmitCardConfigCreate,
    AdmitCardConfigResponse,
    AdmitCardConfigUpdate,
    ClassResultResponse,
    ExamBulkCreate,
    ExamCreate,
    ExamMarkResponse,
    ExamResponse,
    ExamTypeCreate,
    ExamTypeResponse,
    ExamTypeUpdate,
    ExamUpdate,
    GradingScaleResponse,
    GradingScaleUpsert,
    MarkEntryRequest,
    ReportCardTemplateCreate,
    ReportCardTemplateResponse,
    ResultPublishRequest,
    ResultPublishResponse,
)
from app.services.exam_service import ExamService

exam_types_router = APIRouter(prefix="/exam-types", tags=["exam-types"])
grading_router = APIRouter(prefix="/grading-scales", tags=["grading-scales"])
exams_router = APIRouter(prefix="/exams", tags=["exams"])
rc_templates_router = APIRouter(prefix="/report-card-templates", tags=["report-card-templates"])
admit_config_router = APIRouter(prefix="/admit-card-configs", tags=["admit-card-configs"])

# ── Exam Types ────────────────────────────────────────────────────────────────

@exam_types_router.get("", response_model=list[ExamTypeResponse])
async def list_exam_types(
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("exams", "view")),
    db: AsyncSession = Depends(get_db),
):
    return await ExamRepository(db).list_exam_types(school_id)


@exam_types_router.post("", response_model=ExamTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_exam_type(
    payload: ExamTypeCreate,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("exams", "manage")),
    db: AsyncSession = Depends(get_db),
):
    return await ExamRepository(db).create_exam_type(school_id, payload.model_dump())


@exam_types_router.put("/{exam_type_id}", response_model=ExamTypeResponse)
async def update_exam_type(
    exam_type_id: UUID,
    payload: ExamTypeUpdate,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("exams", "manage")),
    db: AsyncSession = Depends(get_db),
):
    repo = ExamRepository(db)
    obj = await repo.get_exam_type(school_id, str(exam_type_id))
    if not obj:
        raise HTTPException(status_code=404, detail="Exam type not found")
    return await repo.update_exam_type(obj, payload.model_dump(exclude_unset=True))


@exam_types_router.delete("/{exam_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exam_type(
    exam_type_id: UUID,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("exams", "manage")),
    db: AsyncSession = Depends(get_db),
):
    repo = ExamRepository(db)
    obj = await repo.get_exam_type(school_id, str(exam_type_id))
    if not obj:
        raise HTTPException(status_code=404, detail="Exam type not found")
    await repo.delete_exam_type(obj)


# ── Grading Scales ────────────────────────────────────────────────────────────

@grading_router.get("", response_model=Optional[GradingScaleResponse])
async def get_grading_scale(
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("exams", "view")),
    db: AsyncSession = Depends(get_db),
):
    return await ExamRepository(db).get_grading_scale(school_id)


@grading_router.put("", response_model=GradingScaleResponse)
async def upsert_grading_scale(
    payload: GradingScaleUpsert,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("exams", "manage")),
    db: AsyncSession = Depends(get_db),
):
    data = payload.model_dump()
    # Serialize GradeRange objects to dicts
    data["ranges"] = [r.model_dump() for r in payload.ranges]
    return await ExamRepository(db).upsert_grading_scale(school_id, data)


# ── Exams ─────────────────────────────────────────────────────────────────────

@exams_router.get("", response_model=list[ExamResponse])
async def list_exams(
    year_id: Optional[UUID] = Query(None),
    class_id: Optional[UUID] = Query(None),
    exam_type_id: Optional[UUID] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("exams", "view")),
    db: AsyncSession = Depends(get_db),
):
    return await ExamRepository(db).list_exams(
        school_id,
        year_id=str(year_id) if year_id else None,
        class_id=str(class_id) if class_id else None,
        exam_type_id=str(exam_type_id) if exam_type_id else None,
        status=status_filter,
    )


@exams_router.post("", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
async def create_exam(
    payload: ExamCreate,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("exams", "create")),
    db: AsyncSession = Depends(get_db),
):
    data = payload.model_dump()
    data["created_by"] = str(current_user.id)
    return await ExamRepository(db).create_exam(school_id, data)


@exams_router.post("/bulk", response_model=list[ExamResponse], status_code=status.HTTP_201_CREATED)
async def bulk_create_exams(
    payload: ExamBulkCreate,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("exams", "create")),
    db: AsyncSession = Depends(get_db),
):
    exams_data = []
    for entry in payload.subjects:
        exams_data.append(
            {
                "academic_year_id": str(payload.academic_year_id),
                "term_id": str(payload.term_id) if payload.term_id else None,
                "exam_type_id": str(payload.exam_type_id),
                "class_id": str(payload.class_id),
                "subject_id": str(entry.subject_id),
                "name": f"{payload.exam_name_prefix} - {entry.subject_id}",
                "exam_date": entry.exam_date,
                "start_time": entry.start_time,
                "end_time": entry.end_time,
                "full_marks": entry.full_marks,
                "pass_marks": entry.pass_marks,
                "created_by": str(current_user.id),
            }
        )
    return await ExamRepository(db).bulk_create_exams(school_id, exams_data)


@exams_router.get("/{exam_id}", response_model=ExamResponse)
async def get_exam(
    exam_id: UUID,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("exams", "view")),
    db: AsyncSession = Depends(get_db),
):
    obj = await ExamRepository(db).get_exam(school_id, str(exam_id))
    if not obj:
        raise HTTPException(status_code=404, detail="Exam not found")
    return obj


@exams_router.put("/{exam_id}", response_model=ExamResponse)
async def update_exam(
    exam_id: UUID,
    payload: ExamUpdate,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("exams", "manage")),
    db: AsyncSession = Depends(get_db),
):
    repo = ExamRepository(db)
    obj = await repo.get_exam(school_id, str(exam_id))
    if not obj:
        raise HTTPException(status_code=404, detail="Exam not found")
    return await repo.update_exam(obj, payload.model_dump(exclude_unset=True))


@exams_router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exam(
    exam_id: UUID,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("exams", "manage")),
    db: AsyncSession = Depends(get_db),
):
    repo = ExamRepository(db)
    obj = await repo.get_exam(school_id, str(exam_id))
    if not obj:
        raise HTTPException(status_code=404, detail="Exam not found")
    await repo.delete_exam(obj)


# ── Marks ─────────────────────────────────────────────────────────────────────

@exams_router.get("/{exam_id}/marks", response_model=list[ExamMarkResponse])
async def get_exam_marks(
    exam_id: UUID,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("exams", "view")),
    db: AsyncSession = Depends(get_db),
):
    repo = ExamRepository(db)
    exam = await repo.get_exam(school_id, str(exam_id))
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    marks = await repo.get_marks_for_exam(str(exam_id))
    grading_scale = await repo.get_grading_scale(school_id)
    students = {str(s.id): s for s in await repo.get_students_for_exam(exam)}

    svc = ExamService(db)
    results = []
    for m in marks:
        student = students.get(str(m.student_id))
        computed = svc._compute_result(
            float(m.marks_obtained) if m.marks_obtained else None,
            exam.pass_marks, exam.full_marks,
            m.is_absent, m.is_exempted, grading_scale,
        )
        results.append(ExamMarkResponse(
            student_id=m.student_id,
            student_name=f"{student.first_name} {student.last_name}" if student else "Unknown",
            admission_number=student.admission_number if student else "",
            roll_number=None,
            marks_obtained=float(m.marks_obtained) if m.marks_obtained else None,
            full_marks=exam.full_marks,
            pass_marks=exam.pass_marks,
            grade=computed.get("grade"),
            grade_point=computed.get("grade_point"),
            percentage=computed.get("percentage"),
            is_absent=m.is_absent,
            is_exempted=m.is_exempted,
            result=computed["result"],
        ))
    return results


@exams_router.post("/{exam_id}/marks", response_model=list[ExamMarkResponse])
async def enter_marks(
    exam_id: UUID,
    payload: MarkEntryRequest,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("exams", "manage")),
    db: AsyncSession = Depends(get_db),
):
    svc = ExamService(db)
    return await svc.enter_marks(school_id, str(exam_id), payload.entries, str(current_user.id))


# ── Results & Publishing ───────────────────────────────────────────────────────

@exams_router.get("/{exam_id}/results/{class_id}", response_model=ClassResultResponse)
async def get_class_results(
    exam_id: UUID,
    class_id: UUID,
    year_id: UUID = Query(...),
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("exams", "view")),
    db: AsyncSession = Depends(get_db),
):
    # exam_id here is used as exam_type_id grouping context
    exam = await ExamRepository(db).get_exam(school_id, str(exam_id))
    exam_type_id = str(exam.exam_type_id) if exam else str(exam_id)
    svc = ExamService(db)
    return await svc.get_class_results(school_id, exam_type_id, str(class_id), str(year_id))


@exams_router.post("/publish", response_model=ResultPublishResponse)
async def publish_results(
    payload: ResultPublishRequest,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("exams", "publish")),
    db: AsyncSession = Depends(get_db),
):
    svc = ExamService(db)
    return await svc.publish_results(school_id, payload)


# ── Report Card Templates ──────────────────────────────────────────────────────

@rc_templates_router.get("", response_model=list[ReportCardTemplateResponse])
async def list_rc_templates(
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("exams", "view")),
    db: AsyncSession = Depends(get_db),
):
    return await ExamRepository(db).list_report_card_templates(school_id)


@rc_templates_router.post("", response_model=ReportCardTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_rc_template(
    payload: ReportCardTemplateCreate,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("exams", "manage")),
    db: AsyncSession = Depends(get_db),
):
    return await ExamRepository(db).create_report_card_template(school_id, payload.model_dump())


@rc_templates_router.put("/{template_id}", response_model=ReportCardTemplateResponse)
async def update_rc_template(
    template_id: UUID,
    payload: ReportCardTemplateCreate,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("exams", "manage")),
    db: AsyncSession = Depends(get_db),
):
    repo = ExamRepository(db)
    obj = await repo.get_report_card_template(school_id, str(template_id))
    if not obj:
        raise HTTPException(status_code=404, detail="Template not found")
    return await repo.update_report_card_template(obj, payload.model_dump(exclude_unset=True))


# ── Admit Card Configs ──────────────────────────────────────────────────────────

@admit_config_router.get("", response_model=list[AdmitCardConfigResponse])
async def list_admit_configs(
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("exams", "view")),
    db: AsyncSession = Depends(get_db),
):
    return await ExamRepository(db).list_admit_card_configs(school_id)


@admit_config_router.post("", response_model=AdmitCardConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_admit_config(
    payload: AdmitCardConfigCreate,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("exams", "manage")),
    db: AsyncSession = Depends(get_db),
):
    return await ExamRepository(db).create_admit_card_config(school_id, payload.model_dump())


@admit_config_router.put("/{config_id}", response_model=AdmitCardConfigResponse)
async def update_admit_config(
    config_id: UUID,
    payload: AdmitCardConfigUpdate,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("exams", "manage")),
    db: AsyncSession = Depends(get_db),
):
    repo = ExamRepository(db)
    obj = await repo.get_admit_card_config(school_id, str(config_id))
    if not obj:
        raise HTTPException(status_code=404, detail="Admit card config not found")
    return await repo.update_admit_card_config(obj, payload.model_dump(exclude_unset=True))


# ── Report Card PDF Generation ────────────────────────────────────────────────

@exams_router.get("/{exam_id}/report-card/{student_id}/pdf")
async def download_report_card_pdf(
    exam_id: UUID,
    student_id: UUID,
    year_id: UUID = Query(...),
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("exams", "view")),
    db: AsyncSession = Depends(get_db),
):
    """Download a student's report card as PDF."""
    from fastapi.responses import Response as FastAPIResponse
    from app.services.pdf_service import generate_report_card_pdf
    from app.repositories.school_repository import SchoolRepository
    from app.repositories.student_repository import StudentRepository
    from sqlalchemy import select, text

    repo = ExamRepository(db)
    exam = await repo.get_exam(school_id, str(exam_id))
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    exam_type_id = str(exam.exam_type_id)

    # Get class result for this exam type & student's class
    svc = ExamService(db)

    # Get student info
    student_repo = StudentRepository(db)
    student = await student_repo.get_detail(student_id, school_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Find class from latest enrollment
    class_name = "—"
    section_name = "—"
    roll_number = None
    if hasattr(student, "enrollments") and student.enrollments:
        latest_enroll = sorted(student.enrollments, key=lambda e: str(e.academic_year_id))[-1]
        class_name = getattr(latest_enroll, "class_name", "—") or "—"
        section_name = getattr(latest_enroll, "section_name", "—") or "—"
        roll_number = getattr(latest_enroll, "roll_number", None)

    # Get grading scale
    grading_scale = await repo.get_grading_scale(school_id)

    # Get all exams for this exam_type + student's class
    exams = await repo.list_exams(
        school_id,
        year_id=str(year_id),
        exam_type_id=exam_type_id,
    )

    subject_results = []
    total_full = 0
    total_obtained = 0
    all_pass = True

    for ex in exams:
        marks_result = await db.execute(
            text(
                "SELECT marks_obtained, is_absent, is_exempted FROM student_marks "
                "WHERE exam_id = :exam_id AND student_id = :student_id"
            ),
            {"exam_id": str(ex.id), "student_id": str(student_id)},
        )
        mark_row = marks_result.fetchone()
        m_obtained = None
        is_absent = False
        is_exempted = False
        if mark_row:
            m_obtained = float(mark_row[0]) if mark_row[0] is not None else None
            is_absent = bool(mark_row[1])
            is_exempted = bool(mark_row[2])

        computed = svc._compute_result(
            m_obtained, ex.pass_marks, ex.full_marks, is_absent, is_exempted, grading_scale
        )

        subject_name_row = await db.execute(
            text("SELECT name FROM subjects WHERE id = :sid"),
            {"sid": str(ex.subject_id)},
        )
        subject_name = subject_name_row.scalar() or str(ex.subject_id)

        subject_results.append(
            {
                "subject_name": subject_name,
                "full_marks": ex.full_marks,
                "pass_marks": ex.pass_marks,
                "marks_obtained": m_obtained,
                "grade": computed.get("grade"),
                "percentage": computed.get("percentage"),
                "result": computed.get("result", "Pending"),
                "is_absent": is_absent,
            }
        )
        if not is_absent and not is_exempted and m_obtained is not None:
            total_full += ex.full_marks
            total_obtained += m_obtained
            if m_obtained < ex.pass_marks:
                all_pass = False

    overall_pct = round((total_obtained / total_full) * 100, 2) if total_full > 0 else 0.0
    overall_grade = None
    if grading_scale:
        g = repo.calculate_grade(grading_scale, overall_pct)
        overall_grade = g.get("grade")

    exam_type_row = await repo.get_exam_type(school_id, exam_type_id)
    exam_type_name = exam_type_row.name if exam_type_row else "Examination"

    school_repo = SchoolRepository(db)
    school = await school_repo.get_by_id(school_id)
    school_name = school.name if school else "School"
    school_address = getattr(school, "address", None)

    pdf_payload = {
        "school_name": school_name,
        "school_address": school_address,
        "academic_year_name": str(year_id),
        "exam_type_name": exam_type_name,
        "student_name": f"{student.first_name} {student.last_name}",
        "admission_number": student.admission_number,
        "class_name": class_name,
        "section_name": section_name,
        "roll_number": roll_number,
        "date_of_birth": str(student.date_of_birth) if student.date_of_birth else None,
        "subjects": subject_results,
        "total_marks": total_full,
        "total_obtained": int(total_obtained),
        "overall_percentage": overall_pct,
        "overall_grade": overall_grade,
        "result": "Pass" if all_pass and total_full > 0 else ("Fail" if total_full > 0 else "Pending"),
    }

    pdf_bytes = generate_report_card_pdf(pdf_payload)
    filename = f"report_card_{student.admission_number}_{exam_type_name.replace(' ', '_')}.pdf"

    return FastAPIResponse(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Admit Card PDF Generation (per student or bulk per class) ─────────────────

@admit_config_router.get("/{exam_type_id}/admit-cards/pdf")
async def download_admit_cards_pdf(
    exam_type_id: UUID,
    class_id: UUID = Query(...),
    year_id: UUID = Query(...),
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("exams", "view")),
    db: AsyncSession = Depends(get_db),
):
    """Download admit cards PDF for all students in a class for an exam type."""
    from fastapi.responses import Response as FastAPIResponse
    from app.services.pdf_service import generate_admit_card_pdf
    from app.repositories.school_repository import SchoolRepository
    from sqlalchemy import text, select

    repo = ExamRepository(db)

    # Get admit card config
    configs = await repo.list_admit_card_configs(school_id)
    config = next((c for c in configs if str(c.exam_type_id) == str(exam_type_id)), None)

    # Get exams for this type + class
    exams = await repo.list_exams(
        school_id,
        year_id=str(year_id),
        class_id=str(class_id),
        exam_type_id=str(exam_type_id),
    )
    if not exams:
        raise HTTPException(status_code=404, detail="No exams found for this type and class")

    # Get students enrolled in this class
    students_result = await db.execute(
        text(
            """
            SELECT s.id, s.first_name, s.last_name, s.admission_number,
                   sec.name AS section_name, se.roll_number,
                   cl.name AS class_name
            FROM students s
            JOIN student_enrollments se ON se.student_id = s.id
            JOIN classes cl ON cl.id = se.class_id
            JOIN sections sec ON sec.id = se.section_id
            WHERE se.class_id = :class_id
              AND se.academic_year_id = :year_id
              AND s.school_id = :school_id
              AND s.is_active = 1
            ORDER BY s.first_name
            """
        ),
        {"class_id": str(class_id), "year_id": str(year_id), "school_id": school_id},
    )
    students = students_result.fetchall()

    # Get subjects info
    exam_subjects = []
    for ex in exams:
        sub_result = await db.execute(
            text("SELECT name FROM subjects WHERE id = :sid"),
            {"sid": str(ex.subject_id)},
        )
        subject_name = sub_result.scalar() or str(ex.subject_id)
        exam_subjects.append(
            {
                "subject_name": subject_name,
                "exam_date": str(ex.exam_date) if ex.exam_date else None,
                "start_time": str(ex.start_time) if ex.start_time else None,
                "end_time": str(ex.end_time) if ex.end_time else None,
                "venue": getattr(ex, "venue", None),
            }
        )

    student_data = []
    for row in students:
        student_data.append(
            {
                "student_name": f"{row[1]} {row[2]}",
                "admission_number": row[3],
                "class_name": row[6],
                "section_name": row[4],
                "roll_number": row[5],
                "exams": exam_subjects,
            }
        )

    exam_type_row = await repo.get_exam_type(school_id, str(exam_type_id))
    exam_type_name = exam_type_row.name if exam_type_row else "Examination"

    school_repo = SchoolRepository(db)
    school = await school_repo.get_by_id(school_id)
    school_name = school.name if school else "School"
    school_address = getattr(school, "address", None)

    admit_config = {
        "school_name": school_name,
        "school_address": school_address,
        "exam_type_name": exam_type_name,
        "instructions": getattr(config, "instructions", None) if config else None,
    }

    pdf_bytes = generate_admit_card_pdf(student_data, admit_config)
    filename = f"admit_cards_{exam_type_name.replace(' ', '_')}.pdf"

    return FastAPIResponse(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


