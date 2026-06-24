from collections import defaultdict
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admissions import AdmissionForm, AdmissionFormConfig


class AdmissionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_config(self, school_id: str, year_id: str) -> Optional[AdmissionFormConfig]:
        result = await self.db.execute(
            select(AdmissionFormConfig).where(
                AdmissionFormConfig.school_id == school_id,
                AdmissionFormConfig.academic_year_id == year_id,
            )
        )
        return result.scalar_one_or_none()

    async def upsert_config(self, school_id: str, data: dict) -> AdmissionFormConfig:
        year_id = str(data["academic_year_id"])
        existing = await self.get_config(school_id, year_id)
        payload = dict(data)
        payload["academic_year_id"] = year_id

        if existing:
            for key, value in payload.items():
                setattr(existing, key, value)
            await self.db.flush()
            await self.db.refresh(existing)
            return existing

        model = AdmissionFormConfig(school_id=school_id, **payload)
        self.db.add(model)
        await self.db.flush()
        await self.db.refresh(model)
        return model

    async def list_forms(self, school_id: str, filters: dict, page: int, page_size: int) -> tuple[list[AdmissionForm], int]:
        stmt = select(AdmissionForm).where(AdmissionForm.school_id == school_id)
        if filters.get("status"):
            stmt = stmt.where(AdmissionForm.status == filters["status"])
        if filters.get("academic_year_id"):
            stmt = stmt.where(AdmissionForm.academic_year_id == filters["academic_year_id"])
        if filters.get("search"):
            query = f"%{filters['search']}%"
            stmt = stmt.where(
                AdmissionForm.applicant_name.ilike(query) | AdmissionForm.parent_phone.ilike(query)
            )

        count_result = await self.db.execute(select(func.count()).select_from(stmt.subquery()))
        total = count_result.scalar_one()
        result = await self.db.execute(
            stmt.order_by(AdmissionForm.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        )
        return list(result.scalars().all()), total

    async def get_form_by_id(self, form_id: str) -> Optional[AdmissionForm]:
        result = await self.db.execute(select(AdmissionForm).where(AdmissionForm.id == form_id))
        return result.scalar_one_or_none()

    async def get_form_by_reference(self, school_id: str, ref: str) -> Optional[AdmissionForm]:
        result = await self.db.execute(
            select(AdmissionForm).where(AdmissionForm.school_id == school_id, AdmissionForm.reference_number == ref)
        )
        return result.scalar_one_or_none()

    async def get_form_by_reference_global(self, ref: str) -> Optional[AdmissionForm]:
        result = await self.db.execute(select(AdmissionForm).where(AdmissionForm.reference_number == ref))
        return result.scalar_one_or_none()

    async def create_form(self, data: dict) -> AdmissionForm:
        model = AdmissionForm(**data)
        self.db.add(model)
        await self.db.flush()
        await self.db.refresh(model)
        return model

    async def update_status(self, form_id: str, data: dict) -> Optional[AdmissionForm]:
        await self.db.execute(update(AdmissionForm).where(AdmissionForm.id == form_id).values(**data))
        await self.db.flush()
        return await self.get_form_by_id(form_id)

    async def count_by_status(self, school_id: str, year_id: str) -> dict:
        result = await self.db.execute(
            select(AdmissionForm.status, func.count())
            .where(AdmissionForm.school_id == school_id, AdmissionForm.academic_year_id == year_id)
            .group_by(AdmissionForm.status)
        )
        stats = defaultdict(int)
        for status, count in result.all():
            stats[str(status)] = count
        return dict(stats)

