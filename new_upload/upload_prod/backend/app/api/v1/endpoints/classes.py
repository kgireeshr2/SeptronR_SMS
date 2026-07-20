from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import permission_required
from app.db.session import get_db
from app.repositories.class_repository import ClassRepository, SectionRepository
from app.repositories.subject_repository import SubjectRepository
from app.schemas.phase4 import (
    ClassCreate,
    ClassSubjectAssign,
    ClassUpdate,
    DuplicateClassesRequest,
    SectionCreate,
    SectionUpdate,
)
from app.services.class_service import ClassService
from app.utils.response import ok

router = APIRouter(prefix="/classes", tags=["Classes"])


def _school_id_from_request(request: Request) -> str:
    school_id = (
        getattr(request.state, "school_id", None)
        or request.headers.get("X-School-Id")
        or request.query_params.get("school_id")
    )
    if not school_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="School context not found")
    return str(school_id)


@router.get("", dependencies=[Depends(permission_required("classes", "view"))])
async def list_classes(
    request: Request,
    academic_year_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    school_id = _school_id_from_request(request)
    classes = await ClassRepository(db).list_with_student_counts(school_id, academic_year_id)
    return ok(classes, "Classes")


@router.post("", dependencies=[Depends(permission_required("classes", "create"))])
async def create_class(data: ClassCreate, request: Request, db: AsyncSession = Depends(get_db)):
    from sqlalchemy.exc import IntegrityError
    school_id = _school_id_from_request(request)
    service = ClassService(ClassRepository(db), SectionRepository(db))
    try:
        class_obj = await service.create_class(
            school_id,
            str(data.academic_year_id),
            {
                "name": data.name,
                "academic_year_id": str(data.academic_year_id),
                "is_active": True,
            },
        )
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A class with this name already exists for this academic year")
    payload = {
        "id": str(class_obj.id),
        "school_id": str(class_obj.school_id),
        "academic_year_id": str(class_obj.academic_year_id),
        "name": class_obj.name,
        "is_active": class_obj.is_active,
        "created_at": class_obj.created_at,
        "student_count": 0,
        "sections": [],
    }
    return ok(payload, "Class created")


@router.get("/{class_id}", dependencies=[Depends(permission_required("classes", "view"))])
async def get_class(class_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    school_id = _school_id_from_request(request)
    class_obj = await ClassRepository(db).get_by_id(class_id, with_sections=True, school_id=school_id)
    if not class_obj or str(class_obj.school_id) != school_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    sections = await SectionRepository(db).list_with_teacher_name(class_id)
    payload = {
        "id": str(class_obj.id),
        "school_id": str(class_obj.school_id),
        "academic_year_id": str(class_obj.academic_year_id),
        "name": class_obj.name,
        "is_active": class_obj.is_active,
        "created_at": class_obj.created_at,
        "sections": sections,
        "student_count": 0,
    }
    return ok(payload, "Class")


@router.put("/{class_id}", dependencies=[Depends(permission_required("classes", "update"))])
async def update_class(class_id: str, data: ClassUpdate, request: Request, db: AsyncSession = Depends(get_db)):
    school_id = _school_id_from_request(request)
    repo = ClassRepository(db)
    class_obj = await repo.get_by_id(class_id, school_id=school_id)
    if not class_obj or str(class_obj.school_id) != school_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    updated = await repo.update(class_id, data.model_dump(exclude_none=True))
    payload = {
        "id": str(updated.id),
        "school_id": str(updated.school_id),
        "academic_year_id": str(updated.academic_year_id),
        "name": updated.name,
        "is_active": updated.is_active,
        "created_at": updated.created_at,
        "student_count": 0,
    }
    return ok(payload, "Class updated")


@router.delete("/{class_id}", dependencies=[Depends(permission_required("classes", "delete"))])
async def delete_class(class_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    school_id = _school_id_from_request(request)
    repo = ClassRepository(db)
    class_obj = await repo.get_by_id(class_id, school_id=school_id)
    if not class_obj or str(class_obj.school_id) != school_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    await repo.hard_delete(class_id)
    return ok(None, "Class deleted")


@router.get("/{class_id}/sections", dependencies=[Depends(permission_required("sections", "view"))])
async def list_sections(class_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    school_id = _school_id_from_request(request)
    class_obj = await ClassRepository(db).get_by_id(class_id, school_id=school_id)
    if not class_obj or str(class_obj.school_id) != school_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    sections = await SectionRepository(db).list_with_teacher_name(class_id)
    return ok(sections, "Sections")


@router.post("/{class_id}/sections", dependencies=[Depends(permission_required("sections", "create"))])
async def create_section(class_id: str, data: SectionCreate, request: Request, db: AsyncSession = Depends(get_db)):
    from sqlalchemy.exc import IntegrityError
    school_id = _school_id_from_request(request)
    class_obj = await ClassRepository(db).get_by_id(class_id, school_id=school_id)
    if not class_obj or str(class_obj.school_id) != school_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    try:
        section_data = data.model_dump(exclude_none=True)
        section_data["school_id"] = school_id
        section = await SectionRepository(db).create(class_id, section_data)
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Section '{data.name}' already exists in this class")
    payload = {
        "id": str(section.id),
        "class_id": str(section.class_id),
        "school_id": str(section.school_id) if section.school_id else None,
        "name": section.name,
        "capacity": section.capacity,
        "class_teacher_id": str(section.class_teacher_id) if section.class_teacher_id else None,
        "room_number": section.room_number,
        "is_active": section.is_active,
        "created_at": section.created_at,
        "student_count": 0,
    }
    return ok(payload, "Section created")


@router.put("/{class_id}/sections/{section_id}", dependencies=[Depends(permission_required("sections", "update"))])
async def update_section(
    class_id: str,
    section_id: str,
    data: SectionUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    school_id = _school_id_from_request(request)
    class_obj = await ClassRepository(db).get_by_id(class_id, school_id=school_id)
    if not class_obj or str(class_obj.school_id) != school_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    section_repo = SectionRepository(db)
    section = await section_repo.get_by_id(section_id, school_id=school_id)
    if not section or str(section.class_id) != class_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")
    updated = await section_repo.update(section_id, data.model_dump(exclude_none=True))
    payload = {
        "id": str(updated.id),
        "class_id": str(updated.class_id),
        "school_id": str(updated.school_id) if updated.school_id else None,
        "name": updated.name,
        "capacity": updated.capacity,
        "class_teacher_id": str(updated.class_teacher_id) if updated.class_teacher_id else None,
        "room_number": updated.room_number,
        "is_active": updated.is_active,
        "created_at": updated.created_at,
        "student_count": 0,
    }
    return ok(payload, "Section updated")


@router.delete("/{class_id}/sections/{section_id}", dependencies=[Depends(permission_required("sections", "delete"))])
async def delete_section(class_id: str, section_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    school_id = _school_id_from_request(request)
    class_obj = await ClassRepository(db).get_by_id(class_id, school_id=school_id)
    if not class_obj or str(class_obj.school_id) != school_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    section_repo = SectionRepository(db)
    section = await section_repo.get_by_id(section_id, school_id=school_id)
    if not section or str(section.class_id) != class_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")
    await section_repo.soft_delete(section_id)
    return ok(None, "Section deleted")


@router.get("/{class_id}/subjects", dependencies=[Depends(permission_required("classes", "view"))])
async def get_subject_assignments(class_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    school_id = _school_id_from_request(request)
    class_obj = await ClassRepository(db).get_by_id(class_id, school_id=school_id)
    if not class_obj or str(class_obj.school_id) != school_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    subjects = await SubjectRepository(db).get_subjects_for_class(class_id)
    return ok({"class_id": class_id, "subjects": subjects}, "Class subjects")


@router.post("/{class_id}/subjects", dependencies=[Depends(permission_required("classes", "update"))])
async def assign_subject_to_class(class_id: str, data: ClassSubjectAssign, request: Request, db: AsyncSession = Depends(get_db)):
    school_id = _school_id_from_request(request)
    class_repo = ClassRepository(db)
    class_obj = await class_repo.get_by_id(class_id, school_id=school_id)
    if not class_obj or str(class_obj.school_id) != school_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    subject_repo = SubjectRepository(db)
    subject = await subject_repo.get_by_id(str(data.subject_id))
    if not subject or str(subject.school_id) != school_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    record = await subject_repo.assign_to_class(class_id, str(data.subject_id), str(data.teacher_id) if data.teacher_id else None)
    rec_payload = {"id": str(record.id), "class_id": str(record.class_id), "subject_id": str(record.subject_id), "teacher_id": str(record.teacher_id) if record.teacher_id else None}
    return ok(rec_payload, "Subject assigned")


@router.put("/{class_id}/subjects/{subject_id}", dependencies=[Depends(permission_required("classes", "update"))])
async def update_subject_assignment(
    class_id: str,
    subject_id: str,
    data: ClassSubjectAssign,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    school_id = _school_id_from_request(request)
    class_obj = await ClassRepository(db).get_by_id(class_id, school_id=school_id)
    if not class_obj or str(class_obj.school_id) != school_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    record = await SubjectRepository(db).assign_to_class(class_id, subject_id, str(data.teacher_id) if data.teacher_id else None)
    rec_payload = {"id": str(record.id), "class_id": str(record.class_id), "subject_id": str(record.subject_id), "teacher_id": str(record.teacher_id) if record.teacher_id else None}
    return ok(rec_payload, "Subject assignment updated")


@router.delete("/{class_id}/subjects/{subject_id}", dependencies=[Depends(permission_required("classes", "update"))])
async def remove_subject_assignment(class_id: str, subject_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    school_id = _school_id_from_request(request)
    class_obj = await ClassRepository(db).get_by_id(class_id, school_id=school_id)
    if not class_obj or str(class_obj.school_id) != school_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    await SubjectRepository(db).remove_from_class(class_id, subject_id)
    return ok(None, "Subject removed from class")


@router.post("/duplicate-to-year", dependencies=[Depends(permission_required("classes", "update"))])
async def duplicate_to_year(data: DuplicateClassesRequest, request: Request, db: AsyncSession = Depends(get_db)):
    school_id = _school_id_from_request(request)
    service = ClassService(ClassRepository(db), SectionRepository(db))
    created = await service.duplicate_classes_for_new_year(school_id, str(data.from_year_id), str(data.to_year_id))
    return ok({"created": created}, "Classes duplicated")


@router.post("/bulk-import", dependencies=[Depends(permission_required("classes", "create"))])
async def bulk_import_classes(
    request: Request,
    academic_year_id: str = Query(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    school_id = _school_id_from_request(request)
    content = (await file.read()).decode("utf-8", errors="replace")
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if len(lines) <= 1:
        return ok({"created": 0}, "No rows imported")

    service = ClassService(ClassRepository(db), SectionRepository(db))
    created = 0
    for line in lines[1:]:
        parts = [item.strip() for item in line.split(",")]
        if not parts[0]:
            continue
        try:
            await service.create_class(
                school_id,
                academic_year_id,
                {
                    "name": parts[0],
                    "academic_year_id": academic_year_id,
                    "is_active": True,
                },
            )
            created += 1
        except HTTPException:
            continue

    return ok({"created": created}, "Bulk import completed")

