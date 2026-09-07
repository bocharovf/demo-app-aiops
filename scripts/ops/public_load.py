#!/usr/bin/env python3
"""Generate checkout load against the public MiniShop URL - runs from any
machine with internet access, no kubectl/port-forward/cluster access needed.

Goes through the real user-facing path (add to cart -> checkout) on
web-bff, exactly like a browser would. Each order uses a fresh cookie jar
(a new "customer"). Connection failures (service fully down, e.g. scenario
1.2) count as failed instead of crashing.

Zero-dependency (stdlib only).

    python scripts/ops/public_load.py
    python scripts/ops/public_load.py --rate 3 --duration 60
    python scripts/ops/public_load.py --url http://201.24.114.118.nip.io:31079
"""
import argparse
import http.cookiejar
import random
import time
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_URL = "http://201.24.114.118.nip.io:31079"
TIMEOUT = 15


def place_order(base_url: str, product_ids: list[int], i: int) -> tuple[bool, str]:
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    product_id = random.choice(product_ids)
    quantity = random.randint(1, 3)

    try:
        add_data = urllib.parse.urlencode({"product_id": product_id, "quantity": quantity}).encode()
        opener.open(urllib.request.Request(f"{base_url}/cart/add", data=add_data, method="POST"), timeout=TIMEOUT)

        checkout_data = urllib.parse.urlencode(
            {"user_email": f"load-test-{i}@example.com", "user_name": "Load Test"}
        ).encode()
        with opener.open(
            urllib.request.Request(f"{base_url}/cart/checkout", data=checkout_data, method="POST"), timeout=TIMEOUT
        ) as resp:
            return True, f"HTTP {resp.status}"
    except urllib.error.HTTPError as exc:
        return False, f"HTTP {exc.code}"
    except urllib.error.URLError as exc:
        return False, f"connection error: {exc.reason}"
    except TimeoutError:
        return False, "timeout"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=DEFAULT_URL, help="base URL of the storefront")
    parser.add_argument("--rate", type=float, default=1.0, help="checkouts per second")
    parser.add_argument("--duration", type=float, default=30, help="seconds to run, 0 = forever")
    parser.add_argument("--products", default="1,2,3,4,5", help="comma-separated product ids to pick from")
    args = parser.parse_args()

    product_ids = [int(p) for p in args.products.split(",")]
    interval = 1.0 / args.rate
    start = time.monotonic()
    ok = failed = 0
    i = 0

    print(f"Placing orders against {args.url} at ~{args.rate}/s (Ctrl+C to stop)")
    try:
        while args.duration == 0 or time.monotonic() - start < args.duration:
            i += 1
            success, detail = place_order(args.url, product_ids, i)
            if success:
                ok += 1
            else:
                failed += 1
            if i % 10 == 0:
                print(f"...{i} sent: ok={ok} failed={failed} (last: {detail})")
            time.sleep(interval)
    except KeyboardInterrupt:
        pass

    print(f"done. ok={ok} failed={failed}")


if __name__ == "__main__":
    main()
