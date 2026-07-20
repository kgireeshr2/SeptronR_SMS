"""
Round 4 — Calendar Tests
Covers: Calendar Events CRUD
"""
import pytest_asyncio
from httpx import AsyncClient
from tests.conftest import create_test_superadmin


def _data(resp):
    body = resp.json()
    if isinstance(body, list):
        return body
    return body.get("data", body)


@pytest_asyncio.fixture(scope="session")
async def cal_setup(session_http_client: AsyncClient) -> dict:
    c = session_http_client
    await create_test_superadmin("cal_superadmin", "cal_super@test.com")

    login = await c.post("/api/v1/auth/login",
        json={"identifier": "cal_super@test.com", "password": "Admin@1234"})
    assert login.status_code == 200, login.text
    token = login.json()["data"]["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    sr = await c.post("/api/v1/schools/bootstrap",
        json={"school_name": "Calendar Test School"}, headers=h)
    assert sr.status_code == 201, sr.text
    school_id = _data(sr)["id"]
    hh = {**h, "X-School-Id": school_id}

    return {"headers": hh, "school_id": school_id}


class TestCalendarEvents:
    async def test_create_event(self, async_client: AsyncClient, cal_setup: dict):
        resp = await async_client.post("/api/v1/calendar",
            json={
                "title": "Sports Day",
                "description": "Annual sports day event for all students.",
                "event_type": "sports",
                "start_datetime": "2025-12-10T08:00:00",
                "end_datetime": "2025-12-10T17:00:00",
                "all_day": False,
                "color_tag": "#FF5733",
                "audience": "all",
                "is_active": True,
            },
            headers=cal_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        data = _data(resp)
        assert data["title"] == "Sports Day"
        cal_setup["anon_event_id"] = data["id"]

    async def test_list_events(self, async_client: AsyncClient, cal_setup: dict):
        # Create one within this session for list
        await async_client.post("/api/v1/calendar",
            json={
                "title": "List Test Event",
                "event_type": "other",
                "start_datetime": "2025-11-01T09:00:00",
                "end_datetime": "2025-11-01T10:00:00",
                "audience": "all",
                "is_active": True,
            },
            headers=cal_setup["headers"])
        resp = await async_client.get("/api/v1/calendar", headers=cal_setup["headers"])
        assert resp.status_code == 200, resp.text
        body = resp.json()
        items = body if isinstance(body, list) else body.get("data", [])
        assert isinstance(items, list)
        assert len(items) >= 1

    async def test_update_event(self, async_client: AsyncClient, cal_setup: dict):
        # Create within session then update
        cr = await async_client.post("/api/v1/calendar",
            json={
                "title": "Update Me Event",
                "event_type": "other",
                "start_datetime": "2025-09-15T10:00:00",
                "end_datetime": "2025-09-15T11:00:00",
                "audience": "all",
                "is_active": True,
            },
            headers=cal_setup["headers"])
        assert cr.status_code in (200, 201), cr.text
        event_id = _data(cr)["id"]
        resp = await async_client.put(f"/api/v1/calendar/{event_id}",
            json={"title": "Sports Day (Updated)", "color_tag": "#3498DB"},
            headers=cal_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        data = _data(resp)
        assert data["title"] == "Sports Day (Updated)"

    async def test_create_allday_event(self, async_client: AsyncClient, cal_setup: dict):
        resp = await async_client.post("/api/v1/calendar",
            json={
                "title": "National Holiday",
                "event_type": "holiday",
                "start_datetime": "2025-08-15T00:00:00",
                "end_datetime": "2025-08-15T23:59:59",
                "all_day": True,
                "audience": "all",
                "is_active": True,
            },
            headers=cal_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        data = _data(resp)
        assert data["all_day"] is True
        cal_setup["holiday_event_id"] = data["id"]

    async def test_delete_event(self, async_client: AsyncClient, cal_setup: dict):
        # Create within session then delete
        cr = await async_client.post("/api/v1/calendar",
            json={
                "title": "Delete Me Event",
                "event_type": "other",
                "start_datetime": "2025-07-04T09:00:00",
                "end_datetime": "2025-07-04T10:00:00",
                "audience": "all",
                "is_active": True,
            },
            headers=cal_setup["headers"])
        assert cr.status_code in (200, 201), cr.text
        event_id = _data(cr)["id"]
        resp = await async_client.delete(f"/api/v1/calendar/{event_id}",
            headers=cal_setup["headers"])
        assert resp.status_code in (200, 204), resp.text
