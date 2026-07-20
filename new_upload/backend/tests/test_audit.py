"""
Round 4 — Audit Log Tests
Covers: Read-only audit log listing
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
async def audit_setup(session_http_client: AsyncClient) -> dict:
    c = session_http_client
    await create_test_superadmin("audit_superadmin", "audit_super@test.com")

    login = await c.post("/api/v1/auth/login",
        json={"identifier": "audit_super@test.com", "password": "Admin@1234"})
    assert login.status_code == 200, login.text
    token = login.json()["data"]["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    sr = await c.post("/api/v1/schools/bootstrap",
        json={"school_name": "Audit Test School"}, headers=h)
    assert sr.status_code == 201, sr.text
    school_id = _data(sr)["id"]
    hh = {**h, "X-School-Id": school_id}

    return {"headers": hh, "school_id": school_id}


class TestAuditLogs:
    async def test_list_audit_logs(self, async_client: AsyncClient, audit_setup: dict):
        resp = await async_client.get("/api/v1/audit-logs", headers=audit_setup["headers"])
        assert resp.status_code == 200, resp.text
        body = resp.json()
        items = body if isinstance(body, list) else body.get("data", [])
        assert isinstance(items, list)

    async def test_audit_logs_filter_by_module(self, async_client: AsyncClient, audit_setup: dict):
        resp = await async_client.get("/api/v1/audit-logs?module=auth",
            headers=audit_setup["headers"])
        assert resp.status_code == 200, resp.text

    async def test_audit_logs_pagination(self, async_client: AsyncClient, audit_setup: dict):
        resp = await async_client.get("/api/v1/audit-logs?page=1&page_size=5",
            headers=audit_setup["headers"])
        assert resp.status_code == 200, resp.text
        body = resp.json()
        items = body if isinstance(body, list) else body.get("data", [])
        assert isinstance(items, list)
