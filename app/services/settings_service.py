from uuid import UUID
from typing import Optional, Dict, Any, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.settings_repository import SettingsRepository
from app.models.foundation import SchoolSetting


class SettingsService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SettingsRepository(db)

    async def get_category(
        self, school_id: UUID, category: Optional[str] = None
    ) -> Dict[str, str]:
        return await self.repo.get_as_dict(school_id, category)

    async def get_all_grouped(self, school_id: UUID) -> Dict[str, Dict[str, str]]:
        items = await self.repo.get_all(school_id)
        grouped: Dict[str, Dict[str, str]] = {}
        for item in items:
            grouped.setdefault(item.category, {})[item.key] = item.value
        return grouped

    async def save_category(
        self,
        school_id: UUID,
        category: str,
        data: Dict[str, Any],
        updated_by: Optional[UUID] = None,
    ) -> Dict[str, str]:
        await self.repo.bulk_upsert(school_id, category, data, updated_by)
        return await self.repo.get_as_dict(school_id, category)

