"""
Report Service — Phase 22
REPORT_REGISTRY pattern with pluggable report classes.
"""
from __future__ import annotations

import abc
from typing import Any, Dict, List, Optional, Type
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

REPORT_REGISTRY: Dict[str, Type["BaseReport"]] = {}


def register_report(report_id: str):
    """Decorator to register a report class."""
    def decorator(cls: Type[BaseReport]):
        REPORT_REGISTRY[report_id] = cls
        return cls
    return decorator


class BaseReport(abc.ABC):
    def __init__(
        self,
        school_id: str,
        year_id: Optional[str],
        filters: Dict[str, Any],
        db: AsyncSession,
    ):
        self.school_id = school_id
        self.year_id = year_id
        self.filters = filters
        self.db = db

    @abc.abstractmethod
    async def generate(self) -> List[Dict[str, Any]]:
        """Return list of row dicts for the report."""

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
        f = self.filters
        conditions = ["s.school_id = :school_id", "COALESCE(s.deleted_at, '') = ''"]
        p: Dict[str, Any] = {"school_id": self.school_id}
        if f.get("class_id"):
            conditions.append("se.class_id = :class_id")
            p["class_id"] = f["class_id"]
        if f.get("gender"):
            conditions.append("s.gender = :gender")
            p["gender"] = f["gender"]
        if f.get("status"):
            conditions.append("s.is_active = :status")
            p["status"] = 1 if f["status"] == "active" else 0
        where = " AND ".join(conditions)
        return await self._rows(
            f"""SELECT s.admission_number, s.first_name || ' ' || s.last_name AS name,
                       s.gender, s.date_of_birth, s.is_active,
                       c.name AS class_name, se.name AS section_name
                FROM students s
                LEFT JOIN student_enrollments en ON en.student_id = s.id AND en.is_current = 1
                LEFT JOIN sections se ON en.section_id = se.id
                LEFT JOIN classes c ON en.class_id = c.id
                WHERE {where}
                ORDER BY c.name, se.name, s.first_name""",
            p,
        )


@register_report("fee_defaulters")
class FeeDefaultersReport(BaseReport):
    async def generate(self) -> List[Dict[str, Any]]:
        p = {"school_id": self.school_id}
        return await self._rows(
            """SELECT s.admission_number, s.first_name || ' ' || s.last_name AS name,
                      c.name AS class_name,
                      SUM(fi.balance_amount) AS outstanding_amount
               FROM fee_invoices fi
               JOIN students s ON fi.student_id = s.id
               LEFT JOIN student_enrollments en ON en.student_id = s.id AND en.is_current = 1
               LEFT JOIN classes c ON en.class_id = c.id
               WHERE fi.school_id = :school_id AND fi.status NOT IN ('paid', 'cancelled')
               GROUP BY s.admission_number, s.first_name, s.last_name, c.name
               HAVING SUM(fi.balance_amount) > 0
               ORDER BY outstanding_amount DESC""",
            p,
        )


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
        return await self._rows(
            f"""SELECT fp.payment_date, fp.receipt_number,
                       s.admission_number, s.first_name || ' ' || s.last_name AS name,
                       fp.amount, fp.payment_method
                FROM fee_payments fp
                JOIN fee_invoices fi ON fp.invoice_id = fi.id
                JOIN students s ON fi.student_id = s.id
                WHERE {where}
                ORDER BY fp.payment_date DESC""",
            p,
        )


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
            conditions.append("EXTRACT(MONTH FROM sa.attendance_date) = :month")
            p["month"] = f["month"]
        if f.get("year"):
            conditions.append("EXTRACT(YEAR FROM sa.attendance_date) = :year")
            p["year"] = f["year"]
        where = " AND ".join(conditions)
        return await self._rows(
            f"""SELECT s.admission_number, s.first_name || ' ' || s.last_name AS name,
                       SUM(CASE WHEN sa.status = 'present' THEN 1 ELSE 0 END) AS present_days,
                       SUM(CASE WHEN sa.status = 'absent' THEN 1 ELSE 0 END) AS absent_days,
                       COUNT(*) AS total_days,
                       CASE WHEN COUNT(*) = 0 THEN 0
                            ELSE ROUND(SUM(CASE WHEN sa.status = 'present' THEN 1.0 ELSE 0 END) * 100.0 / COUNT(*), 1)
                       END AS attendance_pct
                FROM student_attendance sa
                JOIN students s ON sa.student_id = s.id
                LEFT JOIN student_enrollments en ON en.student_id = s.id AND en.is_current = 1
                WHERE {where}
                GROUP BY s.admission_number, s.first_name, s.last_name
                ORDER BY attendance_pct""",
            p,
        )


