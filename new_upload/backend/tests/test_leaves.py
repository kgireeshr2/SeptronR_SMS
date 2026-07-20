"""
Round 2 — Leave Management Tests
Session-scoped fixtures bootstrap school + staff for leave tests.
"""
import uuid
import pytest_asyncio
from httpx import AsyncClient
from tests.conftest import create_test_superadmin


def _data(resp) -> dict:
    body = resp.json()
    return body.get("data", body)


@pytest_asyncio.fixture(scope="session")
async def lv_setup(session_http_client: AsyncClient) -> dict:
    """Bootstrap school + a staff member for leave tests (once per session)."""
    c = session_http_client

    # Create super-admin directly
    await create_test_superadmin("lv_superadmin", "lv_super@test.com")

    login = await c.post(
        "/api/v1/auth/login",
        json={"identifier": "lv_super@test.com", "password": "Admin@1234"},
    )
    assert login.status_code == 200, login.text
    token = login.json()["data"]["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    # Bootstrap school
    sr = await c.post(
        "/api/v1/schools/bootstrap",
        json={"school_name": "Leave Test School"},
        headers=h,
    )
    assert sr.status_code == 201, sr.text
    school_id = _data(sr)["id"]
    hh = {**h, "X-School-Id": school_id}

    # Create a department and designation for staff
    uid = uuid.uuid4().hex[:8]
    dept_r = await c.post("/api/v1/departments", json={"name": f"Leave Dept {uid}"}, headers=hh)
    assert dept_r.status_code in (200, 201), dept_r.text
    dept_id = dept_r.json()["id"]

    desig_r = await c.post("/api/v1/designations", json={"name": f"Leave Teacher {uid}"}, headers=hh)
    assert desig_r.status_code in (200, 201), desig_r.text
    desig_id = desig_r.json()["id"]

    # Create a staff member
    staff_r = await c.post(
        "/api/v1/staff",
        json={
            "first_name": "Leave",
            "last_name": "Staff",
            "date_of_birth": "1985-06-15",
            "gender": "male",
            "department_id": dept_id,
            "designation_id": desig_id,
            "date_of_joining": "2025-01-01",
            "employment_type": "permanent",
            "salary_type": "monthly",
            "monthly_salary": 2500000,
            "email": f"leave.staff.{uid}@test.com",
            "phone": f"91{uid[:8]}",
        },
        headers=hh,
    )
    assert staff_r.status_code in (200, 201), staff_r.text
    staff_id = staff_r.json()["id"]

    return {"headers": hh, "school_id": school_id, "staff_id": staff_id}


# ── Tests: Leave Types ─────────────────────────────────────────────────────────

class TestLeaveTypes:
    async def test_create_leave_type(self, async_client: AsyncClient, lv_setup: dict):
        resp = await async_client.post(
            "/api/v1/leaves/types",
            json={"name": "Sick Leave", "max_days_per_year": 10, "is_paid": True},
            headers=lv_setup["headers"],
        )
        assert resp.status_code in (200, 201), resp.text
        data = resp.json()
        assert data["name"] == "Sick Leave"
        assert data["max_days_per_year"] == 10

    async def test_list_leave_types(self, async_client: AsyncClient, lv_setup: dict):
        resp = await async_client.get("/api/v1/leaves/types", headers=lv_setup["headers"])
        assert resp.status_code == 200, resp.text
        assert isinstance(resp.json(), list)

    async def test_get_leave_type_by_id(self, async_client: AsyncClient, lv_setup: dict):
        cr = await async_client.post(
            "/api/v1/leaves/types",
            json={"name": "Casual Leave", "max_days_per_year": 5, "is_paid": True},
            headers=lv_setup["headers"],
        )
        assert cr.status_code in (200, 201), cr.text
        lt_id = cr.json()["id"]

        gr = await async_client.get(f"/api/v1/leaves/types/{lt_id}", headers=lv_setup["headers"])
        assert gr.status_code == 200, gr.text
        assert gr.json()["id"] == lt_id

    async def test_update_leave_type(self, async_client: AsyncClient, lv_setup: dict):
        cr = await async_client.post(
            "/api/v1/leaves/types",
            json={"name": "Earned Leave", "max_days_per_year": 15, "is_paid": True},
            headers=lv_setup["headers"],
        )
        assert cr.status_code in (200, 201), cr.text
        lt_id = cr.json()["id"]

        ur = await async_client.put(
            f"/api/v1/leaves/types/{lt_id}",
            json={"max_days_per_year": 20},
            headers=lv_setup["headers"],
        )
        assert ur.status_code == 200, ur.text
        assert ur.json()["max_days_per_year"] == 20

    async def test_delete_leave_type(self, async_client: AsyncClient, lv_setup: dict):
        cr = await async_client.post(
            "/api/v1/leaves/types",
            json={"name": "Unpaid Leave", "max_days_per_year": 0, "is_paid": False},
            headers=lv_setup["headers"],
        )
        assert cr.status_code in (200, 201), cr.text
        lt_id = cr.json()["id"]

        dr = await async_client.delete(f"/api/v1/leaves/types/{lt_id}", headers=lv_setup["headers"])
        assert dr.status_code in (200, 204), dr.text

    async def test_get_leave_type_not_found(self, async_client: AsyncClient, lv_setup: dict):
        resp = await async_client.get(
            "/api/v1/leaves/types/00000000-0000-0000-0000-000000000099",
            headers=lv_setup["headers"],
        )
        assert resp.status_code == 404, resp.text


# ── Tests: Leave Applications ──────────────────────────────────────────────────

class TestLeaveApplications:
    async def test_list_leave_applications(self, async_client: AsyncClient, lv_setup: dict):
        resp = await async_client.get("/api/v1/leaves/applications", headers=lv_setup["headers"])
        assert resp.status_code == 200, resp.text
        assert isinstance(resp.json(), list)

    async def test_leave_stats(self, async_client: AsyncClient, lv_setup: dict):
        resp = await async_client.get("/api/v1/leaves/stats/summary", headers=lv_setup["headers"])
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "total_leaves" in data
        assert "pending_leaves" in data

    async def test_leave_balances(self, async_client: AsyncClient, lv_setup: dict):
        resp = await async_client.get("/api/v1/leaves/balances", headers=lv_setup["headers"])
        assert resp.status_code == 200, resp.text
        assert isinstance(resp.json(), list)
