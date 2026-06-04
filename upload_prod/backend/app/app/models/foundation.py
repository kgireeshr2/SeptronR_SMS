from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, SmallInteger, String, Text, UniqueConstraint
from app.models.compat import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class SchoolProfile(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "school_profile"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), unique=True, nullable=False
    )
    school_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    tagline: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(100), nullable=False, default="India")
    pincode: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    favicon_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    established_year: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    affiliation_board: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    affiliation_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    principal_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    principal_signature_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    school_seal_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timezone: Mapped[str] = mapped_column(String(100), nullable=False, default="Asia/Kolkata")
    currency: Mapped[str] = mapped_column(String(20), nullable=False, default="INR")
    date_format: Mapped[str] = mapped_column(String(30), nullable=False, default="DD/MM/YYYY")
    academic_start_month: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=4)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    school = relationship("School", lazy="noload")


class SchoolSetting(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "school_settings"
    __table_args__ = (UniqueConstraint("school_id", "key", name="uq_school_setting_key"),)

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="general")
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    data_type: Mapped[str] = mapped_column(String(20), nullable=False, default="string")
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    updated_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="NO ACTION"), nullable=True
    )

    school = relationship("School", lazy="noload")
