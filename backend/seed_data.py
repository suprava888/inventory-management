"""
Seed script — adds sample categories and inventory items to the database.
Run once: python seed_data.py
"""
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

# ── Categories ────────────────────────────────────────────────────────────────
CATEGORIES = [
    {"name": "Electronics",    "description": "Gadgets, devices and accessories"},
    {"name": "Furniture",      "description": "Office and home furniture"},
    {"name": "Clothing",       "description": "Apparel and accessories"},
    {"name": "Food & Drinks",  "description": "Groceries and beverages"},
    {"name": "Sports",         "description": "Sports and outdoor equipment"},
    {"name": "Stationery",     "description": "Office and school supplies"},
]

# ── Items per category ────────────────────────────────────────────────────────
ITEMS = {
    "Electronics": [
        {"name": "Wireless Mouse",       "sku": "ELEC-001", "quantity": 50,  "price": 29.99,   "status": "In Stock"},
        {"name": "Mechanical Keyboard",  "sku": "ELEC-002", "quantity": 30,  "price": 89.99,   "status": "In Stock"},
        {"name": "USB-C Hub",            "sku": "ELEC-003", "quantity": 75,  "price": 49.99,   "status": "In Stock"},
        {"name": "27\" Monitor",         "sku": "ELEC-004", "quantity": 12,  "price": 349.99,  "status": "Low Stock"},
        {"name": "Webcam HD",            "sku": "ELEC-005", "quantity": 0,   "price": 79.99,   "status": "Out of Stock"},
        {"name": "Noise Cancelling Headphones", "sku": "ELEC-006", "quantity": 20, "price": 199.99, "status": "In Stock"},
    ],
    "Furniture": [
        {"name": "Ergonomic Office Chair", "sku": "FURN-001", "quantity": 15, "price": 299.99, "status": "In Stock"},
        {"name": "Standing Desk",          "sku": "FURN-002", "quantity": 8,  "price": 499.99, "status": "Low Stock"},
        {"name": "Bookshelf 5-tier",       "sku": "FURN-003", "quantity": 20, "price": 149.99, "status": "In Stock"},
        {"name": "Filing Cabinet",         "sku": "FURN-004", "quantity": 0,  "price": 119.99, "status": "Out of Stock"},
    ],
    "Clothing": [
        {"name": "Cotton T-Shirt (M)",   "sku": "CLTH-001", "quantity": 100, "price": 19.99,  "status": "In Stock"},
        {"name": "Denim Jeans (32x32)",  "sku": "CLTH-002", "quantity": 45,  "price": 59.99,  "status": "In Stock"},
        {"name": "Winter Jacket",        "sku": "CLTH-003", "quantity": 5,   "price": 129.99, "status": "Low Stock"},
        {"name": "Running Shoes (42)",   "sku": "CLTH-004", "quantity": 30,  "price": 89.99,  "status": "In Stock"},
    ],
    "Food & Drinks": [
        {"name": "Arabica Coffee Beans 1kg", "sku": "FOOD-001", "quantity": 200, "price": 14.99, "status": "In Stock"},
        {"name": "Green Tea (50 bags)",       "sku": "FOOD-002", "quantity": 150, "price": 8.99,  "status": "In Stock"},
        {"name": "Protein Bar Box (12)",      "sku": "FOOD-003", "quantity": 60,  "price": 24.99, "status": "In Stock"},
        {"name": "Mineral Water 24-pack",     "sku": "FOOD-004", "quantity": 3,   "price": 9.99,  "status": "Low Stock"},
    ],
    "Sports": [
        {"name": "Yoga Mat",             "sku": "SPRT-001", "quantity": 40,  "price": 34.99,  "status": "In Stock"},
        {"name": "Adjustable Dumbbells", "sku": "SPRT-002", "quantity": 10,  "price": 149.99, "status": "Low Stock"},
        {"name": "Jump Rope",            "sku": "SPRT-003", "quantity": 80,  "price": 12.99,  "status": "In Stock"},
        {"name": "Resistance Bands Set", "sku": "SPRT-004", "quantity": 0,   "price": 22.99,  "status": "Out of Stock"},
    ],
    "Stationery": [
        {"name": "Ballpoint Pens (10pk)", "sku": "STAT-001", "quantity": 300, "price": 4.99,  "status": "In Stock"},
        {"name": "A4 Notebook 200pg",     "sku": "STAT-002", "quantity": 120, "price": 7.99,  "status": "In Stock"},
        {"name": "Sticky Notes (5 pads)", "sku": "STAT-003", "quantity": 90,  "price": 5.99,  "status": "In Stock"},
        {"name": "Stapler",               "sku": "STAT-004", "quantity": 2,   "price": 12.99, "status": "Low Stock"},
    ],
}

print("=" * 55)
print("SEEDING DATABASE")
print("=" * 55)

cat_map = {}

for cat in CATEGORIES:
    s, d = req("POST", "/api/categories", cat)
    if s == 200:
        cat_map[cat["name"]] = d["id"]
        print(f"  [+] Category: {cat['name']}  (id={d['id']})")
    elif s == 400:
        # already exists — fetch id
        _, cats = req("GET", "/api/categories")
        for c in cats:
            if c["name"] == cat["name"]:
                cat_map[cat["name"]] = c["id"]
                print(f"  [=] Category already exists: {cat['name']}  (id={c['id']})")
                break
    else:
        print(f"  [!] Failed to create category {cat['name']}: {s} {d}")

print()
item_count = 0
for cat_name, items in ITEMS.items():
    cat_id = cat_map.get(cat_name)
    for item in items:
        payload = {**item, "category_id": cat_id}
        s, d = req("POST", "/api/items", payload)
        if s == 200:
            print(f"  [+] {item['name']}  (${item['price']}  qty={item['quantity']}  {item['status']})")
            item_count += 1
        elif s == 400:
            print(f"  [=] Already exists: {item['name']}")
        else:
            print(f"  [!] Failed: {item['name']}: {s} {d}")

print()
s, stats = req("GET", "/api/stats")
print("=" * 55)
print(f"SEED COMPLETE")
print(f"  Categories : {stats['total_categories']}")
print(f"  Items      : {stats['total_items']}")
print(f"  Total units: {stats['total_units']}")
print(f"  Stock value: ${stats['stock_value']:,.2f}")
print("=" * 55)
