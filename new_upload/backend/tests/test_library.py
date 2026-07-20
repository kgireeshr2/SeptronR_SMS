"""
Round 3 — Library Management Tests
Session-scoped fixtures bootstrap school + user for membership.
"""
import uuid
import pytest_asyncio
from httpx import AsyncClient
from tests.conftest import create_test_superadmin


def _data(resp) -> dict:
    body = resp.json()
    return body.get("data", body)


@pytest_asyncio.fixture(scope="session")
async def lib_setup(session_http_client: AsyncClient) -> dict:
    c = session_http_client
    await create_test_superadmin("lib_superadmin", "lib_super@test.com")

    login = await c.post("/api/v1/auth/login",
        json={"identifier": "lib_super@test.com", "password": "Admin@1234"})
    assert login.status_code == 200, login.text
    login_data = login.json()["data"]
    token = login_data["access_token"]
    user_id = login_data["user"]["id"]
    h = {"Authorization": f"Bearer {token}"}

    sr = await c.post("/api/v1/schools/bootstrap",
        json={"school_name": "Library Test School"}, headers=h)
    assert sr.status_code == 201, sr.text
    school_id = _data(sr)["id"]
    hh = {**h, "X-School-Id": school_id}

    return {"headers": hh, "school_id": school_id, "user_id": user_id}


# ── Book Categories ────────────────────────────────────────────────────────────

class TestBookCategories:
    async def test_create_book_category(self, async_client: AsyncClient, lib_setup: dict):
        resp = await async_client.post("/api/v1/library/categories",
            json={"name": "Science", "description": "Science books"},
            headers=lib_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        assert resp.json()["name"] == "Science"

    async def test_list_book_categories(self, async_client: AsyncClient, lib_setup: dict):
        resp = await async_client.get("/api/v1/library/categories",
            headers=lib_setup["headers"])
        assert resp.status_code == 200, resp.text
        assert isinstance(resp.json(), list)


# ── Books ──────────────────────────────────────────────────────────────────────

class TestBooks:
    async def test_create_book(self, async_client: AsyncClient, lib_setup: dict):
        resp = await async_client.post("/api/v1/library/books",
            json={
                "title": "Physics Vol 1",
                "author": "R.D. Sharma",
                "isbn": f"978{uuid.uuid4().hex[:9]}",
                "publisher": "S. Chand",
                "total_copies": 5,
                "price": 35000,
            },
            headers=lib_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        data = resp.json()
        assert data["title"] == "Physics Vol 1"
        assert data["total_copies"] == 5

    async def test_list_books(self, async_client: AsyncClient, lib_setup: dict):
        resp = await async_client.get("/api/v1/library/books",
            headers=lib_setup["headers"])
        assert resp.status_code == 200, resp.text
        assert isinstance(resp.json(), list)

    async def test_get_book_by_id(self, async_client: AsyncClient, lib_setup: dict):
        cr = await async_client.post("/api/v1/library/books",
            json={"title": "Chemistry Basics", "total_copies": 3},
            headers=lib_setup["headers"])
        assert cr.status_code in (200, 201), cr.text
        book_id = cr.json()["id"]

        gr = await async_client.get(f"/api/v1/library/books/{book_id}",
            headers=lib_setup["headers"])
        assert gr.status_code == 200, gr.text
        assert gr.json()["id"] == book_id

    async def test_update_book(self, async_client: AsyncClient, lib_setup: dict):
        cr = await async_client.post("/api/v1/library/books",
            json={"title": "Biology Book", "total_copies": 2},
            headers=lib_setup["headers"])
        assert cr.status_code in (200, 201), cr.text
        book_id = cr.json()["id"]

        ur = await async_client.put(f"/api/v1/library/books/{book_id}",
            json={"total_copies": 10},
            headers=lib_setup["headers"])
        assert ur.status_code == 200, ur.text
        assert ur.json()["total_copies"] == 10


# ── Library Members ────────────────────────────────────────────────────────────

class TestLibraryMembers:
    async def test_create_library_member(self, async_client: AsyncClient, lib_setup: dict):
        resp = await async_client.post("/api/v1/library/members",
            json={
                "user_id": lib_setup["user_id"],
                "member_type": "staff",
                "max_books_allowed": 5,
            },
            headers=lib_setup["headers"])
        # May be 200/201 on first run, 400/409 on re-run (already exists)
        assert resp.status_code in (200, 201, 400, 409), resp.text

    async def test_list_library_members(self, async_client: AsyncClient, lib_setup: dict):
        resp = await async_client.get("/api/v1/library/members",
            headers=lib_setup["headers"])
        assert resp.status_code == 200, resp.text
        assert isinstance(resp.json(), list)
