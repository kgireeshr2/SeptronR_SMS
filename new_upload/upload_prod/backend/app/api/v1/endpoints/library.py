"""
API Endpoints — Phase 13: Library Management
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_school_id, permission_required
import app.services.library_service as svc
from app.schemas.phase13 import (
    BookCategoryCreate, BookCategoryResponse,
    BookCreate, BookUpdate, BookResponse,
    LibraryMemberCreate, LibraryMemberResponse,
    BookIssueCreate, BookReturnRequest, BookIssueResponse,
)

lib_cat_router = APIRouter(prefix="/library/categories", tags=["Library"])
books_router = APIRouter(prefix="/library/books", tags=["Library"])
members_router = APIRouter(prefix="/library/members", tags=["Library"])
issues_router = APIRouter(prefix="/library/issues", tags=["Library"])


# ─── Categories ──────────────────────────────────────────────────────────────

@lib_cat_router.get("", response_model=List[BookCategoryResponse])
async def list_categories(school_id=Depends(get_school_id), db=Depends(get_db),
                          _=Depends(permission_required("library", "view"))):
    return await svc.list_categories(db, school_id)


@lib_cat_router.post("", response_model=BookCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(data: BookCategoryCreate, school_id=Depends(get_school_id),
                          db=Depends(get_db), _=Depends(permission_required("library", "manage"))):
    obj = await svc.create_category(db, school_id, data)
    await db.commit()
    await db.refresh(obj)
    return obj


# ─── Books ───────────────────────────────────────────────────────────────────

@books_router.get("", response_model=List[BookResponse])
async def list_books(
    category_id: Optional[UUID] = Query(None),
    search: Optional[str] = Query(None),
    available_only: bool = Query(False),
    school_id=Depends(get_school_id), db=Depends(get_db),
    _=Depends(permission_required("library", "view")),
):
    return await svc.list_books(
        db, school_id,
        str(category_id) if category_id else None,
        search, available_only,
    )


@books_router.post("", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(data: BookCreate, school_id=Depends(get_school_id),
                      db=Depends(get_db), _=Depends(permission_required("library", "manage"))):
    obj = await svc.create_book(db, school_id, data)
    await db.commit()
    await db.refresh(obj)
    return obj


@books_router.get("/{book_id}", response_model=BookResponse)
async def get_book(book_id: UUID, school_id=Depends(get_school_id), db=Depends(get_db),
                   _=Depends(permission_required("library", "view"))):
    return await svc.get_book_or_404(db, school_id, str(book_id))


@books_router.put("/{book_id}", response_model=BookResponse)
async def update_book(book_id: UUID, data: BookUpdate, school_id=Depends(get_school_id),
                      db=Depends(get_db), _=Depends(permission_required("library", "manage"))):
    obj = await svc.update_book(db, school_id, str(book_id), data)
    await db.commit()
    await db.refresh(obj)
    return obj


# ─── Members ─────────────────────────────────────────────────────────────────

@members_router.get("", response_model=List[LibraryMemberResponse])
async def list_members(school_id=Depends(get_school_id), db=Depends(get_db),
                       _=Depends(permission_required("library", "view"))):
    return await svc.list_members(db, school_id)


@members_router.post("", response_model=LibraryMemberResponse, status_code=status.HTTP_201_CREATED)
async def create_member(data: LibraryMemberCreate, school_id=Depends(get_school_id),
                        db=Depends(get_db), _=Depends(permission_required("library", "manage"))):
    obj = await svc.create_member(db, school_id, data)
    await db.commit()
    await db.refresh(obj)
    return obj


# ─── Issues ──────────────────────────────────────────────────────────────────

@issues_router.get("", response_model=List[BookIssueResponse])
async def list_issues(
    returned: Optional[bool] = Query(None),
    school_id=Depends(get_school_id), db=Depends(get_db),
    _=Depends(permission_required("library", "view")),
):
    return await svc.list_issues(db, school_id, returned)


@issues_router.get("/overdue", response_model=List[BookIssueResponse])
async def list_overdue(school_id=Depends(get_school_id), db=Depends(get_db),
                       _=Depends(permission_required("library", "view"))):
    return await svc.list_overdue(db, school_id)


@issues_router.post("", response_model=BookIssueResponse, status_code=status.HTTP_201_CREATED)
async def issue_book(data: BookIssueCreate, school_id=Depends(get_school_id),
                     db=Depends(get_db), _=Depends(permission_required("library", "manage"))):
    obj = await svc.issue_book(db, school_id, data)
    await db.commit()
    await db.refresh(obj)
    return obj


@issues_router.post("/{issue_id}/return", response_model=BookIssueResponse)
async def return_book(issue_id: UUID, data: BookReturnRequest,
                      school_id=Depends(get_school_id), db=Depends(get_db),
                      _=Depends(permission_required("library", "manage"))):
    obj = await svc.return_book(db, school_id, str(issue_id), data)
    await db.commit()
    await db.refresh(obj)
    return obj

