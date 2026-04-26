"""
Report Service - Phase 22
REPORT_REGISTRY pattern with pluggable report classes.

SQL fixes:
  - student_list: deleted_at IS NULL, is_current=true, class filter on en.class_id
  - student_attendance: JOIN attendance_sessions for date (sa.attendance_date does not exist)
  - low_attendance: same attendance_sessions fix
  - staff_list: deleted_at IS NULL
  - staff_attendance: added department filter, attendance_pct column

New reports: class_fee_summary, exam_results, leave_report, birthday_report
"""
from __future__ import annotations

import abc
from typing import Any, Dict, List, Optional, Type

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

REPORT_REGISTRY: Dict[str, Type["BaseReport"]] = {}


def register_report(report_id: str):
    def decorator(cls: Type["BaseReport"]):
        REPORT_REGISTRY[report_id] = cls
        return cls
    return decorator


class BaseReport(abc.ABC):
    def __init__(self, school_id: str, year_id: Optional[str], filters: Dict[str, Any], db: AsyncSession):
        self.school_id = school_id
        self.year_id = year_id
        self.filters = filters
        self.db = db

    @abc.abstractmethod
    async def generate(self) -> List[Dict[str, Any]]: ...

    async def _rows(self, sql: str, params: dict) -> List[Dict[str, Any]]:
        r = await self.db.execute(text(sql), params)
        keys = list(r.keys())
        return [dict(zip(keys, row)) for row in r.fetchall()]


# ---------------------------------------------------------------------------
# Student Reports
# ---------------------------------------------------------------------------

@register_report("student_list")
class StudentListReport(BaseReport):
    async def generate(self) -> List[Dict[str, Any]]:
        f = self.filters
        conditions = ["s.school_id = :school_id", "s.deleted_at IS NULL"]
        p: Dict[str, Any] = {"school_id": self.school_id}
        if f.get("class_id"):
            conditions.append("en.class_id = :class_id")
            p["class_id"] = f["class_id"]
        if f.get("gender"):
            conditions.append("s.gender = :gender")
            p["gender"] = f["gender"]
        if f.get("status"):
            conditions.append("s.is_active = :status")
            p["status"] = True if f["status"] == "active" else False
        where = " AND ".join(conditions)
        return await self._rows(f"""
            SELECT s.admission_number,
                   s.first_name || ' ' || s.last_name AS name,
                   s.gender, s.date_of_birth, s.is_active,
                   c.name AS class_name, sec.name AS section_name
            FROM students s
            LEFT JOIN student_enrollments en
                ON en.student_id = s.id AND en.is_current = true
            LEFT JOIN sections sec ON en.section_id = sec.id
            LEFT JOIN classes c ON en.class_id = c.id
            WHERE {where}
            ORDER BY c.name NULLS LAST, sec.name NULLS LAST, s.first_name
        """, p)


@register_report("fee_defaulters")
class FeeDefaultersReport(BaseReport):
    async def generate(self) -> List[Dict[str, Any]]:
        p: Dict[str, Any] = {"school_id": self.school_id}
        class_filter = ""
        if self.filters.get("class_id"):
            class_filter = "AND en.class_id = :class_id"
            p["class_id"] = self.filters["class_id"]
        return await self._rows(f"""
            SELECT s.admission_number,
                   s.first_name || ' ' || s.last_name AS name,
                   c.name AS class_name,
                   SUM(fi.balance_amount) AS outstanding_amount,
                   COUNT(fi.id) AS invoice_count
            FROM fee_invoices fi
            JOIN students s ON fi.student_id = s.id
            LEFT JOIN student_enrollments en
                ON en.student_id = s.id AND en.is_current = true
            LEFT JOIN classes c ON en.class_id = c.id
            WHERE fi.school_id = :school_id
              AND fi.status NOT IN ('paid', 'cancelled')
              AND fi.balance_amount > 0
              {class_filter}
            GROUP BY s.admission_number, s.first_name, s.last_name, c.name
            HAVING SUM(fi.balance_amount) > 0
            ORDER BY outstanding_amount DESC
        """, p)


