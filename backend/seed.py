"""
Seed script — creates a demo business with categories and products.
Run: python seed.py
"""
import httpx

BASE = "http://localhost:8000/v1"

def seed():
    client = httpx.Client(base_url=BASE)

    # 1. Register
    print("Registering user...")
    r = client.post("/auth/register", json={
        "email": "demo@menu.tn",
        "password": "demo1234",
        "full_name": "Demo Owner",
        "phone": "+21612345678"
    })
    if r.status_code == 400 and "already registered" in r.text:
        print("  User exists, logging in...")
        r = client.post("/auth/login", json={"email": "demo@menu.tn", "password": "demo1234"})
    r.raise_for_status()
    token = r.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"  OK — token acquired")

    # 2. Create business
    print("Creating business...")
    r = client.post("/businesses", json={
        "name": "Café El Baraka",
        "name_ar": "مقهى البركة",
        "slug": "cafe-el-baraka",
        "category": "cafe",
        "city": "Tunis",
        "phone": "+21612345678",
        "whatsapp": "+21612345678",
    }, headers=headers)
    if r.status_code == 400 and "already have" in r.text:
        print("  Business exists, skipping creation")
    else:
        r.raise_for_status()
        print(f"  Created: cafe-el-baraka")

    # 3. Create categories
    print("Creating categories...")
    categories = [
        {"name": "Boissons Chaudes", "name_ar": "مشروبات ساخنة", "sort_order": 0},
        {"name": "Boissons Froides", "name_ar": "مشروبات باردة", "sort_order": 1},
        {"name": "Pâtisseries",      "name_ar": "حلويات",         "sort_order": 2},
    ]
    cat_ids = {}
    for cat in categories:
        r = client.post("/categories", json=cat, headers=headers)
        r.raise_for_status()
        cat_ids[cat["name"]] = r.json()["data"]["id"]
        print(f"  {cat['name']} — {cat_ids[cat['name']]}")

    # 4. Create products
    print("Creating products...")
    products = [
        # Boissons Chaudes
        {"name": "Café Express",   "name_ar": "قهوة إكسبريس", "price": "1.500", "category_id": cat_ids["Boissons Chaudes"], "is_featured": True},
        {"name": "Café au Lait",   "name_ar": "قهوة بالحليب",  "price": "2.000", "category_id": cat_ids["Boissons Chaudes"]},
        {"name": "Thé à la Menthe","name_ar": "شاي بالنعناع",  "price": "1.500", "category_id": cat_ids["Boissons Chaudes"]},
        # Boissons Froides
        {"name": "Jus d'Orange",   "name_ar": "عصير برتقال",   "price": "3.500", "category_id": cat_ids["Boissons Froides"], "is_featured": True},
        {"name": "Smoothie Mangue","name_ar": "سموزي مانغو",   "price": "5.000", "category_id": cat_ids["Boissons Froides"]},
        {"name": "Eau Minérale",   "name_ar": "ماء معدني",     "price": "0.800", "category_id": cat_ids["Boissons Froides"]},
        # Pâtisseries
        {"name": "Makroudh",       "name_ar": "مقروض",         "price": "0.500", "category_id": cat_ids["Pâtisseries"], "description": "Pâtisserie tunisienne aux dattes"},
        {"name": "Baklawa",        "name_ar": "بقلاوة",        "price": "1.200", "category_id": cat_ids["Pâtisseries"]},
        {"name": "Bambalouni",     "name_ar": "بنبالوني",      "price": "0.800", "category_id": cat_ids["Pâtisseries"]},
    ]
    for p in products:
        r = client.post("/products", json=p, headers=headers)
        r.raise_for_status()
        print(f"  {p['name']} — {p['price']} TND")

    # 5. Publish
    print("Publishing business...")
    r = client.post("/businesses/me/publish", headers=headers)
    r.raise_for_status()
    print("  Published!")

    print()
    print("=" * 40)
    print("Demo page: http://localhost:3000/cafe-el-baraka")
    print("=" * 40)

if __name__ == "__main__":
    seed()
