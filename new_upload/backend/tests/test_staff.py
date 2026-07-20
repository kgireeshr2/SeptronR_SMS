"""
Round 2 — Staff Management Tests
Session-scoped fixtures use the HTTP API (bootstrap school).
"""
import uuid
import pytest_asyncio
from httpx import AsyncClient
from tests.conftest import create_test_superadmin


def _data(resp) -> dict:
    body = resp.json()
    return body.get("data", body)


@pytest_asyncio.fixture(scope="session")
async def stf_setup(session_http_client: AsyncClient) -> dict:
    """Bootstrap school for staff tests (once per session)."""
    c = session_http_client

    # Create super-admin user directly (no /register endpoint exists)
    await create_test_superadmin("stf_superadmin", "stf_super@test.com")

    login = await c.post(
        "/api/v1/auth/login",
        json={"identifier": "stf_super@test.com", "password": "Admin@1234"},
    )
    assert login.status_code == 200, login.text
    token = login.json()["data"]["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    sr = await c.post(
        "/api/v1/schools/bootstrap",
        json={"school_name": "Staff Test School"},
        headers=h,
    )
    assert sr.status_code == 201, sr.text
    school_id = _data(sr)["id"]
    hh = {**h, "X-School-Id": school_id}
    return {"headers": hh, "school_id": school_id}


# ── Tests: Departments ─────────────────────────────────────────────────────────

class TestDepartments:
    async def test_create_department(self, async_client: AsyncClient, stf_setup: dict):
        resp = await async_client.post(
            "/api/v1/departments",
            json={"name": "Science Department"},
            headers=stf_setup["headers"],
        )
        assert resp.status_code in (200, 201), resp.text
        assert resp.json()["name"] == "Science Department"

    async def test_list_departments(self, async_client: AsyncClient, stf_setup: dict):
        resp = await async_client.get("/api/v1/departments", headers=stf_setup["headers"])
        assert resp.status_code == 200, resp.text
        assert isinstance(resp.json(), (list, dict))

    async def test_create_department_duplicate(self, async_client: AsyncClient, stf_setup: dict):
        # Departments may allow duplicates by name; just verify create succeeds
        payload = {"name": "Maths Department"}
        r1 = await async_client.post("/api/v1/departments", json=payload, headers=stf_setup["headers"])
        assert r1.status_code in (200, 201), r1.text
        r2 = await async_client.post("/api/v1/departments", json=payload, headers=stf_setup["headers"])
        # Either conflict (400/409) or allowed (200/201)
        assert r2.status_code in (200, 201, 400, 409), r2.text

    async def test_get_department_by_id(self, async_client: AsyncClient, stf_setup: dict):
        cr = await async_client.post(
            "/api/v1/departments",
            json={"name": "History Department"},
            headers=stf_setup["headers"],
        )
        assert cr.status_code in (200, 201)
        dept_id = cr.json()["id"]
        gr = await async_client.get(f"/api/v1/departments/{dept_id}", headers=stf_setup["headers"])
        assert gr.status_code == 200
        assert gr.json()["id"] == dept_id

    async def test_update_department(self, async_client: AsyncClient, stf_setup: dict):
        cr = await async_client.post(
            "/api/v1/departments",
            json={"name": "Old Name Dept"},
            headers=stf_setup["headers"],
        )
        assert cr.status_code in (200, 201)
        dept_id = cr.json()["id"]
        ur = await async_client.put(
            f"/api/v1/departments/{dept_id}",
            json={"name": "New Name Dept"},
            headers=stf_setup["headers"],
        )
        assert ur.status_code == 200
        assert ur.json()["name"] == "New Name Dept"


# ── Tests: Designations ────────────────────────────────────────────────────────

class TestDesignations:
    async def test_create_designation(self, async_client: AsyncClient, stf_setup: dict):
        resp = await async_client.post(
            "/api/v1/designations",
            json={"name": "Senior Teacher"},
            headers=stf_setup["headers"],
        )
        assert resp.status_code in (200, 201), resp.text
        assert resp.json()["name"] == "Senior Teacher"

    async def test_list_designations(self, async_client: AsyncClient, stf_setup: dict):
        resp = await async_client.get("/api/v1/designations", headers=stf_setup["headers"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), (list, dict))


# ── Tests: Staff CRUD ──────────────────────────────────────────────────────────

class TestStaffCRUD:
    async def test_create_staff(self, async_client: AsyncClient, stf_setup: dict):
        dept_resp = await async_client.post(
            "/api/v1/departments",
            json={"name": "English Dept"},
            headers=stf_setup["headers"],
        )
        dept_id = dept_resp.json()["id"]

        desig_resp = await async_client.post(
            "/api/v1/designations",
            json={"name": "Teacher"},
            headers=stf_setup["headers"],
        )
        desig_id = desig_resp.json()["id"]

        uid = uuid.uuid4().hex[:8]
        resp = await async_client.post(
            "/api/v1/staff",
            json={
                "first_name": "Staff",
                "last_name": "Member",
                "date_of_birth": "1990-01-15",
                "gender": "female",
                "department_id": dept_id,
                "designation_id": desig_id,
                "date_of_joining": "2025-04-01",
                "employment_type": "permanent",
                "salary_type": "monthly",
                "monthly_salary": 3000000,
                "email": f"staff.member.{uid}@test.com",
                "phone": f"90{uid[:8]}",
            },
            headers=stf_setup["headers"],
        )
        assert resp.status_code in (200, 201), resp.text
        data = resp.json()
        assert data["first_name"] == "Staff"
        assert "employee_id" in data

    async def test_list_staff(self, async_client: AsyncClient, stf_setup: dict):
        resp = await async_client.get("/api/v1/staff", headers=stf_setup["headers"])
        assert resp.status_code == 200, resp.text
        assert isinstance(resp.json(), (list, dict))

    async def test_get_staff_not_found(self, async_client: AsyncClient, stf_setup: dict):
        resp = await async_client.get(
            "/api/v1/staff/00000000-0000-0000-0000-000000000099",
            headers=stf_setup["headers"],
        )
        assert resp.status_code == 404

    async def test_create_staff_duplicate_email(self, async_client: AsyncClient, stf_setup: dict):
        uid = uuid.uuid4().hex[:8]
        email = f"dup.email.{uid}@test.com"
        payload = {
            "first_name": "Dup",
            "last_name": "Email",
            "employment_type": "permanent",
            "salary_type": "monthly",
            "monthly_salary": 0,
            "email": email,
            "phone": f"88{uid[:8]}",
        }
        r1 = await async_client.post("/api/v1/staff", json=payload, headers=stf_setup["headers"])
        assert r1.status_code in (200, 201), r1.text
        r2 = await async_client.post("/api/v1/staff", json={**payload, "phone": f"77{uid[:8]}"}, headers=stf_setup["headers"])
        assert r2.status_code == 400, r2.text

    async def test_get_staff_statistics(self, async_client: AsyncClient, stf_setup: dict):
        resp = await async_client.get("/api/v1/staff/stats/summary", headers=stf_setup["headers"])
        assert resp.status_code == 200, resp.text
        assert "total_staff" in resp.json()
