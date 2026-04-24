"""
SQLAlchemy models — Phase 13: Library Management
Tables: book_categories, books, library_members, book_issues, library_settings (as a simple model)
"""
from __future__ import annotations

from datetime import date
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    BigInteger, Boolean, Date, ForeignKey, SmallInteger,
    String, Text, UniqueConstraint,
)
from app.models.compat import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.school import School
    from app.models.auth import User


class BookCategory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "book_categories"
    __table_args__ = (UniqueConstraint("school_id", "name", name="book_categories_school_name_ux"),)

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Book(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "books"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    category_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("book_categories.id"), nullable=True
    )
    accession_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    author: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    publisher: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    isbn: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    edition: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    publication_year: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    language: Mapped[str] = mapped_column(String(50), nullable=False, default="English")
    total_copies: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    available_copies: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    cover_image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rack_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    price: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    issues: Mapped[list["BookIssue"]] = relationship(
        "BookIssue", back_populates="book", lazy="noload"
    )


class LibraryMember(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "library_members"
    __table_args__ = (UniqueConstraint("school_id", "member_id", name="library_members_school_mid_ux"),)

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    member_id: Mapped[str] = mapped_column(String(20), nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    member_type: Mapped[str] = mapped_column(String(10), nullable=False)  # student|staff
    entity_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=True), nullable=True)
    max_books_allowed: Mapped[int] = mapped_column("max_books_allowed", SmallInteger, nullable=False, default=3)
    membership_valid_until: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    issues: Mapped[list["BookIssue"]] = relationship(
        "BookIssue", back_populates="library_member", lazy="noload"
    )


class BookIssue(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "book_issues"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    book_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("books.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    member_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("library_members.id"), nullable=False, index=True
    )
    issued_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    return_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    fine_per_day: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    fine_amount: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    fine_paid: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="issued")
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    book: Mapped["Book"] = relationship("Book", back_populates="issues", lazy="noload")
    library_member: Mapped["LibraryMember"] = relationship(
        "LibraryMember", back_populates="issues", lazy="noload"
    )
