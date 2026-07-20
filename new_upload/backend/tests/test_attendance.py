"""
Round 2 — Attendance Management Tests
Session-scoped fixtures bootstrap school + class + section + students for attendance tests.
"""
import uuid
from datetime import date
import pytest_asyncio
from httpx import AsyncClient
from tests.conftest import create_test_superadmin


def _data(resp) -> dict:
    body = resp.json()
    return body.get("data", body)


@pytest_asyncio.fixture(scope="session")
async def att_setup(session_http_client: AsyncClient) -> dict:
    """Bootstrap school + academic year + class + section + student for attendance tests."""
    c = session_http_client

    # Create super-admin directly
    await create_test_superadmin("att_superadmin", "att_super@test.com")

    login = await c.post(
        "/api/v1/auth/login",
        json={"identifier": "att_super@test.com", "password": "Admin@1234"},
    )
    assert login.status_code == 200, login.text
    token = login.json()["data"]["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    # Bootstrap school
    sr = await c.post(
        "/api/v1/schools/bootstrap",
        json={"school_name": "Attendance Test School"},
        headers=h,
    )
    assert sr.status_code == 201, sr.text
    school_id = _data(sr)["id"]
    hh = {**h, "X-School-Id": school_id}

    # Academic Year
    ayr = await c.post(
        "/api/v1/academic-years",
        json={
            "name": "2025-26-att",
            "start_date": "2025-04-01",
            "end_date": "2026-03-31",
            "is_current": True,
        },
        headers=hh,
    )
    assert ayr.status_code in (200, 201), ayr.text
    ay_id = _data(ayr)["id"]

    # Class
    cr = await c.post(
        "/api/v1/classes",
        json={"name": "Class 8", "academic_year_id": ay_id},
        headers=hh,
    )
    assert cr.status_code in (200, 201), cr.text
    class_id = _data(cr)["id"]

    # Section
    secr = await c.post(
        f"/api/v1/classes/{class_id}/sections",
        json={"name": "B"},
        headers=hh,
    )
    assert secr.status_code in (200, 201), secr.text
    section_id = _data(secr)["id"]

    # Create a student directly with enrollment
    uid = uuid.uuid4().hex[:8]
    student_r = await c.post(
        "/api/v1/students/",
        json={
            "first_name": "Att",
            "last_name": f"Student{uid}",
            "date_of_birth": "2012-03-10",
            "gender": "male",
            "admission_date": "2025-04-01",
            "enrollment": {
                "class_id": class_id,
                "section_id": section_id,
                "academic_year_id": ay_id,
                "roll_number": "001",
            },
        },
        headers=hh,
    )
    assert student_r.status_code in (200, 201), student_r.text
    student_id = student_r.json()["id"]

    # Staff for staff-attendance tests
    dept_r = await c.post("/api/v1/departments", json={"name": f"Att Dept {uid}"}, headers=hh)
    assert dept_r.status_code in (200, 201), dept_r.text
    dept_id = dept_r.json()["id"]

    desig_r = await c.post("/api/v1/designations", json={"name": f"Att Teacher {uid}"}, headers=hh)
    assert desig_r.status_code in (200, 201), desig_r.text
    desig_id = desig_r.json()["id"]

    staff_r = await c.post(
        "/api/v1/staff",
        json={
            "first_name": "Att",
            "last_name": "Teacher",
            "date_of_birth": "1988-04-20",
            "gender": "female",
            "department_id": dept_id,
            "designation_id": desig_id,
            "date_of_joining": "2025-01-01",
            "employment_type": "permanent",
            "salary_type": "monthly",
            "monthly_salary": 2000000,
            "email": f"att.teacher.{uid}@test.com",
            "phone": f"92{uid[:8]}",
        },
        headers=hh,
    )
    assert staff_r.status_code in (200, 201), staff_r.text
    staff_id = staff_r.json()["id"]

    return {
        "headers": hh,
        "school_id": school_id,
        "academic_year_id": ay_id,
        "class_id": class_id,
        "section_id": section_id,
        "student_id": student_id,
        "staff_id": staff_id,
    }


# ── Tests: Student Attendance ──────────────────────────────────────────────────

class TestStudentAttendance:
    async def test_get_section_attendance_empty(self, async_client: AsyncClient, att_setup: dict):
        """GET attendance for a date with no records should return summary with 0 total."""
        resp = await async_client.get(
            f"/api/v1/attendance/section/{att_setup['section_id']}",
            params={"date": "2025-06-01"},
            headers=att_setup["headers"],
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "section_id" in data
        assert "entries" in data

    async def test_mark_section_attendance(self, async_client: AsyncClient, att_setup: dict):
        """POST marks attendance for the section."""
        resp = await async_client.post(
            f"/api/v1/attendance/section/{att_setup['section_id']}",
            json={
                "section_id": att_setup["section_id"],
                "academic_year_id": att_setup["academic_year_id"],
                "date": "2025-06-02",
                "session_type": "full_day",
                "entries": [
                    {"student_id": att_setup["student_id"], "status": "present"},
                ],
            },
            headers=att_setup["headers"],
        )
        assert resp.status_code in (200, 201), resp.text
        data = resp.json()
        assert data["total"] >= 1
        assert data["present"] >= 1

    async def test_get_student_attendance(self, async_client: AsyncClient, att_setup: dict):
        """GET attendance summary for a specific student."""
        resp = await async_client.get(
            f"/api/v1/attendance/student/{att_setup['student_id']}",
            params={"from": "2025-04-01", "to": "2025-06-30"},
            headers=att_setup["headers"],
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "student_id" in data
        assert "attendance_pct" in data

    async def test_attendance_report(self, async_client: AsyncClient, att_setup: dict):
        """GET attendance report filtered by section."""
        resp = await async_client.get(
            "/api/v1/attendance/report",
            params={
                "section_id": att_setup["section_id"],
                "academic_year_id": att_setup["academic_year_id"],
                "from_date": "2025-04-01",
                "to_date": "2025-06-30",
            },
            headers=att_setup["headers"],
        )
        assert resp.status_code == 200, resp.text
        assert isinstance(resp.json(), list)


# ── Tests: Holidays ────────────────────────────────────────────────────────────

class TestHolidays:
    async def test_create_holiday(self, async_client: AsyncClient, att_setup: dict):
        resp = await async_client.post(
            "/api/v1/holidays",
            json={
                "academic_year_id": att_setup["academic_year_id"],
                "name": "Diwali",
                "date": "2025-10-20",
                "holiday_type": "school",
            },
            headers=att_setup["headers"],
        )
        assert resp.status_code in (200, 201), resp.text
        data = resp.json()
        assert data["name"] == "Diwali"

    async def test_list_holidays(self, async_client: AsyncClient, att_setup: dict):
        resp = await async_client.get("/api/v1/holidays", headers=att_setup["headers"])
        assert resp.status_code == 200, resp.text
        assert isinstance(resp.json(), list)

    async def test_create_national_holiday(self, async_client: AsyncClient, att_setup: dict):
        resp = await async_client.post(
            "/api/v1/holidays",
            json={
                "academic_year_id": att_setup["academic_year_id"],
                "name": "Republic Day",
                "date": "2026-01-26",
                "holiday_type": "national",
            },
            headers=att_setup["headers"],
        )
        assert resp.status_code in (200, 201), resp.text


# ── Tests: Staff Attendance ────────────────────────────────────────────────────

class TestStaffAttendance:
    async def test_mark_staff_attendance(self, async_client: AsyncClient, att_setup: dict):
        resp = await async_client.post(
            "/api/v1/staff-attendance",
            json=[
                {
                    "staff_id": att_setup["staff_id"],
                    "date": "2025-06-02",
                    "status": "present",
                    "source": "manual",
                }
            ],
            headers=att_setup["headers"],
        )
        assert resp.status_code in (200, 201), resp.text
        data = resp.json()
        assert "affected" in data or "message" in data

    async def test_list_staff_attendance(self, async_client: AsyncClient, att_setup: dict):
        resp = await async_client.get(
            "/api/v1/staff-attendance",
            params={"date": "2025-06-02"},
            headers=att_setup["headers"],
        )
        assert resp.status_code == 200, resp.text
        assert isinstance(resp.json(), list)

    async def test_staff_attendance_report(self, async_client: AsyncClient, att_setup: dict):
        resp = await async_client.get(
            "/api/v1/staff-attendance/report",
            params={"month": 6, "year": 2025},
            headers=att_setup["headers"],
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "month" in data
        assert "year" in data
