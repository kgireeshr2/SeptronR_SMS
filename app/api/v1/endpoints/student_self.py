"""Student self-service endpoints.

A logged-in *student* has a `students.user_id` link but no way to discover its
own `student_id` (unlike a parent, who gets children from the parent dashboard).
`GET /students/me` resolves the caller's own student record (and current
class/section from `student_enrollments`) so the mobile app can then load the
student's attendance, fees, report cards, etc.

Auth-only: the record is resolved from `current_user.id`, so it is inherently
the caller's own data (ownership by construction).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_school_id
from app.db.session import get_db
from app.models.auth import User
from app.utils.response import ok

# Same prefix as the students router. This router is included BEFORE the main
# students router in router.py so that `/students/me` is matched before the
# `/students/{student_id}` (UUID) route.
router = APIRouter(prefix="/students", tags=["student-self"])


@router.get("/me")
async def get_my_student_profile(
    school_id=Depends(get_school_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Resolve the current user's own student record + current enrollment."""
    row = (
        await db.execute(
            text(
                """
                SELECT s.id, s.admission_number, s.first_name, s.last_name,
                       s.photo_url, s.gender, s.date_of_birth,
                       e.class_id, c.name AS class_name,
                       e.section_id, sec.name AS section_name,
                       e.academic_year_id, e.roll_number
                FROM students s
                LEFT JOIN student_enrollments e
                       ON e.student_id = s.id AND e.is_current = true
                LEFT JOIN classes c ON c.id = e.class_id
                LEFT JOIN sections sec ON sec.id = e.section_id
                WHERE s.school_id = :school_id
                  AND s.user_id = :user_id
                  AND s.is_active = true
                  AND s.deleted_at IS NULL
                """
            ),
            {"school_id": str(school_id), "user_id": str(current_user.id)},
        )
    ).fetchone()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="No student record is linked to this account.",
        )

    first, last = row[2], row[3]
    data = {
        "id": str(row[0]),
        "admission_number": row[1],
        "first_name": first,
        "last_name": last,
        "full_name": f"{first or ''} {last or ''}".strip(),
        "photo_url": row[4],
        "gender": row[5],
        "date_of_birth": str(row[6]) if row[6] else None,
        "class_id": str(row[7]) if row[7] else None,
        "class_name": row[8],
        "section_id": str(row[9]) if row[9] else None,
        "section_name": row[10],
        "academic_year_id": str(row[11]) if row[11] else None,
        "roll_number": row[12],
    }
    return ok(data, "Student profile")
