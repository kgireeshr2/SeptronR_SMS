"""Resolve a notification audience into concrete recipients (user_id / phone / email)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import User
from app.models.staff import Staff
from app.models.students import Student, StudentEnrollment, StudentParent


@dataclass
class Recipient:
    user_id: Optional[str]
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None


def _dedupe(recipients: List[Recipient]) -> List[Recipient]:
    seen = set()
    out: List[Recipient] = []
    for r in recipients:
        key = str(r.user_id) if r.user_id else (r.phone or r.email or r.name)
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


async def _parents(db, school_id, *, class_id=None, section_id=None, student_ids=None) -> List[Recipient]:
    q = select(StudentParent).where(StudentParent.school_id == school_id)
    if student_ids:
        q = q.where(StudentParent.student_id.in_(list(student_ids)))
    elif class_id or section_id:
        q = q.join(StudentEnrollment, StudentEnrollment.student_id == StudentParent.student_id).where(
            StudentEnrollment.is_current == True  # noqa: E712
        )
        if class_id:
            q = q.where(StudentEnrollment.class_id == class_id)
        if section_id:
            q = q.where(StudentEnrollment.section_id == section_id)
    rows = (await db.execute(q)).scalars().all()
    return [
        Recipient(user_id=str(p.user_id) if p.user_id else None, name=p.name or "Parent",
                  phone=p.phone, email=p.email)
        for p in rows
    ]


async def _students(db, school_id, *, class_id=None, section_id=None, student_ids=None) -> List[Recipient]:
    q = select(Student).where(Student.school_id == school_id, Student.is_active == True)  # noqa: E712
    if student_ids:
        q = q.where(Student.id.in_(list(student_ids)))
    elif class_id or section_id:
        q = q.join(StudentEnrollment, StudentEnrollment.student_id == Student.id).where(
            StudentEnrollment.is_current == True  # noqa: E712
        )
        if class_id:
            q = q.where(StudentEnrollment.class_id == class_id)
        if section_id:
            q = q.where(StudentEnrollment.section_id == section_id)
    rows = (await db.execute(q)).scalars().all()
    return [
        Recipient(user_id=str(s.user_id) if s.user_id else None,
                  name=f"{s.first_name} {s.last_name}".strip(), phone=s.phone, email=s.email)
        for s in rows
    ]


async def _staff(db, school_id) -> List[Recipient]:
    q = (
        select(Staff, User)
        .join(User, User.id == Staff.user_id)
        .where(Staff.school_id == school_id, Staff.is_active == True)  # noqa: E712
    )
    rows = (await db.execute(q)).all()
    return [
        Recipient(user_id=str(u.id), name=f"{s.first_name} {s.last_name}".strip(),
                  phone=u.phone, email=u.email)
        for s, u in rows
    ]


async def _users_by_ids(db, user_ids) -> List[Recipient]:
    if not user_ids:
        return []
    rows = (await db.execute(select(User).where(User.id.in_(list(user_ids))))).scalars().all()
    return [
        Recipient(user_id=str(u.id), name=f"{u.first_name or ''} {u.last_name or ''}".strip() or (u.username or ""),
                  phone=u.phone, email=u.email)
        for u in rows
    ]


async def resolve_recipients(
    db: AsyncSession,
    school_id: str,
    audience: str,
    *,
    class_id: Optional[str] = None,
    section_id: Optional[str] = None,
    user_ids: Optional[list] = None,
    student_ids: Optional[list] = None,
    direct_contacts: Optional[list] = None,
) -> List[Recipient]:
    audience = (audience or "all").lower()
    out: List[Recipient] = []

    if audience == "direct":
        # Ad-hoc contacts not (yet) in the system — e.g. an admission applicant's parent.
        out = [
            Recipient(user_id=c.get("user_id"), name=c.get("name") or "",
                      phone=c.get("phone"), email=c.get("email"))
            for c in (direct_contacts or [])
        ]
    elif audience == "custom":
        out = await _users_by_ids(db, user_ids)
    elif audience in ("student_parents", "parents"):
        out = await _parents(db, school_id, class_id=class_id, section_id=section_id, student_ids=student_ids)
    elif audience == "students":
        out = await _students(db, school_id, class_id=class_id, section_id=section_id, student_ids=student_ids)
    elif audience == "staff":
        out = await _staff(db, school_id)
    elif audience in ("class", "section"):
        # Class/section broadcast → parents + students of that class/section.
        out = await _parents(db, school_id, class_id=class_id, section_id=section_id)
        out += await _students(db, school_id, class_id=class_id, section_id=section_id)
    else:  # "all"
        out = await _staff(db, school_id)
        out += await _parents(db, school_id)
        out += await _students(db, school_id)

    return _dedupe([r for r in out if (r.phone or r.email or r.user_id)])
