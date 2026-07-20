from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, permission_required
from app.db.session import get_db
from app.repositories.academic_repository import AcademicTermRepository, AcademicYearRepository
from app.schemas.phase3 import AcademicTermCreate, AcademicTermUpdate, AcademicYearCreate, AcademicYearUpdate
from app.services.academic_service import AcademicService
from app.utils.response import ok

router = APIRouter(prefix="/academic-years", tags=["Academic Years"])


def _school_id_from_request(request: Request) -> str:
    school_id = (
        getattr(request.state, "school_id", None)
        or request.headers.get("X-School-Id")
        or request.query_params.get("school_id")
    )
    if not school_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="School context not found")
    return str(school_id)


@router.get("", response_model=dict, dependencies=[Depends(permission_required("academic_years", "view"))])
async def list_years(request: Request, db: AsyncSession = Depends(get_db)):
    years = await AcademicYearRepository(db).list_by_school(_school_id_from_request(request))
    return ok(years, "Academic years")


@router.post("", response_model=dict, dependencies=[Depends(permission_required("academic_years", "create"))])
async def create_year(data: AcademicYearCreate, request: Request, db: AsyncSession = Depends(get_db)):
    school_id = _school_id_from_request(request)
    service = AcademicService(AcademicYearRepository(db), AcademicTermRepository(db))
    year = await service.create_academic_year(school_id, data.model_dump())
    return ok(year, "Academic year created")


@router.get("/{year_id}", response_model=dict, dependencies=[Depends(permission_required("academic_years", "view"))])
async def get_year(year_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    school_id = _school_id_from_request(request)
    repo = AcademicYearRepository(db)
    year = await repo.get_by_id(year_id, school_id=school_id)
    if not year or str(year.school_id) != school_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Academic year not found")
    terms = await AcademicTermRepository(db).list_by_year(year_id)
    payload = {
        "id": str(year.id),
        "school_id": str(year.school_id),
        "name": year.name,
        "start_date": year.start_date,
        "end_date": year.end_date,
        "is_current": year.is_current,
        "is_locked": year.is_locked,
        "created_at": year.created_at,
        "terms": terms,
    }
    return ok(payload, "Academic year")


@router.put("/{year_id}", response_model=dict, dependencies=[Depends(permission_required("academic_years", "update"))])
async def update_year(year_id: str, data: AcademicYearUpdate, request: Request, db: AsyncSession = Depends(get_db)):
    school_id = _school_id_from_request(request)
    service = AcademicService(AcademicYearRepository(db), AcademicTermRepository(db))
    updated = await service.update_academic_year(school_id, year_id, data.model_dump(exclude_none=True))
    return ok(updated, "Academic year updated")


@router.delete("/{year_id}", response_model=dict, dependencies=[Depends(permission_required("academic_years", "delete"))])
async def delete_year(year_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    school_id = _school_id_from_request(request)
    repo = AcademicYearRepository(db)
    year = await repo.get_by_id(year_id, school_id=school_id)
    if not year or str(year.school_id) != school_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Academic year not found")
    await repo.delete(year_id)
    return ok(None, "Academic year deleted")


@router.post("/{year_id}/set-current", response_model=dict, dependencies=[Depends(permission_required("academic_years", "update"))])
async def set_current_year(year_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    school_id = _school_id_from_request(request)
    service = AcademicService(AcademicYearRepository(db), AcademicTermRepository(db))
    year = await service.set_current_year(school_id, year_id)
    return ok(year, "Current academic year updated")


@router.post("/{year_id}/lock", response_model=dict, dependencies=[Depends(permission_required("academic_years", "update"))])
async def lock_year(year_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    school_id = _school_id_from_request(request)
    service = AcademicService(AcademicYearRepository(db), AcademicTermRepository(db))
    year = await service.lock_year(school_id, year_id)
    return ok(year, "Academic year locked")


@router.post("/{year_id}/unlock", response_model=dict, dependencies=[Depends(permission_required("academic_years", "update"))])
async def unlock_year(year_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    school_id = _school_id_from_request(request)
    service = AcademicService(AcademicYearRepository(db), AcademicTermRepository(db))
    year = await service.unlock_year(school_id, year_id)
    return ok(year, "Academic year unlocked")


@router.get("/{year_id}/terms", response_model=dict, dependencies=[Depends(permission_required("academic_years", "view"))])
async def list_terms(year_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    school_id = _school_id_from_request(request)
    year = await AcademicYearRepository(db).get_by_id(year_id, school_id=school_id)
    if not year or str(year.school_id) != school_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Academic year not found")
    terms = await AcademicTermRepository(db).list_by_year(year_id)
    return ok(terms, "Academic terms")


@router.post("/{year_id}/terms", response_model=dict, dependencies=[Depends(permission_required("academic_years", "create"))])
async def create_term(year_id: str, data: AcademicTermCreate, request: Request, db: AsyncSession = Depends(get_db)):
    school_id = _school_id_from_request(request)
    year = await AcademicYearRepository(db).get_by_id(year_id, school_id=school_id)
    if not year or str(year.school_id) != school_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Academic year not found")
    term = await AcademicTermRepository(db).create(year_id, school_id, data.model_dump())
    return ok(term, "Academic term created")


@router.put("/{year_id}/terms/{term_id}", response_model=dict, dependencies=[Depends(permission_required("academic_years", "update"))])
async def update_term(year_id: str, term_id: str, data: AcademicTermUpdate, request: Request, db: AsyncSession = Depends(get_db)):
    school_id = _school_id_from_request(request)
    year = await AcademicYearRepository(db).get_by_id(year_id, school_id=school_id)
    if not year or str(year.school_id) != school_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Academic year not found")
    term = await AcademicTermRepository(db).update(term_id, data.model_dump(exclude_none=True))
    return ok(term, "Academic term updated")


@router.post("/{year_id}/terms/{term_id}/set-current", response_model=dict, dependencies=[Depends(permission_required("academic_years", "update"))])
async def set_current_term(year_id: str, term_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    school_id = _school_id_from_request(request)
    year = await AcademicYearRepository(db).get_by_id(year_id, school_id=school_id)
    if not year or str(year.school_id) != school_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Academic year not found")
    term = await AcademicTermRepository(db).set_current(year_id, term_id)
    return ok(term, "Current term updated")


@router.delete("/{year_id}/terms/{term_id}", response_model=dict, dependencies=[Depends(permission_required("academic_years", "delete"))])
async def delete_term(year_id: str, term_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    school_id = _school_id_from_request(request)
    year = await AcademicYearRepository(db).get_by_id(year_id, school_id=school_id)
    if not year or str(year.school_id) != school_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Academic year not found")
    await AcademicTermRepository(db).delete(year_id, term_id)
    return ok(None, "Academic term deleted")

