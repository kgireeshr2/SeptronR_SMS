"""
Round 3 — Inventory Management Tests
Session-scoped fixtures bootstrap school.
"""
import uuid
import pytest_asyncio
from datetime import date
from httpx import AsyncClient
from tests.conftest import create_test_superadmin


def _data(resp) -> dict:
    body = resp.json()
    return body.get("data", body)


@pytest_asyncio.fixture(scope="session")
async def inv_setup(session_http_client: AsyncClient) -> dict:
    c = session_http_client
    await create_test_superadmin("inv_superadmin", "inv_super@test.com")

    login = await c.post("/api/v1/auth/login",
        json={"identifier": "inv_super@test.com", "password": "Admin@1234"})
    assert login.status_code == 200, login.text
    token = login.json()["data"]["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    sr = await c.post("/api/v1/schools/bootstrap",
        json={"school_name": "Inventory Test School"}, headers=h)
    assert sr.status_code == 201, sr.text
    school_id = _data(sr)["id"]
    hh = {**h, "X-School-Id": school_id}

    return {"headers": hh, "school_id": school_id}


# ── Inventory Categories ───────────────────────────────────────────────────────

class TestInventoryCategories:
    async def test_create_category(self, async_client: AsyncClient, inv_setup: dict):
        resp = await async_client.post("/api/v1/inventory/categories",
            json={"name": "Stationery", "description": "Office stationery"},
            headers=inv_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        assert resp.json()["name"] == "Stationery"

    async def test_list_categories(self, async_client: AsyncClient, inv_setup: dict):
        resp = await async_client.get("/api/v1/inventory/categories",
            headers=inv_setup["headers"])
        assert resp.status_code == 200, resp.text
        assert isinstance(resp.json(), list)


# ── Suppliers ──────────────────────────────────────────────────────────────────

class TestSuppliers:
    async def test_create_supplier(self, async_client: AsyncClient, inv_setup: dict):
        uid = uuid.uuid4().hex[:8]
        resp = await async_client.post("/api/v1/inventory/suppliers",
            json={
                "name": f"ABC Supplies {uid}",
                "contact_person": "Raju",
                "phone": f"94{uid[:8]}",
                "email": f"abc.{uid}@supply.com",
            },
            headers=inv_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        assert "suppliers" in resp.json()["name"].lower() or resp.json()["name"] == f"ABC Supplies {uid}"

    async def test_list_suppliers(self, async_client: AsyncClient, inv_setup: dict):
        resp = await async_client.get("/api/v1/inventory/suppliers",
            headers=inv_setup["headers"])
        assert resp.status_code == 200, resp.text
        assert isinstance(resp.json(), list)

    async def test_update_supplier(self, async_client: AsyncClient, inv_setup: dict):
        uid = uuid.uuid4().hex[:8]
        cr = await async_client.post("/api/v1/inventory/suppliers",
            json={"name": f"XYZ Corp {uid}", "phone": f"95{uid[:8]}"},
            headers=inv_setup["headers"])
        assert cr.status_code in (200, 201), cr.text
        sup_id = cr.json()["id"]

        ur = await async_client.put(f"/api/v1/inventory/suppliers/{sup_id}",
            json={"name": f"XYZ Corp Updated {uid}"},
            headers=inv_setup["headers"])
        assert ur.status_code == 200, ur.text


# ── Stores ─────────────────────────────────────────────────────────────────────

class TestStores:
    async def test_create_store(self, async_client: AsyncClient, inv_setup: dict):
        resp = await async_client.post("/api/v1/inventory/stores",
            json={"name": "Main Storage Room", "location": "Block A, Room 101"},
            headers=inv_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        assert resp.json()["name"] == "Main Storage Room"

    async def test_list_stores(self, async_client: AsyncClient, inv_setup: dict):
        resp = await async_client.get("/api/v1/inventory/stores",
            headers=inv_setup["headers"])
        assert resp.status_code == 200, resp.text
        assert isinstance(resp.json(), list)


# ── Items ──────────────────────────────────────────────────────────────────────

class TestItems:
    async def test_create_item(self, async_client: AsyncClient, inv_setup: dict):
        resp = await async_client.post("/api/v1/inventory/items",
            json={
                "name": "A4 Paper Ream",
                "unit": "ream",
                "min_stock_level": 10,
                "current_stock": 50,
                "unit_cost": 25000,
            },
            headers=inv_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        assert resp.json()["name"] == "A4 Paper Ream"

    async def test_list_items(self, async_client: AsyncClient, inv_setup: dict):
        resp = await async_client.get("/api/v1/inventory/items",
            headers=inv_setup["headers"])
        assert resp.status_code == 200, resp.text
        assert isinstance(resp.json(), list)

    async def test_update_item(self, async_client: AsyncClient, inv_setup: dict):
        cr = await async_client.post("/api/v1/inventory/items",
            json={"name": "Whiteboard Marker", "unit": "box", "unit_cost": 15000},
            headers=inv_setup["headers"])
        assert cr.status_code in (200, 201), cr.text
        item_id = cr.json()["id"]

        ur = await async_client.put(f"/api/v1/inventory/items/{item_id}",
            json={"unit_cost": 18000},
            headers=inv_setup["headers"])
        assert ur.status_code == 200, ur.text
        assert ur.json()["unit_cost"] == 18000

    async def test_stock_entry(self, async_client: AsyncClient, inv_setup: dict):
        # Create an item first
        cr = await async_client.post("/api/v1/inventory/items",
            json={"name": "Chalk Box", "unit": "box", "unit_cost": 5000},
            headers=inv_setup["headers"])
        assert cr.status_code in (200, 201), cr.text
        item_id = cr.json()["id"]

        # Add stock
        sr = await async_client.post(f"/api/v1/inventory/items/{item_id}/stock-entries",
            json={
                "item_id": item_id,
                "quantity": 20,
                "unit_cost": 5000,
                "entry_date": str(date.today()),
            },
            headers=inv_setup["headers"])
        assert sr.status_code in (200, 201), sr.text
        assert sr.json()["quantity"] == 20
