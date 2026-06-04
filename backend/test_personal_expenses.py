import urllib.request, urllib.error, json

BASE = "http://localhost:8000/api/v1"

def req(method, path, body=None, token=None):
    url = BASE + path
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json", "Connection": "close"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())
    except Exception as ex:
        return 0, {"error": str(ex)}

# Login
print("=== LOGIN ===")
s, r = req("POST", "/auth/login", {"username": "purushotham", "password": "123456"})
print(f"Status: {s}")
if s != 200: print(r); exit(1)
token = r["data"]["access_token"]
print(f"Logged in as {r['data']['user']['username']}")

# Categories
print("\n=== CATEGORIES ===")
s, r = req("GET", "/personal-expenses/categories", token=token)
print(f"Status: {s}, Response: {json.dumps(r, indent=2)[:500]}")

# Students
print("\n=== STUDENTS ===")
s, r = req("GET", "/students/?limit=1", token=token)
print(f"Status: {s}")
if s == 200 and r.get("data"):
    items = r["data"] if isinstance(r["data"], list) else r["data"].get("items", [])
    if items:
        sid = items[0]["id"]
        print(f"Student: {items[0].get('full_name', items[0].get('first_name','?'))} id={sid}")
    else:
        print("No students"); exit(1)
else:
    print(r); exit(1)