@register_report("staff_list")
class StaffListReport(BaseReport):
    async def generate(self) -> List[Dict[str, Any]]:
        p = {"school_id": self.school_id}
        conditions = ["st.school_id = :school_id", "COALESCE(st.deleted_at, '') = ''"]
        if self.filters.get("department_id"):
            conditions.append("st.department_id = :department_id")
            p["department_id"] = self.filters["department_id"]
        where = " AND ".join(conditions)
        return await self._rows(
            f"""SELECT st.employee_id, st.first_name || ' ' || st.last_name AS name,
                      d.name AS department, des.name AS designation,
                      st.date_of_joining, st.employment_type, st.is_active
               FROM staff st
               LEFT JOIN departments d ON st.department_id = d.id
               LEFT JOIN designations des ON st.designation_id = des.id
               WHERE {where}
               ORDER BY d.name, st.first_name""",
            p,
        )


@register_report("staff_attendance")
class StaffAttendanceReport(BaseReport):
    async def generate(self) -> List[Dict[str, Any]]:
        f = self.filters
        p: Dict[str, Any] = {"school_id": self.school_id}
        conditions = ["sa.school_id = :school_id"]
        if f.get("month"):
            conditions.append("EXTRACT(MONTH FROM sa.date) = :month")
            p["month"] = f["month"]
        if f.get("year"):
            conditions.append("EXTRACT(YEAR FROM sa.date) = :year")
            p["year"] = f["year"]
        where = " AND ".join(conditions)
        return await self._rows(
            f"""SELECT st.employee_id, st.first_name || ' ' || st.last_name AS name,
                       SUM(CASE WHEN sa.status = 'present' THEN 1 ELSE 0 END) AS present_days,
                       SUM(CASE WHEN sa.status = 'absent' THEN 1 ELSE 0 END) AS absent_days,
                       SUM(CASE WHEN sa.status = 'half_day' THEN 1 ELSE 0 END) AS half_days,
                       COUNT(*) AS total_days
                FROM staff_attendance sa
                JOIN staff st ON sa.staff_id = st.id
                WHERE {where}
                GROUP BY st.employee_id, st.first_name, st.last_name
                ORDER BY st.first_name""",
            p,
        )


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
            conditions.append("EXTRACT(MONTH FROM sa.attendance_date) = :month")
            p["month"] = f["month"]
        if f.get("year"):
            conditions.append("EXTRACT(YEAR FROM sa.attendance_date) = :year")
            p["year"] = f["year"]
        where = " AND ".join(conditions)
        return await self._rows(
            f"""SELECT s.admission_number, s.first_name || ' ' || s.last_name AS name,
                       c.name AS class_name,
                       COUNT(*) AS total_days,
                       SUM(CASE WHEN sa.status = 'present' THEN 1 ELSE 0 END) AS present_days,
                       CASE WHEN COUNT(*) = 0 THEN 0
                            ELSE ROUND(SUM(CASE WHEN sa.status = 'present' THEN 1.0 ELSE 0 END) * 100.0 / COUNT(*), 1)
                       END AS attendance_pct
                FROM student_attendance sa
                JOIN students s ON sa.student_id = s.id
                LEFT JOIN student_enrollments en ON en.student_id = s.id AND en.is_current = 1
                LEFT JOIN classes c ON en.class_id = c.id
                WHERE {where}
                GROUP BY s.admission_number, s.first_name, s.last_name, c.name
                HAVING CASE WHEN COUNT(*) = 0 THEN 0
                            ELSE ROUND(SUM(CASE WHEN sa.status = 'present' THEN 1.0 ELSE 0 END) * 100.0 / COUNT(*), 1)
                       END < :threshold
                ORDER BY attendance_pct""",
            p,
        )


