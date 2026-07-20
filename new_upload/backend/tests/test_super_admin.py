"""
Round 4 — Super Admin Tests
Covers: Schools listing, Plans, Subscriptions, Feature Flags, Impersonation
Requires: is_super_admin=True user (create_test_superadmin sets this by default)
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
async def sa_setup(session_http_client: AsyncClient) -> dict:
    c = session_http_client
    await create_test_superadmin("sa_superadmin", "sa_super@test.com")

    login = await c.post("/api/v1/auth/login",
        json={"identifier": "sa_super@test.com", "password": "Admin@1234"})
    assert login.status_code == 200, login.text
    token = login.json()["data"]["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    # Bootstrap a school to have something to manage
    sr = await c.post("/api/v1/schools/bootstrap",
        json={"school_name": "SA Test School"}, headers=h)
    assert sr.status_code == 201, sr.text
    school_id = _data(sr)["id"]

    # Note: superadmin endpoints don't require X-School-Id header
    return {"headers": h, "school_id": school_id}


# ── Schools ────────────────────────────────────────────────────────────────────

class TestSuperAdminSchools:
    async def test_list_schools(self, async_client: AsyncClient, sa_setup: dict):
        resp = await async_client.get("/api/v1/superadmin/schools",
            headers=sa_setup["headers"])
        assert resp.status_code == 200, resp.text
        body = resp.json()
        schools = body if isinstance(body, list) else body.get("data", [])
        assert isinstance(schools, list)
        assert len(schools) >= 1

    async def test_toggle_school_active(self, async_client: AsyncClient, sa_setup: dict):
        school_id = sa_setup["school_id"]
        resp = await async_client.patch(
            f"/api/v1/superadmin/schools/{school_id}/toggle-active?is_active=true",
            headers=sa_setup["headers"])
        assert resp.status_code in (200, 201), resp.text


# ── Subscription Plans ─────────────────────────────────────────────────────────

class TestSubscriptionPlans:
    async def test_create_plan(self, async_client: AsyncClient, sa_setup: dict):
        resp = await async_client.post("/api/v1/superadmin/plans",
            json={
                "name": "Basic Plan",
                "max_students": 500,
                "max_staff": 50,
                "enabled_modules": ["academics", "fees", "attendance"],
                "price_monthly_paise": 999900,
            },
            headers=sa_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        data = _data(resp)
        assert data["name"] == "Basic Plan"
        sa_setup["plan_id"] = data["id"]

    async def test_list_plans(self, async_client: AsyncClient, sa_setup: dict):
        # Create one within this session to ensure at least one exists
        await async_client.post("/api/v1/superadmin/plans",
            json={"name": "List Test Plan", "price_monthly_paise": 50000},
            headers=sa_setup["headers"])
        resp = await async_client.get("/api/v1/superadmin/plans",
            headers=sa_setup["headers"])
        assert resp.status_code == 200, resp.text
        body = resp.json()
        plans = body if isinstance(body, list) else body.get("data", [])
        assert isinstance(plans, list)
        assert len(plans) >= 1

    async def test_update_plan(self, async_client: AsyncClient, sa_setup: dict):
        plan_id = sa_setup.get("plan_id")
        if not plan_id:
            import pytest; pytest.skip("No plan to update")
        resp = await async_client.put(f"/api/v1/superadmin/plans/{plan_id}",
            json={
                "name": "Basic Plan (Updated)",
                "max_students": 600,
                "max_staff": 60,
                "enabled_modules": ["academics", "fees", "attendance", "transport"],
                "price_monthly_paise": 1299900,
            },
            headers=sa_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        data = _data(resp)
        assert data["name"] == "Basic Plan (Updated)"


# ── Subscriptions ──────────────────────────────────────────────────────────────

class TestSubscriptions:
    async def test_create_subscription(self, async_client: AsyncClient, sa_setup: dict):
        plan_id = sa_setup.get("plan_id")
        if not plan_id:
            import pytest; pytest.skip("No plan to subscribe to")
        resp = await async_client.post("/api/v1/superadmin/subscriptions",
            json={
                "school_id": sa_setup["school_id"],
                "plan_id": plan_id,
                "starts_at": "2025-04-01",
                "notes": "Initial subscription",
            },
            headers=sa_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        data = _data(resp)
        assert data["plan_id"] == plan_id
        sa_setup["subscription_id"] = data["id"]

    async def test_list_subscriptions(self, async_client: AsyncClient, sa_setup: dict):
        resp = await async_client.get("/api/v1/superadmin/subscriptions",
            headers=sa_setup["headers"])
        assert resp.status_code == 200, resp.text


# ── Feature Flags ──────────────────────────────────────────────────────────────

class TestFeatureFlags:
    async def test_set_feature_flag(self, async_client: AsyncClient, sa_setup: dict):
        school_id = sa_setup["school_id"]
        resp = await async_client.put(f"/api/v1/superadmin/schools/{school_id}/features",
            json={"feature_key": "transport_module", "is_enabled": True},
            headers=sa_setup["headers"])
        assert resp.status_code in (200, 201), resp.text

    async def test_get_feature_flags(self, async_client: AsyncClient, sa_setup: dict):
        school_id = sa_setup["school_id"]
        resp = await async_client.get(f"/api/v1/superadmin/schools/{school_id}/features",
            headers=sa_setup["headers"])
        assert resp.status_code == 200, resp.text
        body = resp.json()
        flags = body if isinstance(body, list) else body.get("data", [])
        assert isinstance(flags, list)
