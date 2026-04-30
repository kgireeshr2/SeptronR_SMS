from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import permission_required
from app.db.session import get_db
from app.repositories.subject_repository import SubjectRepository
from app.schemas.phase4 import SubjectCreate, SubjectUpdate
from app.utils.response import ok

router = APIRouter(prefix="/subjects", tags=["Subjects"])


def _school_id_from_request(request: Request) -> str:
    school_id = (
        getattr(request.state, "school_id", None)
        or request.headers.get("X-School-Id")
        or request.query_params.get("school_id")
    )
    if not school_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="School context not found")
    return str(school_id)


@router.get("", dependencies=[Depends(permission_required("subjects", "view"))])
async def list_subjects(request: Request, db: AsyncSession = Depends(get_db)):
    subjects = await SubjectRepository(db).list_by_school(_school_id_from_request(request), active_only=False)
    payload = [
        {"id": str(s.id), "school_id": str(s.school_id), "name": s.name, "code": s.code,
         "is_elective": s.is_elective, "full_marks": s.full_marks, "pass_marks": s.pass_marks, "is_active": s.is_active}
        for s in subjects
    ]
    return ok(payload, "Subjects")


@router.post("", dependencies=[Depends(permission_required("subjects", "create"))])
async def create_subject(data: SubjectCreate, request: Request, db: AsyncSession = Depends(get_db)):
    subject = await SubjectRepository(db).create(_school_id_from_request(request), data.model_dump())
    payload = {"id": str(subject.id), "school_id": str(subject.school_id), "name": subject.name, "code": subject.code,
               "is_elective": subject.is_elective, "full_marks": subject.full_marks, "pass_marks": subject.pass_marks, "is_active": subject.is_active}
    return ok(payload, "Subject created")


@router.get("/{subject_id}", dependencies=[Depends(permission_required("subjects", "view"))])
async def get_subject(subject_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    school_id = _school_id_from_request(request)
    subject = await SubjectRepository(db).get_by_id(subject_id)
    if not subject or str(subject.school_id) != school_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    payload = {"id": str(subject.id), "school_id": str(subject.school_id), "name": subject.name, "code": subject.code,
               "is_elective": subject.is_elective, "full_marks": subject.full_marks, "pass_marks": subject.pass_marks, "is_active": subject.is_active}
    return ok(payload, "Subject")


@router.put("/{subject_id}", dependencies=[Depends(permission_required("subjects", "update"))])
async def update_subject(subject_id: str, data: SubjectUpdate, request: Request, db: AsyncSession = Depends(get_db)):
    school_id = _school_id_from_request(request)
    repo = SubjectRepository(db)
    subject = await repo.get_by_id(subject_id)
    if not subject or str(subject.school_id) != school_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    updated = await repo.update(subject_id, data.model_dump(exclude_none=True))
    payload = {"id": str(updated.id), "school_id": str(updated.school_id), "name": updated.name, "code": updated.code,
               "is_elective": updated.is_elective, "full_marks": updated.full_marks, "pass_marks": updated.pass_marks, "is_active": updated.is_active}
    return ok(payload, "Subject updated")


@router.delete("/{subject_id}", dependencies=[Depends(permission_required("subjects", "delete"))])
async def delete_subject(subject_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    school_id = _school_id_from_request(request)
    repo = SubjectRepository(db)
    subject = await repo.get_by_id(subject_id)
    if not subject or str(subject.school_id) != school_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    await repo.soft_delete(subject_id)
    return ok(None, "Subject deleted")

