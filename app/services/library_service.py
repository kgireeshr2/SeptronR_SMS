"""
Service — Phase 13: Library Management
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

import app.repositories.library_repository as repo
from app.core.exceptions import NotFoundError


async def list_categories(db, school_id):
    return await repo.list_categories(db, school_id)


async def create_category(db, school_id, data):
    return await repo.create_category(db, school_id, data)


# Books

async def list_books(db, school_id, category_id=None, search=None, available_only=False):
    return await repo.list_books(db, school_id, category_id, search, available_only)


async def get_book_or_404(db, school_id, book_id):
    book = await repo.get_book(db, school_id, book_id)
    if not book:
        raise NotFoundError("Book not found")
    return book


async def create_book(db, school_id, data):
    return await repo.create_book(db, school_id, data)


async def update_book(db, school_id, book_id, data):
    book = await get_book_or_404(db, school_id, book_id)
    return await repo.update_book(db, book, data)


# Members

async def list_members(db, school_id):
    return await repo.list_members(db, school_id)


async def get_member_or_404(db, school_id, member_id):
    m = await repo.get_member(db, school_id, member_id)
    if not m:
        raise NotFoundError("Library member not found")
    return m


async def create_member(db, school_id, data):
    return await repo.create_member(db, school_id, data)


# Issues

async def list_issues(db, school_id, returned=None):
    return await repo.list_issues(db, school_id, returned)


async def get_issue_or_404(db, school_id, issue_id):
    issue = await repo.get_issue(db, school_id, issue_id)
    if not issue:
        raise NotFoundError("Book issue not found")
    return issue


async def issue_book(db, school_id, data):
    # Check book availability
    book = await get_book_or_404(db, school_id, str(data.book_id))
    if book.available_copies <= 0:
        raise ValueError("No copies available for this book")
    return await repo.issue_book(db, school_id, data)


async def return_book(db, school_id, issue_id, data, fine_per_day: int = 100):
    issue = await get_issue_or_404(db, school_id, issue_id)
    if issue.is_returned:
        raise ValueError("Book already returned")
    return await repo.return_book(db, school_id, issue_id, data, fine_per_day)


async def list_overdue(db, school_id):
    return await repo.list_overdue_issues(db, school_id)

