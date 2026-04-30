from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_school_id, permission_required
from app.db.session import get_db
from app.models.auth import User
from app.services.settings_service import SettingsService

settings_router = APIRouter(prefix="/settings", tags=["Settings"])


@settings_router.get("")
async def get_all_settings(
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(permission_required("settings", "view")),
):
    svc = SettingsService(db)
    return await svc.get_all_grouped(school_id)


@settings_router.get("/{category}")
async def get_settings_category(
    category: str,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(permission_required("settings", "view")),
):
    svc = SettingsService(db)
    return await svc.get_category(school_id, category)


@settings_router.put("/{category}")
async def save_settings_category(
    category: str,
    data: Dict[str, Any],
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(permission_required("settings", "edit")),
):
    svc = SettingsService(db)
    return await svc.save_category(school_id, category, data, current_user.id)