@register_report("fee_collection")
class FeeCollectionReport(BaseReport):
    async def generate(self) -> List[Dict[str, Any]]:
        f = self.filters
        p: Dict[str, Any] = {"school_id": self.school_id}
        conditions = ["fp.school_id = :school_id"]
        if f.get("date_from"):
            conditions.append("fp.payment_date >= :date_from")
            p["date_from"] = f["date_from"]
        if f.get("date_to"):
            conditions.append("fp.payment_date <= :date_to")
            p["date_to"] = f["date_to"]
        where = " AND ".join(conditions)
        return await self._rows(f"""
            SELECT fp.payment_date, fp.receipt_number,
                   s.admission_number,
                   s.first_name || ' ' || s.last_name AS name,
                   fp.amount, fp.payment_method
            FROM fee_payments fp
            JOIN fee_invoices fi ON fp.invoice_id = fi.id
            JOIN students s ON fi.student_id = s.id
            WHERE {where}
            ORDER BY fp.payment_date DESC
        """, p)


@register_report("class_fee_summary")
class ClassFeeSummaryReport(BaseReport):
    async def generate(self) -> List[Dict[str, Any]]:
        p: Dict[str, Any] = {"school_id": self.school_id}
        year_filter = ""
        if self.year_id:
            year_filter = "AND fi.academic_year_id = :year_id"
            p["year_id"] = self.year_id
        return await self._rows(f"""
            SELECT c.name AS class_name,
                   COUNT(DISTINCT fi.student_id) AS student_count,
                   SUM(fi.total_amount) AS total_billed,
                   SUM(fi.paid_amount)  AS total_collected,
                   SUM(fi.balance_amount) AS total_outstanding
            FROM fee_invoices fi
            LEFT JOIN student_enrollments en
                ON en.student_id = fi.student_id AND en.is_current = true
            LEFT JOIN classes c ON en.class_id = c.id
            WHERE fi.school_id = :school_id {year_filter}
            GROUP BY c.name
            ORDER BY c.name NULLS LAST
        """, p)


# ---------------------------------------------------------------------------
# Attendance Reports
# ---------------------------------------------------------------------------

@register_report("student_attendance")
class StudentAttendanceReport(BaseReport):
    async def generate(self) -> List[Dict[str, Any]]:
        f = self.filters
        p: Dict[str, Any] = {"school_id": self.school_id}
        conditions = ["sa.school_id = :school_id"]
        if f.get("class_id"):
            conditions.append("en.class_id = :class_id")
            p["class_id"] = f["class_id"]
        if f.get("month"):
            conditions.append("EXTRACT(MONTH FROM asn.date) = :month")
            p["month"] = int(f["month"])
        if f.get("year"):
            conditions.append("EXTRACT(YEAR FROM asn.date) = :year")
            p["year"] = int(f["year"])
        where = " AND ".join(conditions)
        return await self._rows(f"""
            SELECT s.admission_number,
                   s.first_name || ' ' || s.last_name AS name,
                   c.name AS class_name,
                   COUNT(*) AS total_days,
                   SUM(CASE WHEN sa.status = 'present' THEN 1 ELSE 0 END) AS present_days,
                   SUM(CASE WHEN sa.status = 'absent'  THEN 1 ELSE 0 END) AS absent_days,
                   SUM(CASE WHEN sa.status = 'late'    THEN 1 ELSE 0 END) AS late_days,
                   ROUND(SUM(CASE WHEN sa.status = 'present' THEN 1.0 ELSE 0 END)
                         * 100.0 / GREATEST(COUNT(*), 1), 1) AS attendance_pct
            FROM student_attendance sa
            JOIN attendance_sessions asn ON sa.session_id = asn.id
            JOIN students s ON sa.student_id = s.id
            LEFT JOIN student_enrollments en
                ON en.student_id = s.id AND en.is_current = true
            LEFT JOIN classes c ON en.class_id = c.id
            WHERE {where}
            GROUP BY s.admission_number, s.first_name, s.last_name, c.name
            ORDER BY c.name NULLS LAST, attendance_pct
        """, p)


