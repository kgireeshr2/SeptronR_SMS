import httpx, asyncio, json

BASE = "http://localhost:8000/api/v1"
SCHOOL_ID = "891dc063-d002-4181-aecf-9df31c876992"

async def main():
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{BASE}/auth/login", json={"username": "principal@stonevalley.edu", "password": "Admin@123"})
        token = r.json()["data"]["access_token"]
        h = {"Authorization": f"Bearer {token}", "X-School-Id": SCHOOL_ID}
        print(f"Token OK: {token[:20]}...")

        reports = ["student_list","fee_defaulters","fee_collection","student_attendance","staff_list","staff_attendance","low_attendance","monthly_pl","income_expense"]
        for rid in reports:
            resp = await c.get(f"{BASE}/reports/{rid}", headers=h)
            if resp.status_code == 200:
                d = resp.json()
                print(f"  OK  {rid} -> {d['total_rows']} rows, cols={list(d['data'][0].keys()) if d['data'] else 'empty'}")
            else:
                try:
                    detail = resp.json()
                except:
                    detail = resp.text[:200]
                print(f"  ERR {rid} -> {resp.status_code}: {detail}")

asyncio.run(main())
