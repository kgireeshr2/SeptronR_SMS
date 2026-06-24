"""Test login against local backend."""
import urllib.request
import json

data = json.dumps({"username": "superadmin", "password": "12345678"}).encode()
req = urllib.request.Request(
    "http://localhost:8000/api/v1/auth/login",
    data=data,
    headers={"Content-Type": "application/json"}
)
try:
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read())
    user = result["data"]
    print(f"✓ Login OK: username={user['username']}, is_super_admin={user['is_super_admin']}")
except urllib.error.HTTPError as e:
    body = json.loads(e.read())
    print(f"✗ Login FAILED ({e.code}):", body.get("message"), body.get("data"))
except Exception as e:
    print(f"✗ Error: {e}")
