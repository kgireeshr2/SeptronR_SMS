from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, Text, ForeignKey, DateTime
from app.models.compat import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import UUIDPrimaryKeyMixin, TimestampMixin
from app.db.session import Base

if TYPE_CHECKING:
    from app.models.school import School
    from app.models.rbac import Role


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    school_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=True, index=True
    )
    username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    otp_secret: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_super_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="NO ACTION"), nullable=True
    )

    # Relationships
    school: Mapped[Optional["School"]] = relationship("School", back_populates="users", lazy="noload")
    roles: Mapped[list["Role"]] = relationship(
        "Role",
        secondary="user_roles",
        primaryjoin="User.id == user_roles.c.user_id",
        secondaryjoin="Role.id == user_roles.c.role_id",
        back_populates="users",
        lazy="noload",
    )
    password_reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(
        "PasswordResetToken", back_populates="user", lazy="noload"
    )


class PasswordResetToken(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "password_reset_tokens"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="NO ACTION"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="password_reset_tokens", lazy="noload")
