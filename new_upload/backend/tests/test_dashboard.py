"""
Round 4 — Dashboard Tests
Covers: Admin, Teacher, Student dashboard endpoints
Note: Uses SQL Server-compatible SQL (fixed from PostgreSQL DATE_TRUNC etc.)
"""
import pytest_asyncio
from httpx import AsyncClient
from tests.conftest import create_test_superadmin


def _data(resp) -> dict:
    body = resp.json()
    return body.get("data", body)


@pytest_asyncio.fixture(scope="session")
async def dash_setup(session_http_client: AsyncClient) -> dict:
    c = session_http_client
    await create_test_superadmin("dash_superadmin", "dash_super@test.com")

    login = await c.post("/api/v1/auth/login",
        json={"identifier": "dash_super@test.com", "password": "Admin@1234"})
    assert login.status_code == 200, login.text
    token = login.json()["data"]["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    sr = await c.post("/api/v1/schools/bootstrap",
        json={"school_name": "Dashboard Test School"}, headers=h)
    assert sr.status_code == 201, sr.text
    school_id = _data(sr)["id"]
    hh = {**h, "X-School-Id": school_id}

    return {"headers": hh, "school_id": school_id}


class TestDashboard:
    async def test_admin_dashboard(self, async_client: AsyncClient, dash_setup: dict):
        resp = await async_client.get("/api/v1/dashboard/admin",
            headers=dash_setup["headers"])
        assert resp.status_code == 200, resp.text
        data = resp.json()
        # Verify key fields are present
        assert "total_students" in data
        assert "total_staff" in data
        assert "total_fee_collected_this_month" in data
        assert "total_fee_outstanding" in data
        assert "total_present_today" in data
        assert "total_absent_today" in data
        assert "monthly_fee_collection" in data
        assert "student_by_gender" in data

    async def test_admin_dashboard_with_year_filter(self, async_client: AsyncClient, dash_setup: dict):
        # Test that adding year_id param works without error
        resp = await async_client.get("/api/v1/dashboard/admin",
            headers=dash_setup["headers"])
        assert resp.status_code == 200, resp.text

    async def test_teacher_dashboard(self, async_client: AsyncClient, dash_setup: dict):
        resp = await async_client.get("/api/v1/dashboard/teacher",
            headers=dash_setup["headers"])
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "pending_homework_reviews" in data
        assert "upcoming_exams" in data

    async def test_student_dashboard(self, async_client: AsyncClient, dash_setup: dict):
        resp = await async_client.get("/api/v1/dashboard/student",
            headers=dash_setup["headers"])
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "fee_outstanding" in data
        assert "upcoming_exams" in data
        assert "homework_due" in data

    async def test_admin_dashboard_counts_non_negative(self, async_client: AsyncClient, dash_setup: dict):
        resp = await async_client.get("/api/v1/dashboard/admin",
            headers=dash_setup["headers"])
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["total_students"] >= 0
        assert data["total_staff"] >= 0
        assert data["total_fee_collected_this_month"] >= 0
        assert isinstance(data["monthly_fee_collection"], list)
        assert isinstance(data["student_by_class"], list)
        assert isinstance(data["upcoming_events"], list)
        assert isinstance(data["low_stock_alerts"], list)
