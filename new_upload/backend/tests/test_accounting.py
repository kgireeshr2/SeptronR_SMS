"""
Round 3 — Accounting Management Tests
Session-scoped fixtures bootstrap school.
"""
import pytest_asyncio
from httpx import AsyncClient
from tests.conftest import create_test_superadmin


def _data(resp) -> dict:
    body = resp.json()
    return body.get("data", body)


@pytest_asyncio.fixture(scope="session")
async def acc_setup(session_http_client: AsyncClient) -> dict:
    c = session_http_client
    await create_test_superadmin("acc_superadmin", "acc_super@test.com")

    login = await c.post("/api/v1/auth/login",
        json={"identifier": "acc_super@test.com", "password": "Admin@1234"})
    assert login.status_code == 200, login.text
    token = login.json()["data"]["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    sr = await c.post("/api/v1/schools/bootstrap",
        json={"school_name": "Accounting Test School"}, headers=h)
    assert sr.status_code == 201, sr.text
    school_id = _data(sr)["id"]
    hh = {**h, "X-School-Id": school_id}

    # Income category
    inc_cat = await c.post("/api/v1/accounting/income-categories",
        json={"name": "Fee Collection", "description": "Fee receipts"},
        headers=hh)
    assert inc_cat.status_code in (200, 201), inc_cat.text
    income_cat_id = inc_cat.json()["id"]

    # Expense category
    exp_cat = await c.post("/api/v1/accounting/expense-categories",
        json={"name": "Utilities", "description": "Electricity, water", "budget_amount": 100000},
        headers=hh)
    assert exp_cat.status_code in (200, 201), exp_cat.text
    expense_cat_id = exp_cat.json()["id"]

    # Academic year (for BudgetHead)
    ayr = await c.post("/api/v1/academic-years",
        json={"name": "2025-26-acc", "start_date": "2025-04-01",
              "end_date": "2026-03-31", "is_current": True},
        headers=hh)
    assert ayr.status_code in (200, 201), ayr.text
    academic_year_id = _data(ayr)["id"]

    return {"headers": hh, "school_id": school_id,
            "income_cat_id": income_cat_id, "expense_cat_id": expense_cat_id,
            "academic_year_id": academic_year_id}


# ── Income Categories ──────────────────────────────────────────────────────────

class TestIncomeCategories:
    async def test_create_income_category(self, async_client: AsyncClient, acc_setup: dict):
        resp = await async_client.post("/api/v1/accounting/income-categories",
            json={"name": "Donations", "description": "School donations"},
            headers=acc_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        assert resp.json()["name"] == "Donations"

    async def test_list_income_categories(self, async_client: AsyncClient, acc_setup: dict):
        resp = await async_client.get("/api/v1/accounting/income-categories",
            headers=acc_setup["headers"])
        assert resp.status_code == 200, resp.text
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 1


# ── Expense Categories ─────────────────────────────────────────────────────────

class TestExpenseCategories:
    async def test_create_expense_category(self, async_client: AsyncClient, acc_setup: dict):
        resp = await async_client.post("/api/v1/accounting/expense-categories",
            json={"name": "Office Supplies", "budget_amount": 50000},
            headers=acc_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        assert resp.json()["name"] == "Office Supplies"

    async def test_list_expense_categories(self, async_client: AsyncClient, acc_setup: dict):
        resp = await async_client.get("/api/v1/accounting/expense-categories",
            headers=acc_setup["headers"])
        assert resp.status_code == 200, resp.text
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 1

    async def test_update_expense_category(self, async_client: AsyncClient, acc_setup: dict):
        cr = await async_client.post("/api/v1/accounting/expense-categories",
            json={"name": "Maintenance", "budget_amount": 80000},
            headers=acc_setup["headers"])
        assert cr.status_code in (200, 201), cr.text
        cat_id = cr.json()["id"]

        ur = await async_client.put(f"/api/v1/accounting/expense-categories/{cat_id}",
            json={"budget_amount": 100000},
            headers=acc_setup["headers"])
        assert ur.status_code == 200, ur.text
        assert ur.json()["budget_amount"] == 100000


# ── Income Records ─────────────────────────────────────────────────────────────

class TestIncomeRecords:
    async def test_create_income_record(self, async_client: AsyncClient, acc_setup: dict):
        resp = await async_client.post("/api/v1/accounting/income",
            json={
                "category_id": acc_setup["income_cat_id"],
                "amount": 500000,
                "income_date": "2025-05-01",
                "description": "May fee collection",
                "reference_number": "RCPT-001",
            },
            headers=acc_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        data = resp.json()
        assert data["amount"] == 500000

    async def test_list_income_records(self, async_client: AsyncClient, acc_setup: dict):
        resp = await async_client.get("/api/v1/accounting/income",
            headers=acc_setup["headers"])
        assert resp.status_code == 200, resp.text
        assert isinstance(resp.json(), list)


# ── Expense Records ────────────────────────────────────────────────────────────

class TestExpenseRecords:
    async def test_create_expense_record(self, async_client: AsyncClient, acc_setup: dict):
        resp = await async_client.post("/api/v1/accounting/expenses",
            json={
                "category_id": acc_setup["expense_cat_id"],
                "amount": 25000,
                "expense_date": "2025-05-05",
                "description": "Electricity bill",
                "vendor_name": "Power Corp",
                "payment_mode": "cheque",
            },
            headers=acc_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        data = resp.json()
        assert data["amount"] == 25000

    async def test_list_expense_records(self, async_client: AsyncClient, acc_setup: dict):
        resp = await async_client.get("/api/v1/accounting/expenses",
            headers=acc_setup["headers"])
        assert resp.status_code == 200, resp.text
        assert isinstance(resp.json(), list)


# ── Budget Heads ───────────────────────────────────────────────────────────────

class TestBudgetHeads:
    async def test_create_budget_head(self, async_client: AsyncClient, acc_setup: dict):
        resp = await async_client.post("/api/v1/accounting/budgets",
            json={
                "category_id": acc_setup["expense_cat_id"],
                "academic_year_id": acc_setup["academic_year_id"],
                "allocated_amount": 500000,
                "notes": "Infrastructure budget",
            },
            headers=acc_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        data = resp.json()
        assert data["allocated_amount"] == 500000

    async def test_list_budget_heads(self, async_client: AsyncClient, acc_setup: dict):
        resp = await async_client.get("/api/v1/accounting/budgets",
            headers=acc_setup["headers"])
        assert resp.status_code == 200, resp.text
        assert isinstance(resp.json(), list)


# ── Monthly Summary ────────────────────────────────────────────────────────────

class TestAccountingSummary:
    async def test_monthly_summary(self, async_client: AsyncClient, acc_setup: dict):
        resp = await async_client.get("/api/v1/accounting/summary/monthly",
            params={"year": 2025},
            headers=acc_setup["headers"])
        assert resp.status_code == 200, resp.text
        items = resp.json()
        assert isinstance(items, list)
