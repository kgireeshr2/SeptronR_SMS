"""SaaS entitlements: subscription status, plan seat limits, and feature flags.

Opt-in FastAPI dependencies:
  - require_active_subscription : block when the school's subscription is inactive/expired.
  - feature_required(key)       : gate an endpoint/module behind a SchoolFeatureFlag.
  - enforce_student_seat_limit  : cap student creation at the plan's max_students.

All FAIL OPEN when no subscription/flag is configured, so installs that haven't been
onboarded to billing are unaffected until a plan is assigned.
"""
from __future__ import annotations

from datetime import date
from typing import Optional, Tuple

from fastapi import Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_school_id
from app.db.session import get_db
from app.models.students import Student
from app.models.super_admin import SchoolFeatureFlag, SchoolSubscription, SubscriptionPlan


async def get_active_plan(
    db: AsyncSession, school_id
) -> Tuple[Optional[SchoolSubscription], Optional[SubscriptionPlan]]:
    row = (await db.execute(
        select(SchoolSubscription, SubscriptionPlan)
        .join(SubscriptionPlan, SubscriptionPlan.id == SchoolSubscription.plan_id)
        .where(
            SchoolSubscription.school_id == school_id,
            SchoolSubscription.is_active == True,  # noqa: E712
        )
        .order_by(SchoolSubscription.starts_at.desc())
        .limit(1)
    )).first()
    if not row:
        return None, None
    return row[0], row[1]


def _expired(sub: SchoolSubscription) -> bool:
    return bool(sub.ends_at and sub.ends_at < date.today())


async def require_active_subscription(
    school_id=Depends(get_school_id), db: AsyncSession = Depends(get_db)
):
    """Block when the school has a subscription that is inactive/expired. Fails OPEN
    when no subscription row exists (not yet onboarded to billing)."""
    sub, _ = await get_active_plan(db, school_id)
    if sub is None:
        return
    if not sub.is_active or _expired(sub):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="School subscription is inactive or expired.",
        )


def feature_required(feature_key: str):
    """Gate an endpoint behind a per-school feature flag. Default ON — only an explicit
    is_enabled=False blocks."""
    async def _dep(school_id=Depends(get_school_id), db: AsyncSession = Depends(get_db)):
        row = (await db.execute(
            select(SchoolFeatureFlag.is_enabled).where(
                SchoolFeatureFlag.school_id == school_id,
                SchoolFeatureFlag.feature_key == feature_key,
            ).limit(1)
        )).first()
        if row is not None and row[0] is False:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Feature '{feature_key}' is not enabled for this school.",
            )
    return _dep


async def enforce_student_seat_limit(
    school_id=Depends(get_school_id), db: AsyncSession = Depends(get_db)
):
    """Reject student creation once the plan's max_students is reached. No-op without a plan."""
    _, plan = await get_active_plan(db, school_id)
    if not plan or plan.max_students is None:
        return
    count = (await db.execute(
        select(func.count(Student.id)).where(
            Student.school_id == school_id, Student.deleted_at.is_(None)
        )
    )).scalar() or 0
    if count >= plan.max_students:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Student limit reached for your plan ({plan.max_students}). Upgrade to add more.",
        )
