from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.foundation import SchoolProfile, SchoolSetting
from app.models.school import School


class SchoolRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, school_id: str) -> Optional[School]:
        result = await self.db.execute(select(School).where(School.id == school_id))
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[School]:
        result = await self.db.execute(select(School).where(School.slug == slug))
        return result.scalar_one_or_none()

    async def create(self, data: dict) -> School:
        school = School(**data)
        self.db.add(school)
        await self.db.flush()
        await self.db.refresh(school)
        return school

    async def update(self, school_id: str, data: dict) -> Optional[School]:
        await self.db.execute(update(School).where(School.id == school_id).values(**data))
        await self.db.flush()
        return await self.get_by_id(school_id)

    async def list_all(self, page: int = 1, page_size: int = 20) -> tuple[list[School], int]:
        count_result = await self.db.execute(select(func.count()).select_from(School))
        total = count_result.scalar_one()
        result = await self.db.execute(
            select(School).order_by(School.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        )
        return list(result.scalars().all()), total


class SchoolProfileRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_school(self, school_id: str) -> Optional[SchoolProfile]:
        result = await self.db.execute(select(SchoolProfile).where(SchoolProfile.school_id == school_id))
        return result.scalar_one_or_none()

    async def upsert(self, school_id: str, data: dict) -> SchoolProfile:
        profile = await self.get_by_school(school_id)
        if profile:
            for key, value in data.items():
                setattr(profile, key, value)
            await self.db.flush()
            await self.db.refresh(profile)
            return profile

        profile = SchoolProfile(school_id=school_id, **data)
        self.db.add(profile)
        await self.db.flush()
        await self.db.refresh(profile)
        return profile


class SchoolSettingsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, school_id: str) -> list[SchoolSetting]:
        result = await self.db.execute(
            select(SchoolSetting).where(SchoolSetting.school_id == school_id).order_by(SchoolSetting.category, SchoolSetting.key)
        )
        return list(result.scalars().all())

    async def get_by_category(self, school_id: str, category: str) -> list[SchoolSetting]:
        result = await self.db.execute(
            select(SchoolSetting)
            .where(SchoolSetting.school_id == school_id, SchoolSetting.category == category)
            .order_by(SchoolSetting.key)
        )
        return list(result.scalars().all())

    async def get_value(self, school_id: str, key: str) -> Optional[str]:
        result = await self.db.execute(
            select(SchoolSetting).where(SchoolSetting.school_id == school_id, SchoolSetting.key == key)
        )
        row = result.scalar_one_or_none()
        return row.value if row else None

    async def upsert(self, school_id: str, key: str, value: str, updated_by: Optional[str]) -> SchoolSetting:
        result = await self.db.execute(
            select(SchoolSetting).where(SchoolSetting.school_id == school_id, SchoolSetting.key == key)
        )
        setting = result.scalar_one_or_none()
        if setting:
            setting.value = value
            setting.updated_by = updated_by
            await self.db.flush()
            return setting

        setting = SchoolSetting(
            school_id=school_id,
            key=key,
            value=value,
            category="general",
            data_type="string",
            updated_by=updated_by,
        )
        self.db.add(setting)
        await self.db.flush()
        return setting

    async def bulk_upsert(self, school_id: str, settings: dict, updated_by: Optional[str]) -> list[SchoolSetting]:
        saved = []
        for key, value in settings.items():
            item = await self.upsert(school_id, key, str(value), updated_by)
            saved.append(item)
        return saved

