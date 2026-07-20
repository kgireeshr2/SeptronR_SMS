"""Schemas for Phase 18 — Audit Logs."""
from __future__ import annotations
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    school_id: Optional[UUID]
    user_id: Optional[UUID]
    user_name: Optional[str]
    role_snapshot: Optional[str]
    module: str
    action: str
    record_type: Optional[str]
    record_id: Optional[UUID]
    record_description: Optional[str]
    old_values: Optional[Any]
    new_values: Optional[Any]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime


class AuditLogFilter(BaseModel):
    module: Optional[str] = None
    action: Optional[str] = None
    user_id: Optional[UUID] = None
    record_type: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
