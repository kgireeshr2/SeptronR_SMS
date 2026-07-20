"""
Round 4 — Communications Tests
Covers: Notification Templates, Notifications, Bulk Messages, Announcements
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from tests.conftest import create_test_superadmin


def _data(resp):
    body = resp.json()
    if isinstance(body, list):
        return body
    return body.get("data", body)


@pytest_asyncio.fixture(scope="session")
async def comm_setup(session_http_client: AsyncClient) -> dict:
    c = session_http_client
    await create_test_superadmin("comm_superadmin", "comm_super@test.com")

    login = await c.post("/api/v1/auth/login",
        json={"identifier": "comm_super@test.com", "password": "Admin@1234"})
    assert login.status_code == 200, login.text
    token = login.json()["data"]["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    sr = await c.post("/api/v1/schools/bootstrap",
        json={"school_name": "Comm Test School"}, headers=h)
    assert sr.status_code == 201, sr.text
    school_id = _data(sr)["id"]
    hh = {**h, "X-School-Id": school_id}

    # Need a user_id for notifications
    me = await c.get("/api/v1/auth/me", headers=hh)
    user_id = me.json()["data"]["id"] if "data" in me.json() else me.json()["id"]

    return {"headers": hh, "school_id": school_id, "user_id": user_id}


# ── Notification Templates ─────────────────────────────────────────────────────

class TestNotificationTemplates:
    async def test_create_template(self, async_client: AsyncClient, comm_setup: dict):
        resp = await async_client.post("/api/v1/communications/templates",
            json={
                "name": "Fee Reminder",
                "event_trigger": "fee_due",
                "channels": ["email", "sms"],
                "subject": "Fee Due Reminder",
                "body_template": "Dear {{name}}, your fee of {{amount}} is due on {{date}}.",
                "is_active": True,
            },
            headers=comm_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        data = _data(resp)
        assert data["name"] == "Fee Reminder"
        comm_setup["template_id"] = data["id"]

    async def test_list_templates(self, async_client: AsyncClient, comm_setup: dict):
        # Create one within this session to ensure at least one exists
        await async_client.post("/api/v1/communications/templates",
            json={
                "name": "Test List Template",
                "event_trigger": "test_event",
                "channels": ["email"],
                "subject": "Test Subject",
                "body_template": "Hello {{name}}",
                "is_active": True,
            },
            headers=comm_setup["headers"])
        resp = await async_client.get("/api/v1/communications/templates",
            headers=comm_setup["headers"])
        assert resp.status_code == 200, resp.text
        body = resp.json()
        items = body if isinstance(body, list) else body.get("data", [])
        assert isinstance(items, list)
        assert len(items) >= 1


# ── Notifications ──────────────────────────────────────────────────────────────

class TestNotifications:
    async def test_create_notification(self, async_client: AsyncClient, comm_setup: dict):
        resp = await async_client.post("/api/v1/notifications",
            json={
                "user_id": comm_setup["user_id"],
                "type": "info",
                "title": "Test Notification",
                "body": "This is a test notification body.",
                "channel": "in_app",
            },
            headers=comm_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        data = _data(resp)
        assert data["title"] == "Test Notification"
        comm_setup["notification_id"] = data["id"]

    async def test_list_notifications(self, async_client: AsyncClient, comm_setup: dict):
        resp = await async_client.get("/api/v1/notifications",
            headers=comm_setup["headers"])
        assert resp.status_code == 200, resp.text
        body = resp.json()
        items = body if isinstance(body, list) else body.get("data", [])
        assert isinstance(items, list)

    async def test_mark_notifications_read(self, async_client: AsyncClient, comm_setup: dict):
        # mark-read requires a MarkReadRequest with notification_ids list
        resp = await async_client.post("/api/v1/notifications/mark-read",
            json={"notification_ids": []},
            headers=comm_setup["headers"])
        assert resp.status_code in (200, 204), resp.text


# ── Bulk Messages ──────────────────────────────────────────────────────────────

class TestBulkMessages:
    async def test_create_bulk_message(self, async_client: AsyncClient, comm_setup: dict):
        resp = await async_client.post("/api/v1/communications/bulk-messages",
            json={
                "title": "Holiday Notice",
                "body": "School will remain closed on Monday.",
                "channel": "in_app",
                "audience": "all",
            },
            headers=comm_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        data = _data(resp)
        assert data["title"] == "Holiday Notice"

    async def test_list_bulk_messages(self, async_client: AsyncClient, comm_setup: dict):
        resp = await async_client.get("/api/v1/communications/bulk-messages",
            headers=comm_setup["headers"])
        assert resp.status_code == 200, resp.text


# ── Announcements ──────────────────────────────────────────────────────────────

class TestAnnouncements:
    async def test_create_announcement(self, async_client: AsyncClient, comm_setup: dict):
        resp = await async_client.post("/api/v1/announcements",
            json={
                "title": "Annual Day Celebration",
                "body": "Annual day is on Dec 15th. All students must attend.",
                "audience": "all",
            },
            headers=comm_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        data = _data(resp)
        assert data["title"] == "Annual Day Celebration"
        comm_setup["announcement_id"] = data["id"]

    async def test_list_announcements(self, async_client: AsyncClient, comm_setup: dict):
        # Create one within this session to ensure at least one exists
        await async_client.post("/api/v1/announcements",
            json={"title": "List Announcement", "body": "Test body for listing.", "audience": "all"},
            headers=comm_setup["headers"])
        resp = await async_client.get("/api/v1/announcements",
            headers=comm_setup["headers"])
        assert resp.status_code == 200, resp.text
        body = resp.json()
        items = body if isinstance(body, list) else body.get("data", [])
        assert isinstance(items, list)
        assert len(items) >= 1

    async def test_delete_announcement(self, async_client: AsyncClient, comm_setup: dict):
        # Create announcement within this session then delete it
        cr = await async_client.post("/api/v1/announcements",
            json={"title": "Delete Me", "body": "To be deleted.", "audience": "all"},
            headers=comm_setup["headers"])
        assert cr.status_code in (200, 201), cr.text
        ann_id = _data(cr)["id"]
        resp = await async_client.delete(f"/api/v1/announcements/{ann_id}",
            headers=comm_setup["headers"])
        assert resp.status_code in (200, 204), resp.text
