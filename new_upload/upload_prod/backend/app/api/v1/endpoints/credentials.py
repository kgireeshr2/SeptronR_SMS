"""
Credential Management Endpoint
Admin can manage passwords and alternate login identifiers for students, parents, and staff.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, or_, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_school_id, permission_required
from app.core.security import hash_password
from app.db.session import get_db
from app.models.auth import User
from app.utils.response import ok

router = APIRouter(prefix="/credentials", tags=["credentials"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class SetPasswordRequest(BaseModel):
    user_id: str
    new_password: str = Field(..., min_length=6)


class SetUsernameRequest(BaseModel):
    """Set an alternate login username for a user."""
    user_id: str
    username: Optional[str] = None   # pass None to clear
    phone: Optional[str] = None      # pass to update phone (used as parent login)


class UserCredentialInfo(BaseModel):
    id: str
    user_type: str        # student | parent | staff
    display_name: str
    email: Optional[str]
    phone: Optional[str]
    username: Optional[str]   # alternate login (admission_number for students, employee_id for staff)
    is_active: bool
    linked_id: Optional[str]  # student_id / staff_id
    linked_ref: Optional[str]  # admission_number / employee_id


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.get("/users", response_model=dict, dependencies=[Depends(permission_required("users", "view"))])
async def list_credential_users(
    user_type: Optional[str] = Query(None, description="student | parent | staff | all"),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all portal users for a school grouped by type."""
    sid = str(school_id)
    results = []

    if not user_type or user_type in ("student", "all"):
        # Students with their user accounts
        q = """
            SELECT
                u.id AS user_id,
                u.email,
                u.phone,
                u.username,
                u.is_active,
                s.id AS linked_id,
                s.first_name || ' ' || s.last_name AS display_name,
                s.admission_number AS linked_ref
            FROM students s
            LEFT JOIN users u ON u.id = s.user_id
            WHERE s.school_id = :sid AND s.deleted_at IS NULL
        """
        params: dict = {"sid": sid}
        if search:
            q += " AND (s.first_name LIKE :q OR s.last_name LIKE :q OR s.admission_number LIKE :q OR u.email LIKE :q)"
            params["q"] = f"%{search}%"
        q += f" ORDER BY s.first_name LIMIT {limit} OFFSET {skip}"
        rows = (await db.execute(text(q), params)).fetchall()
        for r in rows:
            results.append({
                "id": str(r.user_id) if r.user_id else None,
                "user_type": "student",
                "display_name": r.display_name,
                "email": r.email,
                "phone": r.phone,
                "username": r.username,
                "is_active": bool(r.is_active) if r.is_active is not None else True,
                "linked_id": str(r.linked_id),
                "linked_ref": r.linked_ref,
            })

    if not user_type or user_type in ("parent", "all"):
        q = """
            SELECT
                u.id AS user_id,
                u.email,
                u.phone,
                u.username,
                u.is_active,
                sp.id AS linked_id,
                sp.name AS display_name,
                sp.relation AS linked_ref
            FROM student_parents sp
            LEFT JOIN users u ON u.id = sp.user_id
            WHERE sp.school_id = :sid
        """
        params = {"sid": sid}
        if search:
            q += " AND (sp.name LIKE :q OR sp.phone LIKE :q OR u.email LIKE :q)"
            params["q"] = f"%{search}%"
        q += f" ORDER BY sp.name LIMIT {limit} OFFSET {skip}"
        rows = (await db.execute(text(q), params)).fetchall()
        for r in rows:
            results.append({
                "id": str(r.user_id) if r.user_id else None,
                "user_type": "parent",
                "display_name": r.display_name,
                "email": r.email,
                "phone": r.phone,
                "username": r.username,
                "is_active": bool(r.is_active) if r.is_active is not None else True,
                "linked_id": str(r.linked_id),
                "linked_ref": str(r.linked_ref) if r.linked_ref else None,
            })

    if not user_type or user_type in ("staff", "all"):
        q = """
            SELECT
                u.id AS user_id,
                u.email,
                u.phone,
                u.username,
                u.is_active,
                st.id AS linked_id,
                st.first_name || ' ' || st.last_name AS display_name,
                st.employee_id AS linked_ref
            FROM staff st
            LEFT JOIN users u ON u.id = st.user_id
            WHERE st.school_id = :sid AND st.deleted_at IS NULL
        """
        params = {"sid": sid}
        if search:
            q += " AND (st.first_name LIKE :q OR st.last_name LIKE :q OR st.employee_id LIKE :q OR u.email LIKE :q)"
            params["q"] = f"%{search}%"
        q += f" ORDER BY st.first_name LIMIT {limit} OFFSET {skip}"
        rows = (await db.execute(text(q), params)).fetchall()
        for r in rows:
            results.append({
                "id": str(r.user_id) if r.user_id else None,
                "user_type": "staff",
                "display_name": r.display_name,
                "email": r.email,
                "phone": r.phone,
                "username": r.username,
                "is_active": bool(r.is_active) if r.is_active is not None else True,
                "linked_id": str(r.linked_id),
                "linked_ref": r.linked_ref,
            })

    return ok({"items": results, "total": len(results)})


@router.post("/set-password", response_model=dict, dependencies=[Depends(permission_required("users", "edit"))])
async def set_user_password(
    data: SetPasswordRequest,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admin sets / resets password for any user in the school."""
    result = await db.execute(
        select(User).where(User.id == data.user_id, User.school_id == str(school_id))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.password_hash = hash_password(data.new_password)
    await db.commit()
    return ok(None, "Password updated successfully")


@router.post("/set-username", response_model=dict, dependencies=[Depends(permission_required("users", "edit"))])
async def set_user_username(
    data: SetUsernameRequest,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Set alternate login username and/or phone for a user.
    - Students: set username = admission_number (allows login with admission no.)
    - Parents: set phone (allows login with phone number)
    - Staff: set username = employee_id (allows login with employee ID)
    """
    result = await db.execute(
        select(User).where(User.id == data.user_id, User.school_id == str(school_id))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if data.username is not None:
        # Check for duplicate username in school
        if data.username:
            dup = await db.execute(
                select(User).where(
                    User.school_id == str(school_id),
                    User.username == data.username,
                    User.id != data.user_id,
                )
            )
            if dup.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This username is already in use by another account",
                )
        user.username = data.username or None

    if data.phone is not None:
        # Check for duplicate phone in school
        if data.phone:
            dup = await db.execute(
                select(User).where(
                    User.school_id == str(school_id),
                    User.phone == data.phone,
                    User.id != data.user_id,
                )
            )
            if dup.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This phone number is already registered to another account",
                )
        user.phone = data.phone or None

    await db.commit()
    return ok({"username": user.username, "phone": user.phone}, "Login identity updated")


@router.post("/toggle-active", response_model=dict, dependencies=[Depends(permission_required("users", "edit"))])
async def toggle_user_active(
    user_id: str,
    is_active: bool,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Enable or disable a user account."""
    result = await db.execute(
        select(User).where(User.id == user_id, User.school_id == str(school_id))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_active = is_active
    await db.commit()
    return ok(None, f"Account {'enabled' if is_active else 'disabled'}")
