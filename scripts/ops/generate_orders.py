#!/usr/bin/env python3
"""Continuously place random orders against a running MiniShop stack.

Useful for generating background order traffic during testing.
Zero-dependency (stdlib only).

    python scripts/ops/generate_orders.py
    python scripts/ops/generate_orders.py --rate 5 --duration 120
"""
import argparse
import json
import random
import time
import urllib.error
import urllib.request
import os

ORDER_URL = os.environ.get("ORDER_URL", "http://localhost:8002")
CATALOG_URL = os.environ.get("CATALOG_URL", "http://localhost:8001")


def get_json(url: str) -> object:
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read())


def post_json(url: str, body: dict) -> tuple[int, dict | None]:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        return exc.code, None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rate", type=float, default=2.0, help="orders per second")
    parser.add_argument("--duration", type=float, default=0, help="seconds to run, 0 = forever")
    args = parser.parse_args()

    products = get_json(f"{CATALOG_URL}/products")
    if not products:
        raise SystemExit("catalog has no products - run scripts/seed_data.py first")

    interval = 1.0 / args.rate
    start = time.monotonic()
    placed = failed = 0

    print(f"Placing orders against {ORDER_URL} at ~{args.rate}/s (Ctrl+C to stop)")
    try:
        while args.duration == 0 or time.monotonic() - start < args.duration:
            product = random.choice(products)
            body = {
                "user_email": f"load-test-{random.randint(1, 1000)}@example.com",
                "user_name": "Load Test",
                "items": [{"product_id": product["id"], "quantity": random.randint(1, 3)}],
            }
            status, _ = post_json(f"{ORDER_URL}/orders", body)
            if status < 400:
                placed += 1
            else:
                failed += 1
            if (placed + failed) % 20 == 0:
                print(f"placed={placed} failed={failed}")
            time.sleep(interval)
    except KeyboardInterrupt:
        pass

    print(f"done. placed={placed} failed={failed}")


if __name__ == "__main__":
    main()
