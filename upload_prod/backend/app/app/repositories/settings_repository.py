from uuid import UUID
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.foundation import SchoolSetting


class SettingsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, school_id: UUID, category: Optional[str] = None) -> List[SchoolSetting]:
        q = select(SchoolSetting).where(SchoolSetting.school_id == school_id)
        if category:
            q = q.where(SchoolSetting.category == category)
        result = await self.db.execute(q.order_by(SchoolSetting.category, SchoolSetting.key))
        return list(result.scalars().all())

    async def get_by_key(self, school_id: UUID, key: str) -> Optional[SchoolSetting]:
        q = select(SchoolSetting).where(
            and_(SchoolSetting.school_id == school_id, SchoolSetting.key == key)
        )
        result = await self.db.execute(q)
        return result.scalar_one_or_none()

    async def upsert(
        self,
        school_id: UUID,
        category: str,
        key: str,
        value: str,
        data_type: str = "string",
        is_public: bool = False,
        updated_by: Optional[UUID] = None,
    ) -> SchoolSetting:
        existing = await self.get_by_key(school_id, key)
        if existing:
            existing.value = value
            existing.data_type = data_type
            existing.is_public = is_public
            if updated_by:
                existing.updated_by = updated_by
            await self.db.flush()
            return existing
        setting = SchoolSetting(
            school_id=school_id,
            category=category,
            key=key,
            value=value,
            data_type=data_type,
            is_public=is_public,
            updated_by=updated_by,
        )
        self.db.add(setting)
        await self.db.flush()
        await self.db.refresh(setting)
        return setting

    async def bulk_upsert(
        self,
        school_id: UUID,
        category: str,
        entries: Dict[str, Any],
        updated_by: Optional[UUID] = None,
    ) -> List[SchoolSetting]:
        results = []
        for key, value in entries.items():
            s = await self.upsert(
                school_id=school_id,
                category=category,
                key=key,
                value=str(value),
                updated_by=updated_by,
            )
            results.append(s)
        await self.db.commit()
        return results

    async def get_as_dict(
        self, school_id: UUID, category: Optional[str] = None
    ) -> Dict[str, str]:
        items = await self.get_all(school_id, category)
        return {s.key: s.value for s in items}

