import urllib.request, json

BASE = "http://127.0.0.1:8000"

def req(method, path, body=None):
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"} if body else {}
    r = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r) as res:
            return res.status, json.loads(res.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())

_, items = req("GET", "/api/items")
for item in items:
    iid = item["id"]
    req("DELETE", f"/api/items/{iid}")

_, cats = req("GET", "/api/categories")
for cat in cats:
    cid = cat["id"]
    req("DELETE", f"/api/categories/{cid}")

_, items2 = req("GET", "/api/items")
_, cats2 = req("GET", "/api/categories")
print(f"Cleanup done. Items: {len(items2)}, Categories: {len(cats2)}")