@register_report("low_attendance")
class LowAttendanceReport(BaseReport):
    async def generate(self) -> List[Dict[str, Any]]:
        f = self.filters
        threshold = int(f.get("threshold_pct", 75))
        p: Dict[str, Any] = {"school_id": self.school_id, "threshold": threshold}
        conditions = ["sa.school_id = :school_id"]
        if f.get("class_id"):
            conditions.append("en.class_id = :class_id")
            p["class_id"] = f["class_id"]
        if f.get("month"):
            conditions.append("EXTRACT(MONTH FROM asn.date) = :month")
            p["month"] = int(f["month"])
        if f.get("year"):
            conditions.append("EXTRACT(YEAR FROM asn.date) = :year")
            p["year"] = int(f["year"])
        where = " AND ".join(conditions)
        return await self._rows(f"""
            SELECT s.admission_number,
                   s.first_name || ' ' || s.last_name AS name,
                   c.name AS class_name,
                   COUNT(*) AS total_days,
                   SUM(CASE WHEN sa.status = 'present' THEN 1 ELSE 0 END) AS present_days,
                   ROUND(SUM(CASE WHEN sa.status = 'present' THEN 1.0 ELSE 0 END)
                         * 100.0 / GREATEST(COUNT(*), 1), 1) AS attendance_pct
            FROM student_attendance sa
            JOIN attendance_sessions asn ON sa.session_id = asn.id
            JOIN students s ON sa.student_id = s.id
            LEFT JOIN student_enrollments en
                ON en.student_id = s.id AND en.is_current = true
            LEFT JOIN classes c ON en.class_id = c.id
            WHERE {where}
            GROUP BY s.admission_number, s.first_name, s.last_name, c.name
            HAVING ROUND(SUM(CASE WHEN sa.status = 'present' THEN 1.0 ELSE 0 END)
                         * 100.0 / GREATEST(COUNT(*), 1), 1) < :threshold
            ORDER BY attendance_pct, c.name NULLS LAST
        """, p)


# ---------------------------------------------------------------------------
# Staff Reports
# ---------------------------------------------------------------------------

@register_report("staff_list")
class StaffListReport(BaseReport):
    async def generate(self) -> List[Dict[str, Any]]:
        p: Dict[str, Any] = {"school_id": self.school_id}
        conditions = ["st.school_id = :school_id", "st.deleted_at IS NULL"]
        if self.filters.get("department_id"):
            conditions.append("st.department_id = :department_id")
            p["department_id"] = self.filters["department_id"]
        where = " AND ".join(conditions)
        return await self._rows(f"""
            SELECT st.employee_id,
                   st.first_name || ' ' || st.last_name AS name,
                   d.name AS department, des.name AS designation,
                   st.date_of_joining, st.employment_type, st.is_active
            FROM staff st
            LEFT JOIN departments d ON st.department_id = d.id
            LEFT JOIN designations des ON st.designation_id = des.id
            WHERE {where}
            ORDER BY d.name NULLS LAST, st.first_name
        """, p)


@register_report("staff_attendance")
class StaffAttendanceReport(BaseReport):
    async def generate(self) -> List[Dict[str, Any]]:
        f = self.filters
        p: Dict[str, Any] = {"school_id": self.school_id}
        conditions = ["sa.school_id = :school_id"]
        if f.get("month"):
            conditions.append("EXTRACT(MONTH FROM sa.date) = :month")
            p["month"] = int(f["month"])
        if f.get("year"):
            conditions.append("EXTRACT(YEAR FROM sa.date) = :year")
            p["year"] = int(f["year"])
        if f.get("department_id"):
            conditions.append("st.department_id = :department_id")
            p["department_id"] = f["department_id"]
        where = " AND ".join(conditions)
        return await self._rows(f"""
            SELECT st.employee_id,
                   st.first_name || ' ' || st.last_name AS name,
                   d.name AS department,
                   COUNT(*) AS total_days,
                   SUM(CASE WHEN sa.status = 'present'  THEN 1 ELSE 0 END) AS present_days,
                   SUM(CASE WHEN sa.status = 'absent'   THEN 1 ELSE 0 END) AS absent_days,
                   SUM(CASE WHEN sa.status = 'half_day' THEN 1 ELSE 0 END) AS half_days,
                   SUM(CASE WHEN sa.status = 'on_leave' THEN 1 ELSE 0 END) AS on_leave_days,
                   ROUND(SUM(CASE WHEN sa.status = 'present' THEN 1.0 ELSE 0 END)
                         * 100.0 / GREATEST(COUNT(*), 1), 1) AS attendance_pct
            FROM staff_attendance sa
            JOIN staff st ON sa.staff_id = st.id
            LEFT JOIN departments d ON st.department_id = d.id
            WHERE {where}
            GROUP BY st.employee_id, st.first_name, st.last_name, d.name
            ORDER BY d.name NULLS LAST, st.first_name
        """, p)


