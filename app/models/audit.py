"""
SQLAlchemy models — Phase 18: Audit Logs
Table: audit_logs (partitioned by created_at — managed in Alembic migration)
"""
from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from uuid import UUID as PyUUID
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, func
from app.models.compat import UUID, JSONB

from app.db.session import Base


class AuditLog(Base):
    """
    Append-only audit log. Table is RANGE-partitioned by created_at.
    Do NOT add updated_at (it is immutable).
    """
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    user_name = Column(String(200), nullable=True)
    role_snapshot = Column(String(100), nullable=True)
    module = Column(String(100), nullable=True, index=True)
    action = Column(String(50), nullable=True, index=True)
    record_type = Column(String(100), nullable=True)
    record_id = Column(UUID(as_uuid=True), nullable=True)
    record_description = Column(Text, nullable=True)
    old_values = Column(JSONB, nullable=True)
    new_values = Column(JSONB, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
