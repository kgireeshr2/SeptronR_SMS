from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, func, select

from app.core.dependencies import get_school_id, get_current_user
from app.db.session import get_db
from app.models.auth import User

dashboard_router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


async def _scalar(db: AsyncSession, q: str, params: dict) -> int:
    """Execute a raw count query and return the integer."""
    result = await db.execute(text(q), params)
    row = result.fetchone()
    return int(row[0]) if row and row[0] is not None else 0


@dashboard_router.get("/admin")
async def admin_dashboard(
    year_id: Optional[UUID] = Query(None),
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    p = {"school_id": school_id}

    total_students = await _scalar(
        db,
        "SELECT COUNT(*) FROM students WHERE school_id = :school_id AND is_active=true",
        p,
    )
    total_staff = await _scalar(
        db, "SELECT COUNT(*) FROM staff WHERE school_id = :school_id AND is_active=true", p
    )
    total_fee_collected_this_month = await _scalar(
        db,
        """SELECT COALESCE(SUM(amount), 0) FROM fee_payments
           WHERE school_id = :school_id
             AND DATE_TRUNC('month', payment_date)
               = DATE_TRUNC('month', NOW())""",
        p,
    )
    total_fee_outstanding = await _scalar(
        db,
        """SELECT COALESCE(SUM(balance_amount), 0) FROM fee_invoices
           WHERE school_id = :school_id AND status NOT IN ('paid', 'cancelled')""",
        p,
    )
    total_present_today = await _scalar(
        db,
        """SELECT COUNT(*) FROM student_attendance sa
           JOIN attendance_sessions ats ON sa.session_id = ats.id
           WHERE sa.school_id = :school_id AND ats.date = CAST(NOW() AS DATE) AND sa.status = 'present'""",
        p,
    )
    total_absent_today = await _scalar(
        db,
        """SELECT COUNT(*) FROM student_attendance sa
           JOIN attendance_sessions ats ON sa.session_id = ats.id
           WHERE sa.school_id = :school_id AND ats.date = CAST(NOW() AS DATE) AND sa.status = 'absent'""",
        p,
    )
    pending_leave_requests = await _scalar(
        db,
        "SELECT COUNT(*) FROM staff_leaves WHERE school_id = :school_id AND status = 'pending'",
        p,
    )

    # Monthly fee collection last 6 months
    fee_trend_raw = await db.execute(
        text(
            """SELECT TO_CHAR(DATE_TRUNC('month', payment_date), 'Mon YYYY') AS month,
                      COALESCE(SUM(amount), 0) AS amount
               FROM fee_payments
               WHERE school_id = :school_id
                 AND payment_date >= (NOW() - INTERVAL '6 months')
               GROUP BY DATE_TRUNC('month', payment_date)
               ORDER BY DATE_TRUNC('month', payment_date)"""
        ),
        p,
    )
    monthly_fee_collection = [{"month": r[0], "amount": int(r[1])} for r in fee_trend_raw.fetchall()]

    # Student gender breakdown
    gender_raw = await db.execute(
        text(
            """SELECT COALESCE(gender, 'other') AS gender, COUNT(*) AS cnt
               FROM students WHERE school_id = :school_id AND is_active=true
               GROUP BY gender"""
        ),
        p,
    )
    gender_rows = gender_raw.fetchall()
    gender_map: dict = {"male": 0, "female": 0, "other": 0}
    for row in gender_rows:
        key = str(row[0]).lower()
        if key in gender_map:
            gender_map[key] = int(row[1])
        else:
            gender_map["other"] += int(row[1])

    # Students per class (via enrollments)
    class_raw = await db.execute(
        text(
            """SELECT c.name AS class_name, COUNT(se.student_id) AS cnt
               FROM student_enrollments se
               JOIN classes c ON se.class_id = c.id
               WHERE se.school_id = :school_id AND se.is_current = true
               GROUP BY c.name ORDER BY c.name"""
        ),
        p,
    )
    student_by_class = [{"class_name": r[0], "count": int(r[1])} for r in class_raw.fetchall()]

    # Upcoming calendar events (next 7 days)
    events_raw = await db.execute(
        text(
            """SELECT title, event_type, start_datetime FROM calendar_events
               WHERE school_id = :school_id
                 AND start_datetime BETWEEN NOW() AND (NOW() + INTERVAL '7 days')
                 AND is_active=true
               ORDER BY start_datetime
               LIMIT 5"""
        ),
        p,
    )
    upcoming_events = [
        {"title": r[0], "event_type": r[1], "start_datetime": str(r[2])}
        for r in events_raw.fetchall()
    ]

    # Low stock alerts
    stock_raw = await db.execute(
        text(
            """SELECT name, current_stock, min_stock_level FROM items
               WHERE school_id = :school_id AND current_stock <= min_stock_level LIMIT 5"""
        ),
        p,
    )
    low_stock_alerts = [
        {"name": r[0], "current_stock": int(r[1]), "reorder_level": int(r[2])}
        for r in stock_raw.fetchall()
    ]

    attendance_pct = (
        round(total_present_today / (total_present_today + total_absent_today) * 100, 1)
        if (total_present_today + total_absent_today) > 0
        else 0.0
    )

    return {
        "total_students": total_students,
        "total_staff": total_staff,
        "total_fee_collected_this_month": total_fee_collected_this_month,
        "total_fee_outstanding": total_fee_outstanding,
        "total_present_today": total_present_today,
        "total_absent_today": total_absent_today,
        "attendance_pct_today": attendance_pct,
        "pending_leave_requests": pending_leave_requests,
        "monthly_fee_collection": monthly_fee_collection,
        "student_by_class": student_by_class,
        "student_by_gender": gender_map,
        "upcoming_events": upcoming_events,
        "low_stock_alerts": low_stock_alerts,
    }


@dashboard_router.get("/teacher")
async def teacher_dashboard(
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    p = {"school_id": school_id, "user_id": str(current_user.id)}

    pending_hw_reviews = await _scalar(
        db,
        """SELECT COUNT(*) FROM homework_submissions hs
           JOIN homework h ON hs.homework_id = h.id
           WHERE h.school_id = :school_id AND h.teacher_id = :user_id
             AND hs.marks_given IS NULL""",
        p,
    )

    upcoming_exams_raw = await db.execute(
        text(
            """SELECT e.name, e.exam_date FROM exams e
               WHERE e.school_id = :school_id
                 AND e.exam_date BETWEEN CAST(NOW() AS DATE) AND (NOW() + INTERVAL '14 days')
               ORDER BY e.exam_date
               LIMIT 5"""
        ),
        p,
    )
    upcoming_exams = [{"name": r[0], "exam_date": str(r[1])} for r in upcoming_exams_raw.fetchall()]

    return {
        "pending_homework_reviews": pending_hw_reviews,
        "upcoming_exams": upcoming_exams,
    }


@dashboard_router.get("/student")
async def student_dashboard(
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    p = {"school_id": school_id, "user_id": str(current_user.id)}

    # Student's fee outstanding
    fee_due = await _scalar(
        db,
        """SELECT COALESCE(SUM(fi.balance_amount), 0) FROM fee_invoices fi
           JOIN students s ON fi.student_id = s.id
           WHERE fi.school_id = :school_id AND s.user_id = :user_id
             AND fi.status NOT IN ('paid', 'cancelled')""",
        p,
    )

    upcoming_exams_raw = await db.execute(
        text(
            """SELECT e.name, e.exam_date FROM exams e
               WHERE e.school_id = :school_id
                 AND e.exam_date >= CAST(NOW() AS DATE)
               ORDER BY e.exam_date
               LIMIT 5"""
        ),
        p,
    )
    upcoming_exams = [{'name': r[0], 'exam_date': str(r[1])} for r in upcoming_exams_raw.fetchall()]

    homework_due_raw = await db.execute(
        text(
            """SELECT h.title, h.due_date FROM homework h
               JOIN students s ON s.school_id = h.school_id
               WHERE h.school_id = :school_id AND s.user_id = :user_id
                 AND h.due_date >= CAST(NOW() AS DATE)
               ORDER BY h.due_date
               LIMIT 5"""
        ),
        p,
    )
    homework_due = [{"title": r[0], "due_date": str(r[1])} for r in homework_due_raw.fetchall()]

    return {
        "fee_outstanding": fee_due,
        "upcoming_exams": upcoming_exams,
        "homework_due": homework_due,
    }


@dashboard_router.get("/parent")
async def parent_dashboard(
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dashboard for parent role — returns data for all children of the logged-in parent."""
    p = {"school_id": school_id, "user_id": str(current_user.id)}

    # Get children linked to this parent user
    children_raw = await db.execute(
        text(
            """SELECT s.id, s.first_name, s.last_name, s.admission_number,
                      c.name AS class_name, sec.name AS section_name
               FROM students s
               LEFT JOIN classes c ON s.class_id = c.id
               LEFT JOIN sections sec ON s.section_id = sec.id
               WHERE s.school_id = :school_id AND s.parent_id = :user_id AND s.is_active=true"""
        ),
        p,
    )
    children = [
        {
            "id": str(r[0]),
            "name": f"{r[1] or ''} {r[2] or ''}".strip(),
            "admission_number": r[3],
            "class_name": r[4],
            "section_name": r[5],
        }
        for r in children_raw.fetchall()
    ]

    child_ids = [c["id"] for c in children]

    # Fee outstanding for all children
    total_fee_due = 0
    if child_ids:
        ids_str = ",".join(f"'{cid}'" for cid in child_ids)
        total_fee_due = await _scalar(
            db,
            f"""SELECT COALESCE(SUM(balance_amount), 0) FROM fee_invoices
                WHERE school_id = :school_id AND student_id IN ({ids_str})
                  AND status NOT IN ('paid', 'cancelled')""",
            {"school_id": school_id},
        )

    # Today's attendance for all children
    attendance_today = []
    if child_ids:
        ids_str = ",".join(f"'{cid}'" for cid in child_ids)
        att_raw = await db.execute(
            text(
                f"""SELECT sa.student_id, sa.status
                    FROM student_attendance sa
                    JOIN attendance_sessions ats ON sa.session_id = ats.id
                    WHERE sa.school_id = :school_id
                      AND ats.date = CAST(NOW() AS DATE)
                      AND sa.student_id IN ({ids_str})"""
            ),
            {"school_id": school_id},
        )
        attendance_today = [{"student_id": str(r[0]), "status": r[1]} for r in att_raw.fetchall()]

    # Upcoming exams
    upcoming_exams_raw = await db.execute(
        text(
            """SELECT e.name, e.exam_date FROM exams e
               WHERE e.school_id = :school_id
                 AND e.exam_date >= CAST(NOW() AS DATE)
               ORDER BY e.exam_date
               LIMIT 5"""
        ),
        {"school_id": school_id},
    )
    upcoming_exams = [{'name': r[0], 'exam_date': str(r[1])} for r in upcoming_exams_raw.fetchall()]

    # Homework due
    homework_due_raw = await db.execute(
        text(
            """SELECT h.title, h.due_date, h.subject_id FROM homework h
               WHERE h.school_id = :school_id
                 AND h.due_date >= CAST(NOW() AS DATE)
               ORDER BY h.due_date
               LIMIT 5"""
        ),
        {"school_id": school_id},
    )
    homework_due = [{"title": r[0], "due_date": str(r[1])} for r in homework_due_raw.fetchall()]

    # Announcements (latest 5)
    announcements_raw = await db.execute(
        text(
            """SELECT title, content, created_at FROM announcements
               WHERE school_id = :school_id AND is_active=true
               ORDER BY created_at DESC LIMIT 5"""
        ),
        {"school_id": school_id},
    )
    announcements = [
        {"title": r[0], "content": r[1], "created_at": str(r[2])}
        for r in announcements_raw.fetchall()
    ]

    return {
        "children": children,
        "total_fee_outstanding": total_fee_due,
        "attendance_today": attendance_today,
        "upcoming_exams": upcoming_exams,
        "homework_due": homework_due,
        "announcements": announcements,
    }