@register_report("leave_report")
class LeaveReport(BaseReport):
    async def generate(self) -> List[Dict[str, Any]]:
        f = self.filters
        p: Dict[str, Any] = {"school_id": self.school_id}
        conditions = ["sl.school_id = :school_id"]
        if f.get("department_id"):
            conditions.append("st.department_id = :department_id")
            p["department_id"] = f["department_id"]
        if f.get("status"):
            conditions.append("sl.status = :status")
            p["status"] = f["status"]
        if f.get("date_from"):
            conditions.append("sl.from_date >= :date_from")
            p["date_from"] = f["date_from"]
        if f.get("date_to"):
            conditions.append("sl.to_date <= :date_to")
            p["date_to"] = f["date_to"]
        where = " AND ".join(conditions)
        return await self._rows(f"""
            SELECT st.employee_id,
                   st.first_name || ' ' || st.last_name AS staff_name,
                   d.name AS department, lt.name AS leave_type,
                   sl.from_date, sl.to_date, sl.days_count AS days,
                   sl.status, sl.reason
            FROM staff_leaves sl
            JOIN staff st ON sl.staff_id = st.id
            LEFT JOIN departments d ON st.department_id = d.id
            LEFT JOIN leave_types lt ON sl.leave_type_id = lt.id
            WHERE {where}
            ORDER BY sl.from_date DESC
        """, p)


# ---------------------------------------------------------------------------
# Finance Reports
# ---------------------------------------------------------------------------

@register_report("monthly_pl")
class MonthlyPLReport(BaseReport):
    async def generate(self) -> List[Dict[str, Any]]:
        f = self.filters
        p: Dict[str, Any] = {"school_id": self.school_id}
        inc_f = exp_f = ""
        if f.get("year"):
            inc_f += " AND EXTRACT(YEAR FROM ir.income_date) = :year"
            exp_f += " AND EXTRACT(YEAR FROM er.expense_date) = :year"
            p["year"] = int(f["year"])
        if f.get("month"):
            inc_f += " AND EXTRACT(MONTH FROM ir.income_date) = :month"
            exp_f += " AND EXTRACT(MONTH FROM er.expense_date) = :month"
            p["month"] = int(f["month"])
        income_rows = await self._rows(f"""
            SELECT ic.name AS category, SUM(ir.amount) AS total
            FROM income_records ir
            JOIN income_categories ic ON ir.category_id = ic.id
            WHERE ir.school_id = :school_id {inc_f}
            GROUP BY ic.name ORDER BY ic.name
        """, p)
        expense_rows = await self._rows(f"""
            SELECT ec.name AS category, SUM(er.amount) AS total
            FROM expense_records er
            JOIN expense_categories ec ON er.category_id = ec.id
            WHERE er.school_id = :school_id {exp_f}
            GROUP BY ec.name ORDER BY ec.name
        """, p)
        total_income  = sum(r["total"] or 0 for r in income_rows)
        total_expense = sum(r["total"] or 0 for r in expense_rows)
        return (
            [{"type": "Income",  "category": r["category"], "amount": r["total"]} for r in income_rows]
            + [{"type": "Expense", "category": r["category"], "amount": r["total"]} for r in expense_rows]
            + [{"type": "SUMMARY", "category": "Net P&L", "amount": total_income - total_expense}]
        )


@register_report("income_expense")
class IncomeExpenseReport(BaseReport):
    async def generate(self) -> List[Dict[str, Any]]:
        f = self.filters
        p: Dict[str, Any] = {"school_id": self.school_id}
        inc_f = exp_f = ""
        if f.get("year"):
            inc_f += " AND EXTRACT(YEAR FROM ir.income_date) = :year"
            exp_f += " AND EXTRACT(YEAR FROM er.expense_date) = :year"
            p["year"] = int(f["year"])
        if f.get("month"):
            inc_f += " AND EXTRACT(MONTH FROM ir.income_date) = :month"
            exp_f += " AND EXTRACT(MONTH FROM er.expense_date) = :month"
            p["month"] = int(f["month"])
        income = await self._rows(f"""
            SELECT 'income' AS type, ic.name AS category, ir.amount,
                   ir.income_date AS transaction_date, ir.description
            FROM income_records ir
            JOIN income_categories ic ON ir.category_id = ic.id
            WHERE ir.school_id = :school_id {inc_f}
        """, p)
        expense = await self._rows(f"""
            SELECT 'expense' AS type, ec.name AS category, er.amount,
                   er.expense_date AS transaction_date, er.description
            FROM expense_records er
            JOIN expense_categories ec ON er.category_id = ec.id
            WHERE er.school_id = :school_id {exp_f}
        """, p)
        return sorted(income + expense, key=lambda x: x["transaction_date"] or "", reverse=True)


