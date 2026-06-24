from fastapi import HTTPException, status

from app.repositories.academic_repository import AcademicTermRepository, AcademicYearRepository


class AcademicService:
    def __init__(self, year_repo: AcademicYearRepository, term_repo: AcademicTermRepository):
        self.year_repo = year_repo
        self.term_repo = term_repo

    async def create_academic_year(self, school_id: str, data: dict):
        years = await self.year_repo.list_by_school(school_id)
        for year in years:
            overlaps = not (data["end_date"] < year.start_date or data["start_date"] > year.end_date)
            if overlaps:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Academic year dates overlap with an existing year",
                )
        return await self.year_repo.create(school_id, data)

    async def update_academic_year(self, school_id: str, year_id: str, data: dict):
        year = await self.year_repo.get_by_id(year_id)
        if not year or str(year.school_id) != str(school_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Academic year not found")
        if year.is_locked:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Locked year cannot be edited")
        return await self.year_repo.update(year_id, data)

    async def set_current_year(self, school_id: str, year_id: str):
        year = await self.year_repo.get_by_id(year_id)
        if not year or str(year.school_id) != str(school_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Academic year not found")
        return await self.year_repo.set_current(school_id, year_id)

    async def lock_year(self, school_id: str, year_id: str):
        year = await self.year_repo.get_by_id(year_id)
        if not year or str(year.school_id) != str(school_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Academic year not found")
        return await self.year_repo.lock(year_id)

    async def unlock_year(self, school_id: str, year_id: str):
        year = await self.year_repo.get_by_id(year_id)
        if not year or str(year.school_id) != str(school_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Academic year not found")
        return await self.year_repo.unlock(year_id)

