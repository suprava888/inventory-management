import urllib.request, urllib.error, json

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

print("=" * 55)
print("BACKEND API TEST SUITE")
print("=" * 55)

passed = 0
failed = 0

def check(label, condition, extra=""):
    global passed, failed
    if condition:
        print(f"  [PASS] {label} {extra}")
        passed += 1
    else:
        print(f"  [FAIL] {label} {extra}")
        failed += 1

# 1. Health check
s, d = req("GET", "/api/health")
check("GET /api/health", s == 200 and d["status"] == "ok", f"=> {d}")

# 2. Create category 1
s, cat1 = req("POST", "/api/categories", {"name": "Electronics", "description": "Gadgets and devices"})
check("POST /api/categories (Electronics)", s == 200 and cat1.get("id"), f"=> id={cat1.get('id')}")

# 3. Create category 2
s, cat2 = req("POST", "/api/categories", {"name": "Furniture", "description": "Home furniture"})
check("POST /api/categories (Furniture)", s == 200 and cat2.get("id"), f"=> id={cat2.get('id')}")

# 4. Duplicate category should 400
s, d = req("POST", "/api/categories", {"name": "Electronics"})
check("POST duplicate category => 400", s == 400, f"=> {s}")

# 5. List categories
s, cats = req("GET", "/api/categories")
check("GET /api/categories", s == 200 and len(cats) >= 2, f"=> {len(cats)} categories")

# 6. Update category
s, d = req("PUT", f"/api/categories/{cat1['id']}", {"name": "Electronics & Gadgets", "description": "Updated desc"})
check(f"PUT /api/categories/{cat1['id']}", s == 200 and d.get("name") == "Electronics & Gadgets", f"=> name={d.get('name')}")

# 7. Create item 1
s, item1 = req("POST", "/api/items", {"name": "Laptop Pro", "category_id": cat1["id"], "quantity": 10, "price": 999.99, "sku": "LAP-001", "status": "In Stock"})
check("POST /api/items (Laptop Pro)", s == 200 and item1.get("id"), f"=> id={item1.get('id')} cat={item1.get('category_name')}")

# 8. Create item 2
s, item2 = req("POST", "/api/items", {"name": "Office Chair", "category_id": cat2["id"], "quantity": 5, "price": 299.50, "sku": "CHR-001", "status": "In Stock"})
check("POST /api/items (Office Chair)", s == 200 and item2.get("id"), f"=> id={item2.get('id')} cat={item2.get('category_name')}")

# 9. Create item 3
s, item3 = req("POST", "/api/items", {"name": "Headphones", "category_id": cat1["id"], "quantity": 20, "price": 149.99, "sku": "HP-001", "status": "Low Stock"})
check("POST /api/items (Headphones)", s == 200 and item3.get("id"), f"=> id={item3.get('id')}")

# 10. Duplicate SKU should 400
s, d = req("POST", "/api/items", {"name": "Another Laptop", "quantity": 1, "price": 500, "sku": "LAP-001"})
check("POST duplicate SKU => 400", s == 400, f"=> {s}")

# 11. List all items
s, items = req("GET", "/api/items")
check("GET /api/items (list all)", s == 200 and len(items) >= 3, f"=> {len(items)} items")

# 12. Search by name
s, items = req("GET", "/api/items?q=Laptop")
check("GET /api/items?q=Laptop", s == 200 and len(items) >= 1, f"=> {len(items)} results")

# 13. Search by SKU
s, items = req("GET", "/api/items?q=HP-001")
check("GET /api/items?q=HP-001", s == 200 and len(items) == 1, f"=> {len(items)} result")

# 14. Filter by category
s, items = req("GET", f"/api/items?category_id={cat1['id']}")
check(f"GET /api/items?category_id={cat1['id']}", s == 200 and len(items) >= 2, f"=> {len(items)} items in Electronics")

# 15. Update item
s, d = req("PUT", f"/api/items/{item1['id']}", {"name": "Gaming Laptop", "category_id": cat1["id"], "quantity": 8, "price": 1299.99, "sku": "LAP-001", "status": "In Stock"})
check(f"PUT /api/items/{item1['id']}", s == 200 and d.get("name") == "Gaming Laptop", f"=> name={d.get('name')} price={d.get('price')}")

# 16. Delete item
s, d = req("DELETE", f"/api/items/{item3['id']}")
check(f"DELETE /api/items/{item3['id']}", s == 200, f"=> {d}")

# 17. Delete non-existent item => 404
s, d = req("DELETE", "/api/items/99999")
check("DELETE non-existent item => 404", s == 404, f"=> {s}")

# 18. Delete category (cascades items to null)
s, d = req("DELETE", f"/api/categories/{cat2['id']}")
check(f"DELETE /api/categories/{cat2['id']}", s == 200, f"=> {d}")

# 19. Delete non-existent category => 404
s, d = req("DELETE", "/api/categories/99999")
check("DELETE non-existent category => 404", s == 404, f"=> {s}")

# 20. Final state
s, cats = req("GET", "/api/categories")
s2, items = req("GET", "/api/items")
check("Final GET /api/categories", s == 200, f"=> {len(cats)} categories remaining")
check("Final GET /api/items", s2 == 200, f"=> {len(items)} items remaining")

print("=" * 55)
print(f"RESULTS: {passed} passed, {failed} failed out of {passed+failed} tests")
print("=" * 55)