# ---------------------------------------------------------------------------
# Other Reports
# ---------------------------------------------------------------------------

@register_report("exam_results")
class ExamResultsReport(BaseReport):
    async def generate(self) -> List[Dict[str, Any]]:
        f = self.filters
        p: Dict[str, Any] = {"school_id": self.school_id}
        conditions = ["sm.school_id = :school_id"]
        if f.get("class_id"):
            conditions.append("e.class_id = :class_id")
            p["class_id"] = f["class_id"]
        if f.get("exam_type_id"):
            conditions.append("e.exam_type_id = :exam_type_id")
            p["exam_type_id"] = f["exam_type_id"]
        if self.year_id:
            conditions.append("e.academic_year_id = :year_id")
            p["year_id"] = self.year_id
        where = " AND ".join(conditions)
        return await self._rows(f"""
            SELECT e.name AS exam_name, et.name AS exam_type,
                   c.name AS class_name,
                   e.full_marks, e.pass_marks,
                   COUNT(sm.id) AS total_students,
                   SUM(CASE WHEN sm.is_absent THEN 1 ELSE 0 END) AS absent_count,
                   SUM(CASE WHEN NOT sm.is_absent
                             AND sm.marks_obtained >= e.pass_marks THEN 1 ELSE 0 END) AS passed,
                   SUM(CASE WHEN NOT sm.is_absent
                             AND sm.marks_obtained < e.pass_marks  THEN 1 ELSE 0 END) AS failed,
                   ROUND(AVG(CASE WHEN NOT sm.is_absent THEN sm.marks_obtained END), 1) AS avg_marks,
                   MAX(sm.marks_obtained) AS highest_marks,
                   MIN(CASE WHEN NOT sm.is_absent THEN sm.marks_obtained END) AS lowest_marks
            FROM student_marks sm
            JOIN exams e ON sm.exam_id = e.id
            JOIN exam_types et ON e.exam_type_id = et.id
            JOIN classes c ON e.class_id = c.id
            WHERE {where}
            GROUP BY e.name, et.name, c.name, e.full_marks, e.pass_marks
            ORDER BY c.name, e.name
        """, p)


@register_report("birthday_report")
class BirthdayReport(BaseReport):
    async def generate(self) -> List[Dict[str, Any]]:
        f = self.filters
        p: Dict[str, Any] = {"school_id": self.school_id}
        conditions = ["s.school_id = :school_id", "s.deleted_at IS NULL", "s.is_active = true"]
        if f.get("month"):
            conditions.append("EXTRACT(MONTH FROM s.date_of_birth) = :month")
            p["month"] = int(f["month"])
        else:
            conditions.append("EXTRACT(MONTH FROM s.date_of_birth) = EXTRACT(MONTH FROM CURRENT_DATE)")
        if f.get("class_id"):
            conditions.append("en.class_id = :class_id")
            p["class_id"] = f["class_id"]
        where = " AND ".join(conditions)
        return await self._rows(f"""
            SELECT s.admission_number,
                   s.first_name || ' ' || s.last_name AS name,
                   s.date_of_birth,
                   EXTRACT(DAY   FROM s.date_of_birth)::int AS birth_day,
                   EXTRACT(MONTH FROM s.date_of_birth)::int AS birth_month,
                   c.name AS class_name, sec.name AS section_name
            FROM students s
            LEFT JOIN student_enrollments en
                ON en.student_id = s.id AND en.is_current = true
            LEFT JOIN classes c ON en.class_id = c.id
            LEFT JOIN sections sec ON en.section_id = sec.id
            WHERE {where}
            ORDER BY EXTRACT(DAY FROM s.date_of_birth), c.name NULLS LAST
        """, p)


# ---------------------------------------------------------------------------
# Service entry point
# ---------------------------------------------------------------------------

async def run_report(
    report_id: str,
    school_id: str,
    year_id: Optional[str],
    filters: Dict[str, Any],
    db: AsyncSession,
) -> List[Dict[str, Any]]:
    cls = REPORT_REGISTRY.get(report_id)
    if cls is None:
        raise ValueError(f"Unknown report: {report_id}")
    return await cls(school_id=school_id, year_id=year_id, filters=filters, db=db).generate()
