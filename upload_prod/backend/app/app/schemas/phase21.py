from datetime import date, datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# Subscription Plans
class SubscriptionPlanCreate(BaseModel):
    name: str
    max_students: Optional[int] = None
    max_staff: Optional[int] = None
    enabled_modules: List[str] = []
    price_monthly_paise: int = 0


class SubscriptionPlanResponse(SubscriptionPlanCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime


# School Subscriptions
class SchoolSubscriptionCreate(BaseModel):
    school_id: UUID
    plan_id: UUID
    starts_at: date
    ends_at: Optional[date] = None
    notes: Optional[str] = None


class SchoolSubscriptionResponse(SchoolSubscriptionCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    is_active: bool
    created_at: datetime


# Feature Flags
class FeatureFlagSet(BaseModel):
    feature_key: str
    is_enabled: bool


class FeatureFlagResponse(FeatureFlagSet):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    school_id: UUID
    created_at: datetime


# Impersonation
class ImpersonateRequest(BaseModel):
    school_id: UUID
    user_id: UUID


class ImpersonationLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    super_admin_id: UUID
    impersonated_school_id: UUID
    impersonated_user_id: UUID
    started_at: datetime
    ended_at: Optional[datetime] = None


# School overview for super admin list
class SchoolOverview(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    slug: Optional[str] = None
    code: Optional[str] = None
    is_active: bool
    created_at: datetime
    setup_progress: int = 0  # 0–8 steps completed
