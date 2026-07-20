"""
Round 2 — Student Management Tests
Session-scoped fixtures use the HTTP API (bootstrap school, create resources).
"""
import pytest_asyncio
from httpx import AsyncClient
from tests.conftest import create_test_superadmin


# ── Helpers ─────────────────────────────────────────────────────────────────

def _data(resp) -> dict:
    """Unwrap ok() envelope: {success, data, message}."""
    body = resp.json()
    return body.get("data", body)


# ── Session-scoped shared setup ───────────────────────────────────────────────

@pytest_asyncio.fixture(scope="session")
async def std_setup(session_http_client: AsyncClient) -> dict:
    """Bootstrap school + resources needed for student tests (once per session)."""
    c = session_http_client

    # Create super-admin directly (no /register endpoint exists)
    await create_test_superadmin("std_superadmin", "std_super@test.com")

    login = await c.post(
        "/api/v1/auth/login",
        json={"identifier": "std_super@test.com", "password": "Admin@1234"},
    )
    assert login.status_code == 200, login.text
    token = login.json()["data"]["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    # Bootstrap school
    sr = await c.post(
        "/api/v1/schools/bootstrap",
        json={"school_name": "Student Test School"},
        headers=h,
    )
    assert sr.status_code == 201, sr.text
    school_id = _data(sr)["id"]
    hh = {**h, "X-School-Id": school_id}

    # Academic Year
    ayr = await c.post(
        "/api/v1/academic-years",
        json={"name": "2025-26", "start_date": "2025-04-01", "end_date": "2026-03-31", "is_current": True},
        headers=hh,
    )
    assert ayr.status_code == 200, ayr.text
    ay_id = _data(ayr)["id"]

    # Class
    cr = await c.post(
        "/api/v1/classes",
        json={"name": "Class 5", "academic_year_id": ay_id, "is_active": True},
        headers=hh,
    )
    assert cr.status_code in (200, 201), cr.text
    class_id = _data(cr)["id"]

    # Section
    secr = await c.post(
        f"/api/v1/classes/{class_id}/sections",
        json={"name": "A"},
        headers=hh,
    )
    assert secr.status_code in (200, 201), secr.text
    section_id = _data(secr)["id"]

    return {
        "headers": hh,
        "school_id": school_id,
        "academic_year_id": ay_id,
        "class_id": class_id,
        "section_id": section_id,
    }


def _student_payload(s: dict, first_name="Test", last_name="Student"):
    return {
        "first_name": first_name,
        "last_name": last_name,
        "date_of_birth": "2012-05-10",
        "gender": "male",
        "nationality": "Indian",
        "admission_date": "2025-04-01",
        "is_active": True,
        "enrollment": {
            "academic_year_id": s["academic_year_id"],
            "class_id": s["class_id"],
            "section_id": s["section_id"],
            "is_current": True,
        },
        "parents": [],
    }


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestStudentCRUD:
    async def test_create_student(self, async_client: AsyncClient, std_setup: dict):
        resp = await async_client.post(
            "/api/v1/students/", json=_student_payload(std_setup), headers=std_setup["headers"]
        )
        assert resp.status_code in (200, 201), resp.text
        data = resp.json()
        assert data["first_name"] == "Test"
        assert "id" in data

    async def test_list_students(self, async_client: AsyncClient, std_setup: dict):
        resp = await async_client.get("/api/v1/students/", headers=std_setup["headers"])
        assert resp.status_code == 200, resp.text
        assert isinstance(resp.json(), (list, dict))

    async def test_get_student_not_found(self, async_client: AsyncClient, std_setup: dict):
        resp = await async_client.get(
            "/api/v1/students/00000000-0000-0000-0000-000000000001",
            headers=std_setup["headers"],
        )
        assert resp.status_code == 404

    async def test_get_student_by_id(self, async_client: AsyncClient, std_setup: dict):
        cr = await async_client.post(
            "/api/v1/students/",
            json=_student_payload(std_setup, "Fetch", "Me"),
            headers=std_setup["headers"],
        )
        assert cr.status_code in (200, 201), cr.text
        sid = cr.json()["id"]
        resp = await async_client.get(f"/api/v1/students/{sid}", headers=std_setup["headers"])
        assert resp.status_code == 200
        assert resp.json()["id"] == sid

    async def test_update_student(self, async_client: AsyncClient, std_setup: dict):
        cr = await async_client.post(
            "/api/v1/students/",
            json=_student_payload(std_setup, "Update", "Test"),
            headers=std_setup["headers"],
        )
        assert cr.status_code in (200, 201)
        sid = cr.json()["id"]
        ur = await async_client.put(
            f"/api/v1/students/{sid}", json={"first_name": "Updated"}, headers=std_setup["headers"]
        )
        assert ur.status_code == 200
        assert ur.json()["first_name"] == "Updated"

    async def test_get_student_stats(self, async_client: AsyncClient, std_setup: dict):
        resp = await async_client.get("/api/v1/students/stats", headers=std_setup["headers"])
        assert resp.status_code == 200, resp.text
        assert "total_students" in resp.json()

    async def test_create_student_unauthenticated(self, async_client: AsyncClient, std_setup: dict):
        resp = await async_client.post(
            "/api/v1/students/",
            json=_student_payload(std_setup),
            headers={"X-School-Id": std_setup["school_id"]},
        )
        assert resp.status_code == 401


class TestStudentParents:
    async def test_add_parent(self, async_client: AsyncClient, std_setup: dict):
        cr = await async_client.post(
            "/api/v1/students/",
            json=_student_payload(std_setup, "Parent", "Kid"),
            headers=std_setup["headers"],
        )
        assert cr.status_code in (200, 201)
        sid = cr.json()["id"]

        pr = await async_client.post(
            f"/api/v1/students/{sid}/parents",
            json={
                "relation": "father",
                "name": "Father Name",
                "phone": "9988776655",
                "email": "father@example.com",
                "is_primary_contact": True,
                "can_access_portal": True,
            },
            headers=std_setup["headers"],
        )
        assert pr.status_code in (200, 201), pr.text
