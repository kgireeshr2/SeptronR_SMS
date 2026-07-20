"""
Round 3 — Payroll Management Tests
Session-scoped fixtures bootstrap school + staff member.
"""
import uuid
import pytest_asyncio
from httpx import AsyncClient
from tests.conftest import create_test_superadmin


def _data(resp) -> dict:
    body = resp.json()
    return body.get("data", body)


@pytest_asyncio.fixture(scope="session")
async def payroll_setup(session_http_client: AsyncClient) -> dict:
    c = session_http_client
    await create_test_superadmin("pr_superadmin", "pr_super@test.com")

    login = await c.post("/api/v1/auth/login",
        json={"identifier": "pr_super@test.com", "password": "Admin@1234"})
    assert login.status_code == 200, login.text
    token = login.json()["data"]["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    sr = await c.post("/api/v1/schools/bootstrap",
        json={"school_name": "Payroll Test School"}, headers=h)
    assert sr.status_code == 201, sr.text
    school_id = _data(sr)["id"]
    hh = {**h, "X-School-Id": school_id}

    # Academic Year
    ayr = await c.post("/api/v1/academic-years",
        json={"name": "2025-26-pr", "start_date": "2025-04-01",
              "end_date": "2026-03-31", "is_current": True}, headers=hh)
    assert ayr.status_code in (200, 201), ayr.text
    ay_id = _data(ayr)["id"]

    # Department + Designation
    uid = uuid.uuid4().hex[:8]
    dept = await c.post("/api/v1/departments",
        json={"name": f"PR Dept {uid}"}, headers=hh)
    assert dept.status_code in (200, 201), dept.text
    dept_id = dept.json()["id"]

    desig = await c.post("/api/v1/designations",
        json={"name": f"PR Teacher {uid}"}, headers=hh)
    assert desig.status_code in (200, 201), desig.text
    desig_id = desig.json()["id"]

    # Staff member
    staff_r = await c.post("/api/v1/staff", json={
        "first_name": "Payroll",
        "last_name": "Teacher",
        "date_of_birth": "1985-03-10",
        "gender": "male",
        "department_id": dept_id,
        "designation_id": desig_id,
        "date_of_joining": "2025-01-01",
        "employment_type": "permanent",
        "salary_type": "monthly",
        "monthly_salary": 3000000,
        "email": f"pr.teacher.{uid}@test.com",
        "phone": f"93{uid[:8]}",
    }, headers=hh)
    assert staff_r.status_code in (200, 201), staff_r.text
    staff_id = staff_r.json()["id"]

    return {"headers": hh, "school_id": school_id, "academic_year_id": ay_id,
            "staff_id": staff_id}


# ── Payroll Tests ──────────────────────────────────────────────────────────────

class TestPayroll:
    async def test_list_payroll_initially(self, async_client: AsyncClient, payroll_setup: dict):
        resp = await async_client.get("/api/v1/payroll",
            params={"month": 5, "year": 2025},
            headers=payroll_setup["headers"])
        assert resp.status_code == 200, resp.text
        assert isinstance(resp.json(), list)

    async def test_generate_payroll(self, async_client: AsyncClient, payroll_setup: dict):
        resp = await async_client.post("/api/v1/payroll/generate",
            json={
                "month": 5,
                "year": 2025,
                "academic_year_id": payroll_setup["academic_year_id"],
                "staff_ids": [payroll_setup["staff_id"]],
            },
            headers=payroll_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["month"] == 5

    async def test_list_payroll_after_generate(self, async_client: AsyncClient, payroll_setup: dict):
        resp = await async_client.get("/api/v1/payroll",
            params={"month": 5, "year": 2025},
            headers=payroll_setup["headers"])
        assert resp.status_code == 200, resp.text
        rows = resp.json()
        assert len(rows) >= 1

    async def test_get_payroll_by_id(self, async_client: AsyncClient, payroll_setup: dict):
        # Generate for a unique month to get a clean entry
        gen = await async_client.post("/api/v1/payroll/generate",
            json={
                "month": 6,
                "year": 2025,
                "academic_year_id": payroll_setup["academic_year_id"],
                "staff_ids": [payroll_setup["staff_id"]],
            },
            headers=payroll_setup["headers"])
        assert gen.status_code in (200, 201), gen.text
        payroll_id = gen.json()[0]["id"]

        resp = await async_client.get(f"/api/v1/payroll/{payroll_id}",
            headers=payroll_setup["headers"])
        assert resp.status_code == 200, resp.text
        assert resp.json()["id"] == payroll_id

    async def test_payroll_for_staff(self, async_client: AsyncClient, payroll_setup: dict):
        resp = await async_client.get(
            f"/api/v1/payroll/staff/{payroll_setup['staff_id']}",
            headers=payroll_setup["headers"])
        assert resp.status_code == 200, resp.text
        assert isinstance(resp.json(), list)
