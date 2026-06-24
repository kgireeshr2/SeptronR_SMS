"""
Repository — Phase 13: Library Management
"""
from __future__ import annotations

import datetime
import re
from typing import List, Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.library import Book, BookCategory, BookIssue, LibraryMember
from app.schemas.phase13 import (
    BookCategoryCreate,
    BookCreate, BookUpdate,
    BookIssueCreate, BookReturnRequest,
    LibraryMemberCreate,
)


# ─── Book Categories ─────────────────────────────────────────────────────────

async def list_categories(db: AsyncSession, school_id: str) -> List[BookCategory]:
    r = await db.execute(
        select(BookCategory).where(BookCategory.school_id == school_id)
    )
    return list(r.scalars().all())


async def create_category(
    db: AsyncSession, school_id: str, data: BookCategoryCreate
) -> BookCategory:
    obj = BookCategory(school_id=school_id, **data.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


# ─── Books ───────────────────────────────────────────────────────────────────

async def _next_accession(db: AsyncSession, school_id: str) -> str:
    r = await db.execute(
        select(func.count()).select_from(Book).where(Book.school_id == school_id)
    )
    count = r.scalar_one() or 0
    return f"ACC-{count + 1:05d}"


async def list_books(
    db: AsyncSession, school_id: str,
    category_id: Optional[str] = None,
    search: Optional[str] = None,
    available_only: bool = False,
) -> List[Book]:
    q = select(Book).where(Book.school_id == school_id, Book.is_active == True)
    if category_id:
        q = q.where(Book.category_id == category_id)
    if search:
        q = q.where(Book.title.ilike(f"%{search}%"))
    if available_only:
        q = q.where(Book.available_copies > 0)
    r = await db.execute(q.order_by(Book.title))
    return list(r.scalars().all())


async def get_book(db: AsyncSession, school_id: str, book_id: str) -> Optional[Book]:
    r = await db.execute(
        select(Book).where(Book.id == book_id, Book.school_id == school_id)
    )
    return r.scalar_one_or_none()


async def create_book(db: AsyncSession, school_id: str, data: BookCreate) -> Book:
    accession_number = await _next_accession(db, school_id)
    obj = Book(
        school_id=school_id,
        accession_number=accession_number,
        available_copies=data.total_copies,
        **data.model_dump(),
    )
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def update_book(db: AsyncSession, book: Book, data: BookUpdate) -> Book:
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(book, k, v)
    await db.flush()
    await db.refresh(book)
    return book


# ─── Library Members ─────────────────────────────────────────────────────────

async def _next_member_id(db: AsyncSession, school_id: str) -> str:
    r = await db.execute(
        select(func.count()).select_from(LibraryMember).where(LibraryMember.school_id == school_id)
    )
    count = r.scalar_one() or 0
    return f"LIB-{count + 1:03d}"


async def list_members(db: AsyncSession, school_id: str) -> List[LibraryMember]:
    r = await db.execute(
        select(LibraryMember).where(LibraryMember.school_id == school_id)
    )
    return list(r.scalars().all())


async def get_member(
    db: AsyncSession, school_id: str, member_id: str
) -> Optional[LibraryMember]:
    r = await db.execute(
        select(LibraryMember).where(
            LibraryMember.id == member_id, LibraryMember.school_id == school_id
        )
    )
    return r.scalar_one_or_none()


async def create_member(
    db: AsyncSession, school_id: str, data: LibraryMemberCreate
) -> LibraryMember:
    member_id = await _next_member_id(db, school_id)
    obj = LibraryMember(school_id=school_id, member_id=member_id, **data.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


# ─── Book Issues ─────────────────────────────────────────────────────────────

async def list_issues(
    db: AsyncSession, school_id: str, returned: Optional[bool] = None
) -> List[BookIssue]:
    q = select(BookIssue).where(BookIssue.school_id == school_id)
    if returned is not None:
        status_val = "returned" if returned else "issued"
        q = q.where(BookIssue.status == status_val)
    r = await db.execute(q.order_by(BookIssue.issue_date.desc()))
    return list(r.scalars().all())


async def get_issue(
    db: AsyncSession, school_id: str, issue_id: str
) -> Optional[BookIssue]:
    r = await db.execute(
        select(BookIssue).where(
            BookIssue.id == issue_id, BookIssue.school_id == school_id
        )
    )
    return r.scalar_one_or_none()


async def issue_book(
    db: AsyncSession, school_id: str, data: BookIssueCreate
) -> BookIssue:
    issue = BookIssue(school_id=school_id, status="issued", fine_amount=0, **data.model_dump())
    db.add(issue)
    # Reduce available copies
    await db.execute(
        update(Book)
        .where(Book.id == str(data.book_id))
        .values(available_copies=Book.available_copies - 1)
    )
    await db.flush()
    await db.refresh(issue)
    return issue


async def return_book(
    db: AsyncSession,
    school_id: str,
    issue_id: str,
    data: BookReturnRequest,
    fine_per_day: int = 100,
) -> BookIssue:
    issue = await get_issue(db, school_id, issue_id)
    if not issue or issue.status == "returned":
        return issue  # type: ignore

    fine = 0
    if data.return_date > issue.due_date:
        overdue_days = (data.return_date - issue.due_date).days
        fine = overdue_days * fine_per_day

    issue.status = "returned"
    issue.return_date = data.return_date
    issue.fine_amount = fine
    if data.remarks:
        issue.remarks = data.remarks

    await db.execute(
        update(Book)
        .where(Book.id == str(issue.book_id))
        .values(available_copies=Book.available_copies + 1)
    )
    await db.flush()
    await db.refresh(issue)
    return issue


async def list_overdue_issues(db: AsyncSession, school_id: str) -> List[BookIssue]:
    today = datetime.date.today()
    r = await db.execute(
        select(BookIssue).where(
            BookIssue.school_id == school_id,
            BookIssue.status == "issued",
            BookIssue.due_date < today,
        )
    )
    return list(r.scalars().all())

