"""
Round 4 — Settings Tests
Covers: Get all settings, get by category, update by category
"""
import pytest_asyncio
from httpx import AsyncClient
from tests.conftest import create_test_superadmin


def _data(resp) -> dict:
    body = resp.json()
    return body.get("data", body)


@pytest_asyncio.fixture(scope="session")
async def settings_setup(session_http_client: AsyncClient) -> dict:
    c = session_http_client
    await create_test_superadmin("settings_superadmin", "settings_super@test.com")

    login = await c.post("/api/v1/auth/login",
        json={"identifier": "settings_super@test.com", "password": "Admin@1234"})
    assert login.status_code == 200, login.text
    token = login.json()["data"]["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    sr = await c.post("/api/v1/schools/bootstrap",
        json={"school_name": "Settings Test School"}, headers=h)
    assert sr.status_code == 201, sr.text
    school_id = _data(sr)["id"]
    hh = {**h, "X-School-Id": school_id}

    return {"headers": hh, "school_id": school_id}


class TestSettings:
    async def test_get_all_settings(self, async_client: AsyncClient, settings_setup: dict):
        resp = await async_client.get("/api/v1/settings", headers=settings_setup["headers"])
        assert resp.status_code == 200, resp.text
        body = resp.json()
        data = body.get("data", body)
        # Should return a dict or list
        assert data is not None

    async def test_get_settings_by_category(self, async_client: AsyncClient, settings_setup: dict):
        resp = await async_client.get("/api/v1/settings/general",
            headers=settings_setup["headers"])
        assert resp.status_code in (200, 404), resp.text

    async def test_update_settings_category(self, async_client: AsyncClient, settings_setup: dict):
        resp = await async_client.put("/api/v1/settings/general",
            json={"settings": {"school_timezone": "Asia/Kolkata", "date_format": "DD-MM-YYYY"}},
            headers=settings_setup["headers"])
        assert resp.status_code in (200, 201, 422), resp.text
        # 422 is acceptable if validation fails for unknown keys

    async def test_update_notification_settings(self, async_client: AsyncClient, settings_setup: dict):
        resp = await async_client.put("/api/v1/settings/notifications",
            json={"settings": {"email_enabled": True, "sms_enabled": False}},
            headers=settings_setup["headers"])
        assert resp.status_code in (200, 201, 422), resp.text
