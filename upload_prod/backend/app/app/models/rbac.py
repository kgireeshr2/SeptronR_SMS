from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, Text, ForeignKey, DateTime, PrimaryKeyConstraint
from app.models.compat import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import UUIDPrimaryKeyMixin, TimestampMixin
from app.db.session import Base

if TYPE_CHECKING:
    from app.models.auth import User


class Permission(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "permissions"

    module: Mapped[str] = mapped_column(String(60), nullable=False)
    action: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    roles: Mapped[list["Role"]] = relationship(
        "Role", secondary="role_permissions", back_populates="permissions", lazy="noload"
    )


class Role(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "roles"

    school_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    permissions: Mapped[list["Permission"]] = relationship(
        "Permission", secondary="role_permissions", back_populates="roles", lazy="noload"
    )
    users: Mapped[list["User"]] = relationship(
        "User",
        secondary="user_roles",
        primaryjoin="Role.id == user_roles.c.role_id",
        secondaryjoin="User.id == user_roles.c.user_id",
        back_populates="roles",
        lazy="noload",
    )


class RolePermission(Base):
    __tablename__ = "role_permissions"
    __table_args__ = (PrimaryKeyConstraint("role_id", "permission_id"),)

    role_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id", ondelete="NO ACTION"), nullable=False
    )
    permission_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="NO ACTION"), nullable=False
    )


class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = (PrimaryKeyConstraint("user_id", "role_id"),)

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="NO ACTION"), nullable=False
    )
    role_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id", ondelete="NO ACTION"), nullable=False
    )
    assigned_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="NO ACTION"), nullable=True
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
