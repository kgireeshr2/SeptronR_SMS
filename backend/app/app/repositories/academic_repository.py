from typing import Optional

from sqlalchemy import and_, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.academic import AcademicTerm, AcademicYear


class AcademicYearRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_school(self, school_id: str) -> list[AcademicYear]:
        result = await self.db.execute(
            select(AcademicYear)
            .where(AcademicYear.school_id == school_id)
            .order_by(AcademicYear.start_date.desc())
        )
        return list(result.scalars().all())

    async def get_current(self, school_id: str) -> Optional[AcademicYear]:
        result = await self.db.execute(
            select(AcademicYear).where(AcademicYear.school_id == school_id, AcademicYear.is_current == True)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, year_id: str) -> Optional[AcademicYear]:
        result = await self.db.execute(select(AcademicYear).where(AcademicYear.id == year_id))
        return result.scalar_one_or_none()

    async def create(self, school_id: str, data: dict) -> AcademicYear:
        model = AcademicYear(school_id=school_id, **data)
        self.db.add(model)
        await self.db.flush()
        await self.db.refresh(model)
        return model

    async def update(self, year_id: str, data: dict) -> Optional[AcademicYear]:
        await self.db.execute(update(AcademicYear).where(AcademicYear.id == year_id).values(**data))
        await self.db.flush()
        return await self.get_by_id(year_id)

    async def set_current(self, school_id: str, year_id: str) -> Optional[AcademicYear]:
        await self.db.execute(
            update(AcademicYear).where(AcademicYear.school_id == school_id).values(is_current=False)
        )
        await self.db.execute(
            update(AcademicYear).where(AcademicYear.id == year_id, AcademicYear.school_id == school_id).values(is_current=True)
        )
        await self.db.flush()
        return await self.get_by_id(year_id)

    async def lock(self, year_id: str) -> Optional[AcademicYear]:
        await self.db.execute(update(AcademicYear).where(AcademicYear.id == year_id).values(is_locked=True))
        await self.db.flush()
        return await self.get_by_id(year_id)

    async def unlock(self, year_id: str) -> Optional[AcademicYear]:
        await self.db.execute(update(AcademicYear).where(AcademicYear.id == year_id).values(is_locked=False))
        await self.db.flush()
        return await self.get_by_id(year_id)

    async def delete(self, year_id: str) -> None:
        await self.db.execute(delete(AcademicYear).where(AcademicYear.id == year_id))
        await self.db.flush()


class AcademicTermRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_year(self, year_id: str) -> list[AcademicTerm]:
        result = await self.db.execute(
            select(AcademicTerm).where(AcademicTerm.academic_year_id == year_id).order_by(AcademicTerm.start_date.asc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, term_id: str) -> Optional[AcademicTerm]:
        result = await self.db.execute(select(AcademicTerm).where(AcademicTerm.id == term_id))
        return result.scalar_one_or_none()

    async def create(self, year_id: str, school_id: str, data: dict) -> AcademicTerm:
        term = AcademicTerm(academic_year_id=year_id, school_id=school_id, **data)
        self.db.add(term)
        await self.db.flush()
        await self.db.refresh(term)
        return term

    async def update(self, term_id: str, data: dict) -> Optional[AcademicTerm]:
        await self.db.execute(update(AcademicTerm).where(AcademicTerm.id == term_id).values(**data))
        await self.db.flush()
        return await self.get_by_id(term_id)

    async def set_current(self, year_id: str, term_id: str) -> Optional[AcademicTerm]:
        await self.db.execute(update(AcademicTerm).where(AcademicTerm.academic_year_id == year_id).values(is_current=False))
        await self.db.execute(
            update(AcademicTerm).where(AcademicTerm.id == term_id, AcademicTerm.academic_year_id == year_id).values(is_current=True)
        )
        await self.db.flush()
        return await self.get_by_id(term_id)

    async def delete(self, year_id: str, term_id: str) -> None:
        await self.db.execute(
            delete(AcademicTerm).where(and_(AcademicTerm.academic_year_id == year_id, AcademicTerm.id == term_id))
        )
        await self.db.flush()

