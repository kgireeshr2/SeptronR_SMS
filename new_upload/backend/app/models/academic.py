from datetime import date
from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, String
from app.models.compat import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class AcademicYear(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "academic_years"
    __table_args__ = (
        CheckConstraint("end_date > start_date", name="chk_academic_year_dates"),
    )

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    terms: Mapped[list["AcademicTerm"]] = relationship(
        "AcademicTerm", back_populates="academic_year", lazy="noload", cascade="all, delete-orphan"
    )


class AcademicTerm(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "academic_terms"
    __table_args__ = (
        CheckConstraint("end_date > start_date", name="chk_academic_term_dates"),
    )

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    academic_year_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    academic_year: Mapped["AcademicYear"] = relationship("AcademicYear", back_populates="terms", lazy="noload")
