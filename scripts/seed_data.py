#!/usr/bin/env python3
"""Populate the catalog with demo categories and products. Idempotent - safe
to re-run, categories/products are matched by name.

Zero-dependency (stdlib only) so it can be run against docker-compose or a
kubectl port-forward without setting up a virtualenv first:

    python scripts/seed_data.py
    CATALOG_URL=http://localhost:8001 python scripts/seed_data.py
"""
import json
import os
import sys
import urllib.request

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

CATALOG_URL = os.environ.get("CATALOG_URL", "http://localhost:8001")

PRODUCTS = [
    {"category": "Электроника", "name": "Наушники", "description": "Беспроводные, шумоподавление", "price": 49.90, "initial_quantity": 25},
    {"category": "Электроника", "name": "Powerbank 20000mAh", "description": "Быстрая зарядка", "price": 34.50, "initial_quantity": 15},
    {"category": "Книги", "name": "Чистый код", "description": "Р. Мартин", "price": 19.90, "initial_quantity": 8},
    {"category": "Книги", "name": "SRE: Google", "description": "Site Reliability Engineering", "price": 24.90, "initial_quantity": 5},
    {"category": "Игрушки", "name": "Кубик Рубика", "description": "Классический 3x3", "price": 9.90, "initial_quantity": 40},
]


def request(method: str, path: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(f"{CATALOG_URL}{path}", data=data, method=method)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def get_or_create_category(name: str) -> int:
    category = request("POST", "/categories", {"name": name})
    return category["id"]


def main() -> None:
    print(f"Seeding catalog at {CATALOG_URL}")
    category_ids: dict[str, int] = {}
    existing_products = {p["name"] for p in request("GET", "/products")}

    for product in PRODUCTS:
        if product["name"] in existing_products:
            print(f"skip (already exists): {product['name']}")
            continue

        category_id = category_ids.setdefault(product["category"], get_or_create_category(product["category"]))
        created = request(
            "POST",
            "/products",
            {
                "category_id": category_id,
                "name": product["name"],
                "description": product["description"],
                "price": product["price"],
                "initial_quantity": product["initial_quantity"],
            },
        )
        print(f"created product #{created['id']}: {created['name']}")


if __name__ == "__main__":
    main()
