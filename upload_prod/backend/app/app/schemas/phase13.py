"""
Pydantic v2 schemas — Phase 13: Library Management
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BookCategoryCreate(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None


class BookCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    name: str
    description: Optional[str]
    is_active: bool


class BookCreate(BaseModel):
    title: str = Field(..., max_length=300)
    author: Optional[str] = None
    isbn: Optional[str] = None
    publisher: Optional[str] = None
    edition: Optional[str] = None
    publication_year: Optional[int] = None
    category_id: Optional[UUID] = None
    total_copies: int = Field(1, ge=1)
    price: int = 0
    location: Optional[str] = None
    description: Optional[str] = None


class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    isbn: Optional[str] = None
    publisher: Optional[str] = None
    edition: Optional[str] = None
    category_id: Optional[UUID] = None
    total_copies: Optional[int] = None
    price: Optional[int] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None


class BookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    accession_number: Optional[str]
    title: str
    author: Optional[str]
    isbn: Optional[str]
    publisher: Optional[str]
    edition: Optional[str]
    publication_year: Optional[int]
    category_id: Optional[UUID]
    total_copies: int
    available_copies: int
    price: int
    location: Optional[str]
    is_active: bool


class LibraryMemberCreate(BaseModel):
    user_id: UUID
    member_type: str = Field("student", pattern="^(student|staff)$")
    max_books_allowed: int = 3


class LibraryMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    member_id: str
    user_id: UUID
    member_type: str
    max_books_allowed: int
    is_active: bool


class BookIssueCreate(BaseModel):
    book_id: UUID
    member_id: UUID
    issue_date: date
    due_date: date
    remarks: Optional[str] = None


class BookReturnRequest(BaseModel):
    return_date: date
    condition: str = "good"
    remarks: Optional[str] = None


class BookIssueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    book_id: UUID
    member_id: UUID
    issue_date: date
    due_date: date
    return_date: Optional[date]
    status: str
    fine_amount: int
    remarks: Optional[str]
    created_at: datetime
