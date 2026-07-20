"""
Round 3 — Transport Management Tests
Session-scoped fixtures bootstrap school.
"""
import uuid
import pytest_asyncio
from httpx import AsyncClient
from tests.conftest import create_test_superadmin


def _data(resp) -> dict:
    body = resp.json()
    return body.get("data", body)


@pytest_asyncio.fixture(scope="session")
async def transport_setup(session_http_client: AsyncClient) -> dict:
    c = session_http_client
    await create_test_superadmin("trans_superadmin", "trans_super@test.com")

    login = await c.post("/api/v1/auth/login",
        json={"identifier": "trans_super@test.com", "password": "Admin@1234"})
    assert login.status_code == 200, login.text
    token = login.json()["data"]["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    sr = await c.post("/api/v1/schools/bootstrap",
        json={"school_name": "Transport Test School"}, headers=h)
    assert sr.status_code == 201, sr.text
    school_id = _data(sr)["id"]
    hh = {**h, "X-School-Id": school_id}

    return {"headers": hh, "school_id": school_id}


# ── Vehicles ───────────────────────────────────────────────────────────────────

class TestVehicles:
    async def test_create_vehicle(self, async_client: AsyncClient, transport_setup: dict):
        uid = uuid.uuid4().hex[:6]
        resp = await async_client.post("/api/v1/transport/vehicles",
            json={
                "registration_number": f"MH-12-AB-{uid}",
                "vehicle_type": "bus",
                "capacity": 50,
                "make": "Ashok Leyland",
                "model": "Viking",
                "year": 2020,
            },
            headers=transport_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        data = resp.json()
        assert data["capacity"] == 50

    async def test_list_vehicles(self, async_client: AsyncClient, transport_setup: dict):
        resp = await async_client.get("/api/v1/transport/vehicles",
            headers=transport_setup["headers"])
        assert resp.status_code == 200, resp.text
        assert isinstance(resp.json(), list)

    async def test_get_vehicle_by_id(self, async_client: AsyncClient, transport_setup: dict):
        uid = uuid.uuid4().hex[:6]
        cr = await async_client.post("/api/v1/transport/vehicles",
            json={"registration_number": f"MH-14-CD-{uid}", "vehicle_type": "van", "capacity": 15},
            headers=transport_setup["headers"])
        assert cr.status_code in (200, 201), cr.text
        veh_id = cr.json()["id"]

        gr = await async_client.get(f"/api/v1/transport/vehicles/{veh_id}",
            headers=transport_setup["headers"])
        assert gr.status_code == 200, gr.text
        assert str(gr.json()["id"]) == veh_id

    async def test_update_vehicle(self, async_client: AsyncClient, transport_setup: dict):
        uid = uuid.uuid4().hex[:6]
        cr = await async_client.post("/api/v1/transport/vehicles",
            json={"registration_number": f"MH-16-EF-{uid}", "vehicle_type": "bus", "capacity": 40},
            headers=transport_setup["headers"])
        assert cr.status_code in (200, 201), cr.text
        veh_id = cr.json()["id"]

        ur = await async_client.put(f"/api/v1/transport/vehicles/{veh_id}",
            json={"capacity": 45},
            headers=transport_setup["headers"])
        assert ur.status_code == 200, ur.text
        assert ur.json()["capacity"] == 45


# ── Routes ─────────────────────────────────────────────────────────────────────

class TestRoutes:
    async def test_create_route(self, async_client: AsyncClient, transport_setup: dict):
        uid = uuid.uuid4().hex[:8]
        resp = await async_client.post("/api/v1/transport/routes",
            json={
                "name": f"Route A - North {uid}",
                "description": "North zone route",
                "stops": [
                    {"name": "Stop 1 - Market", "stop_order": 1, "fare": 5000},
                    {"name": "Stop 2 - Park", "stop_order": 2, "fare": 8000},
                ],
            },
            headers=transport_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        data = resp.json()
        assert "Route A" in data["name"]

    async def test_list_routes(self, async_client: AsyncClient, transport_setup: dict):
        resp = await async_client.get("/api/v1/transport/routes",
            headers=transport_setup["headers"])
        assert resp.status_code == 200, resp.text
        assert isinstance(resp.json(), list)

    async def test_get_route_by_id(self, async_client: AsyncClient, transport_setup: dict):
        uid = uuid.uuid4().hex[:8]
        cr = await async_client.post("/api/v1/transport/routes",
            json={"name": f"Route B - South {uid}"},
            headers=transport_setup["headers"])
        assert cr.status_code in (200, 201), cr.text
        route_id = cr.json()["id"]

        gr = await async_client.get(f"/api/v1/transport/routes/{route_id}",
            headers=transport_setup["headers"])
        assert gr.status_code == 200, gr.text
        assert str(gr.json()["id"]) == route_id

    async def test_add_stop_to_route(self, async_client: AsyncClient, transport_setup: dict):
        uid = uuid.uuid4().hex[:8]
        cr = await async_client.post("/api/v1/transport/routes",
            json={"name": f"Route C - East {uid}"},
            headers=transport_setup["headers"])
        assert cr.status_code in (200, 201), cr.text
        route_id = cr.json()["id"]

        sr = await async_client.post(f"/api/v1/transport/routes/{route_id}/stops",
            json={"name": "East Gate Stop", "stop_order": 1, "fare": 6000},
            headers=transport_setup["headers"])
        assert sr.status_code in (200, 201), sr.text
        assert sr.json()["name"] == "East Gate Stop"
