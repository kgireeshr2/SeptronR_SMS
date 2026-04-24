from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.auth import User
from app.repositories.super_admin_repository import SuperAdminRepository
from app.schemas.phase21 import (
    SubscriptionPlanCreate,
    SubscriptionPlanResponse,
    SchoolSubscriptionCreate,
    SchoolSubscriptionResponse,
    FeatureFlagSet,
    FeatureFlagResponse,
    ImpersonateRequest,
    ImpersonationLogResponse,
    SchoolOverview,
)

superadmin_router = APIRouter(prefix="/superadmin", tags=["Super Admin"])


def require_super_admin(current_user: User = Depends(get_current_user)) -> User:
    if not getattr(current_user, "is_super_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super admin access required.")
    return current_user


# ---- Schools ----

@superadmin_router.get("/schools", response_model=List[SchoolOverview])
async def list_schools(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_super_admin),
) -> list:
    repo = SuperAdminRepository(db)
    return await repo.list_schools()


@superadmin_router.patch("/schools/{school_id}/toggle-active")
async def toggle_school(
    school_id: UUID,
    is_active: bool,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_super_admin),
):
    repo = SuperAdminRepository(db)
    school = await repo.toggle_school_active(school_id, is_active)
    if not school:
        raise HTTPException(404, "School not found")
    return school


# ---- Subscription Plans ----

@superadmin_router.get("/plans", response_model=List[SubscriptionPlanResponse])
async def list_plans(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_super_admin),
):
    return await SuperAdminRepository(db).list_plans()


@superadmin_router.post("/plans", response_model=SubscriptionPlanResponse, status_code=201)
async def create_plan(
    data: SubscriptionPlanCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_super_admin),
):
    return await SuperAdminRepository(db).create_plan(data.model_dump())


@superadmin_router.put("/plans/{plan_id}", response_model=SubscriptionPlanResponse)
async def update_plan(
    plan_id: UUID,
    data: SubscriptionPlanCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_super_admin),
):
    repo = SuperAdminRepository(db)
    plan = await repo.update_plan(plan_id, data.model_dump(exclude_unset=True))
    if not plan:
        raise HTTPException(404, "Plan not found")
    return plan


# ---- Subscriptions ----

@superadmin_router.get("/subscriptions", response_model=List[SchoolSubscriptionResponse])
async def list_subscriptions(
    school_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_super_admin),
):
    return await SuperAdminRepository(db).list_subscriptions(school_id)


@superadmin_router.post("/subscriptions", response_model=SchoolSubscriptionResponse, status_code=201)
async def create_subscription(
    data: SchoolSubscriptionCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_super_admin),
):
    return await SuperAdminRepository(db).create_subscription(data.model_dump())


@superadmin_router.patch("/subscriptions/{sub_id}/deactivate")
async def deactivate_subscription(
    sub_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_super_admin),
):
    result = await SuperAdminRepository(db).deactivate_subscription(sub_id)
    if not result:
        raise HTTPException(404, "Subscription not found")
    return result


# ---- Feature Flags ----

@superadmin_router.get("/schools/{school_id}/features", response_model=List[FeatureFlagResponse])
async def get_features(
    school_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_super_admin),
):
    return await SuperAdminRepository(db).get_flags(school_id)


@superadmin_router.put("/schools/{school_id}/features")
async def set_feature(
    school_id: UUID,
    data: FeatureFlagSet,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_super_admin),
):
    return await SuperAdminRepository(db).set_flag(school_id, data.feature_key, data.is_enabled)


# ---- Impersonation ----

@superadmin_router.post("/impersonate", response_model=ImpersonationLogResponse, status_code=201)
async def start_impersonation(
    req: ImpersonateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return await SuperAdminRepository(db).create_impersonation_log(
        current_user.id, req.school_id, req.user_id
    )


@superadmin_router.patch("/impersonate/{log_id}/end")
async def end_impersonation(
    log_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_super_admin),
):
    result = await SuperAdminRepository(db).end_impersonation(log_id)
    if not result:
        raise HTTPException(404, "Impersonation log not found")
    return result

