from sqlalchemy import String, Boolean, Text, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import UUIDPrimaryKeyMixin, TimestampMixin
from app.db.session import Base


class School(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "schools"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    code: Mapped[str | None] = mapped_column(String(50))  # unique enforced via filtered index below
    email: Mapped[str | None] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(20))
    address: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(100), default="India")
    pincode: Mapped[str | None] = mapped_column(String(10))
    logo_url: Mapped[str | None] = mapped_column(Text)
    website: Mapped[str | None] = mapped_column(String(200))
    board: Mapped[str | None] = mapped_column(String(50))
    medium: Mapped[str | None] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    deleted_at: Mapped[str | None] = mapped_column(nullable=True)

    # Relationships
    users: Mapped[list["User"]] = relationship("User", back_populates="school", lazy="noload")

    __table_args__ = (
        # Filtered unique index: only enforce uniqueness when code IS NOT NULL
        # (MSSQL unique constraints only allow one NULL row — this workaround
        # allows multiple NULL codes while still preventing duplicate non-null codes)
        Index(
            "ix_schools_code_unique",
            "code",
            unique=True,
            mssql_where=text("code IS NOT NULL"),
        ),
    )
