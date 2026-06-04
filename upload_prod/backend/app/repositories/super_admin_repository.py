from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, text

from app.models.super_admin import (
    SubscriptionPlan,
    SchoolSubscription,
    SchoolFeatureFlag,
    ImpersonationLog,
)
from app.models.school import School


class SuperAdminRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ---- Subscription Plans ----
    async def list_plans(self) -> List[SubscriptionPlan]:
        r = await self.db.execute(select(SubscriptionPlan).order_by(SubscriptionPlan.price_monthly_paise))
        return list(r.scalars().all())

    async def create_plan(self, data: dict) -> SubscriptionPlan:
        plan = SubscriptionPlan(**data)
        self.db.add(plan)
        await self.db.commit()
        await self.db.refresh(plan)
        return plan

    async def update_plan(self, plan_id: UUID, data: dict) -> Optional[SubscriptionPlan]:
        r = await self.db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id))
        plan = r.scalar_one_or_none()
        if not plan:
            return None
        for k, v in data.items():
            setattr(plan, k, v)
        await self.db.commit()
        await self.db.refresh(plan)
        return plan

    # ---- Subscriptions ----
    async def list_subscriptions(self, school_id: Optional[UUID] = None) -> List[SchoolSubscription]:
        q = select(SchoolSubscription)
        if school_id:
            q = q.where(SchoolSubscription.school_id == school_id)
        r = await self.db.execute(q.order_by(SchoolSubscription.starts_at.desc()))
        return list(r.scalars().all())

    async def create_subscription(self, data: dict) -> SchoolSubscription:
        sub = SchoolSubscription(**data)
        self.db.add(sub)
        await self.db.commit()
        await self.db.refresh(sub)
        return sub

    async def deactivate_subscription(self, sub_id: UUID) -> Optional[SchoolSubscription]:
        r = await self.db.execute(select(SchoolSubscription).where(SchoolSubscription.id == sub_id))
        sub = r.scalar_one_or_none()
        if sub:
            sub.is_active = False
            await self.db.commit()
        return sub

    # ---- Feature Flags ----
    async def get_flags(self, school_id: UUID) -> List[SchoolFeatureFlag]:
        r = await self.db.execute(
            select(SchoolFeatureFlag).where(SchoolFeatureFlag.school_id == school_id)
        )
        return list(r.scalars().all())

    async def set_flag(self, school_id: UUID, feature_key: str, is_enabled: bool) -> SchoolFeatureFlag:
        r = await self.db.execute(
            select(SchoolFeatureFlag).where(
                SchoolFeatureFlag.school_id == school_id,
                SchoolFeatureFlag.feature_key == feature_key,
            )
        )
        flag = r.scalar_one_or_none()
        if flag:
            flag.is_enabled = is_enabled
        else:
            flag = SchoolFeatureFlag(school_id=school_id, feature_key=feature_key, is_enabled=is_enabled)
            self.db.add(flag)
        await self.db.commit()
        await self.db.refresh(flag)
        return flag

    # ---- Impersonation ----
    async def create_impersonation_log(
        self, super_admin_id: UUID, school_id: UUID, user_id: UUID
    ) -> ImpersonationLog:
        log = ImpersonationLog(
            super_admin_id=super_admin_id,
            impersonated_school_id=school_id,
            impersonated_user_id=user_id,
        )
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def end_impersonation(self, log_id: UUID) -> Optional[ImpersonationLog]:
        r = await self.db.execute(select(ImpersonationLog).where(ImpersonationLog.id == log_id))
        log = r.scalar_one_or_none()
        if log:
            log.ended_at = datetime.utcnow()
            await self.db.commit()
        return log

    # ---- Schools ----
    async def list_schools(self) -> List[dict]:
        sql = text("""
            SELECT
                s.id,
                s.name,
                s.slug,
                s.code,
                s.is_active,
                s.created_at,
                COALESCE(ay.cnt, 0) +
                COALESCE(cl.cnt, 0) +
                COALESCE(st.cnt, 0) +
                COALESCE(std.cnt, 0) +
                COALESCE(fs.cnt, 0) +
                COALESCE(tt.cnt, 0) +
                COALESCE(ex.cnt, 0) +
                COALESCE(att.cnt, 0) AS setup_progress
            FROM schools s
            LEFT JOIN (SELECT school_id, CAST(CASE WHEN COUNT(*)>0 THEN 1 ELSE 0 END AS INT) AS cnt FROM academic_years GROUP BY school_id) ay ON ay.school_id = s.id
            LEFT JOIN (SELECT school_id, CAST(CASE WHEN COUNT(*)>0 THEN 1 ELSE 0 END AS INT) AS cnt FROM classes GROUP BY school_id) cl ON cl.school_id = s.id
            LEFT JOIN (SELECT school_id, CAST(CASE WHEN COUNT(*)>0 THEN 1 ELSE 0 END AS INT) AS cnt FROM staff GROUP BY school_id) st ON st.school_id = s.id
            LEFT JOIN (SELECT school_id, CAST(CASE WHEN COUNT(*)>0 THEN 1 ELSE 0 END AS INT) AS cnt FROM students GROUP BY school_id) std ON std.school_id = s.id
            LEFT JOIN (SELECT school_id, CAST(CASE WHEN COUNT(*)>0 THEN 1 ELSE 0 END AS INT) AS cnt FROM fee_structures GROUP BY school_id) fs ON fs.school_id = s.id
            LEFT JOIN (SELECT school_id, CAST(CASE WHEN COUNT(*)>0 THEN 1 ELSE 0 END AS INT) AS cnt FROM timetables GROUP BY school_id) tt ON tt.school_id = s.id
            LEFT JOIN (SELECT school_id, CAST(CASE WHEN COUNT(*)>0 THEN 1 ELSE 0 END AS INT) AS cnt FROM exam_types GROUP BY school_id) ex ON ex.school_id = s.id
            LEFT JOIN (SELECT school_id, CAST(CASE WHEN COUNT(*)>0 THEN 1 ELSE 0 END AS INT) AS cnt FROM attendance_sessions GROUP BY school_id) att ON att.school_id = s.id
            ORDER BY s.name
        """)
        result = await self.db.execute(sql)
        rows = result.mappings().all()
        return [
            {
                "id": str(row["id"]),
                "name": row["name"],
                "slug": row["slug"],
                "code": row["code"],
                "is_active": row["is_active"],
                "created_at": row["created_at"],
                "setup_progress": int(row["setup_progress"]),
            }
            for row in rows
        ]

    async def toggle_school_active(self, school_id: UUID, is_active: bool) -> Optional[School]:
        r = await self.db.execute(select(School).where(School.id == school_id))
        school = r.scalar_one_or_none()
        if school:
            school.is_active = is_active
            await self.db.commit()
            await self.db.refresh(school)
        return school

