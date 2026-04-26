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


# ---- Feature Flags (global, not per-school) ----

@superadmin_router.get("/feature-flags")
async def list_all_feature_flags(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_super_admin),
):
    """List all feature flags across all schools."""
    from sqlalchemy import select
    from app.models.super_admin import SchoolFeatureFlag
    r = await db.execute(select(SchoolFeatureFlag).order_by(SchoolFeatureFlag.school_id))
    flags = r.scalars().all()
    return [{"id": str(f.id), "school_id": str(f.school_id), "flag_key": f.feature_key, "is_enabled": f.is_enabled} for f in flags]


@superadmin_router.post("/feature-flags", status_code=201)
async def create_feature_flag(
    data: dict,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_super_admin),
):
    from app.models.super_admin import SchoolFeatureFlag
    flag = SchoolFeatureFlag(
        school_id=data.get("school_id"),
        feature_key=data.get("flag_key", data.get("feature_key", "")),
        is_enabled=data.get("is_enabled", True),
    )
    db.add(flag)
    await db.commit()
    await db.refresh(flag)
    return {"id": str(flag.id), "school_id": str(flag.school_id), "flag_key": flag.feature_key, "is_enabled": flag.is_enabled}


@superadmin_router.patch("/feature-flags/{flag_id}")
async def update_feature_flag(
    flag_id: UUID,
    data: dict,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_super_admin),
):
    from sqlalchemy import select
    from app.models.super_admin import SchoolFeatureFlag
    r = await db.execute(select(SchoolFeatureFlag).where(SchoolFeatureFlag.id == flag_id))
    flag = r.scalar_one_or_none()
    if not flag:
        raise HTTPException(404, "Feature flag not found")
    if "is_enabled" in data:
        flag.is_enabled = data["is_enabled"]
    await db.commit()
    return {"id": str(flag.id), "school_id": str(flag.school_id), "flag_key": flag.feature_key, "is_enabled": flag.is_enabled}


# ---- School Users (for impersonation) ----

@superadmin_router.get("/schools/{school_id}/users")
async def list_school_users(
    school_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_super_admin),
):
    """List users belonging to a school (for impersonation)."""
    from sqlalchemy import text
    rows = await db.execute(
        text("SELECT id, email, first_name, last_name FROM users WHERE school_id = :sid AND is_active = true ORDER BY email LIMIT 100"),
        {"sid": str(school_id)},
    )
    return [{"id": str(r["id"]), "email": r["email"], "name": f"{r['first_name'] or ''} {r['last_name'] or ''}".strip()} for r in rows.mappings().all()]


# ---- Impersonation Log List ----

@superadmin_router.get("/impersonate")
async def list_impersonation_logs(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_super_admin),
):
    from sqlalchemy import select
    from app.models.super_admin import ImpersonationLog
    r = await db.execute(select(ImpersonationLog).order_by(ImpersonationLog.started_at.desc()).limit(100))
    logs = r.scalars().all()
    return [{"id": str(l.id), "super_admin_id": str(l.super_admin_id), "school_id": str(l.impersonated_school_id), "user_id": str(l.impersonated_user_id), "started_at": l.started_at.isoformat(), "ended_at": l.ended_at.isoformat() if l.ended_at else None} for l in logs]


# ---- Direct School Impersonation (returns token) ----

@superadmin_router.post("/impersonate/{school_id}")
async def impersonate_school(
    school_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """Quick impersonation: create a token scoped to a school admin."""
    from sqlalchemy import text
    from app.core.security import create_access_token
    # Get the admin user of the target school
    row = await db.execute(
        text("SELECT id FROM users WHERE school_id = :sid AND is_active = true ORDER BY created_at LIMIT 1"),
        {"sid": str(school_id)},
    )
    admin_row = row.mappings().first()
    if not admin_row:
        raise HTTPException(404, "No active users found for this school")
    token, _ = create_access_token(subject=str(admin_row["id"]), school_id=str(school_id))
    # Log it
    log = await SuperAdminRepository(db).create_impersonation_log(current_user.id, school_id, admin_row["id"])
    return {"access_token": token, "log_id": str(log.id), "school_id": str(school_id)}

