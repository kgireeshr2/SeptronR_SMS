"""
Base mixins for all SQLAlchemy models.
"""
import uuid
from sqlalchemy import Column, DateTime, func
from app.models.compat import UUID


class TimestampMixin:
    """Adds created_at and updated_at columns to models."""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDPrimaryKeyMixin:
    """Adds a UUID primary key column to models."""
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