@register_report("monthly_pl")
class MonthlyPLReport(BaseReport):
    async def generate(self) -> List[Dict[str, Any]]:
        f = self.filters
        p: Dict[str, Any] = {"school_id": self.school_id}
        month_filter_income = ""
        month_filter_expense = ""
        if f.get("month") and f.get("year"):
            month_filter_income = "AND EXTRACT(MONTH FROM ir.income_date) = :month AND EXTRACT(YEAR FROM ir.income_date) = :year"
            month_filter_expense = "AND EXTRACT(MONTH FROM er.expense_date) = :month AND EXTRACT(YEAR FROM er.expense_date) = :year"
            p["month"] = f["month"]
            p["year"] = f["year"]
        income_rows = await self._rows(
            f"""SELECT ic.name AS category, SUM(ir.amount) AS total
                FROM income_records ir JOIN income_categories ic ON ir.category_id = ic.id
                WHERE ir.school_id = :school_id {month_filter_income}
                GROUP BY ic.name""",
            p,
        )
        expense_rows = await self._rows(
            f"""SELECT ec.name AS category, SUM(er.amount) AS total
                FROM expense_records er JOIN expense_categories ec ON er.category_id = ec.id
                WHERE er.school_id = :school_id {month_filter_expense}
                GROUP BY ec.name""",
            p,
        )
        total_income = sum(r["total"] or 0 for r in income_rows)
        total_expense = sum(r["total"] or 0 for r in expense_rows)
        rows = (
            [{"type": "Income", "category": r["category"], "amount": r["total"]} for r in income_rows]
            + [{"type": "Expense", "category": r["category"], "amount": r["total"]} for r in expense_rows]
            + [{"type": "SUMMARY", "category": "Net P&L", "amount": total_income - total_expense}]
        )
        return rows


@register_report("income_expense")
class IncomeExpenseReport(BaseReport):
    async def generate(self) -> List[Dict[str, Any]]:
        f = self.filters
        p: Dict[str, Any] = {"school_id": self.school_id}
        month_income = ""
        month_expense = ""
        if f.get("month") and f.get("year"):
            month_income = "AND EXTRACT(MONTH FROM ir.income_date) = :month AND EXTRACT(YEAR FROM ir.income_date) = :year"
            month_expense = "AND EXTRACT(MONTH FROM er.expense_date) = :month AND EXTRACT(YEAR FROM er.expense_date) = :year"
            p["month"] = f["month"]
            p["year"] = f["year"]
        income = await self._rows(
            f"""SELECT 'income' AS type, ic.name AS category, ir.amount, ir.income_date AS transaction_date, ir.description
                FROM income_records ir JOIN income_categories ic ON ir.category_id = ic.id
                WHERE ir.school_id = :school_id {month_income}""",
            p,
        )
        expense = await self._rows(
            f"""SELECT 'expense' AS type, ec.name AS category, er.amount, er.expense_date AS transaction_date, er.description
                FROM expense_records er JOIN expense_categories ec ON er.category_id = ec.id
                WHERE er.school_id = :school_id {month_expense}""",
            p,
        )
        return sorted(income + expense, key=lambda x: x["transaction_date"], reverse=True)


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
    report = cls(school_id=school_id, year_id=year_id, filters=filters, db=db)
    return await report.generate()

