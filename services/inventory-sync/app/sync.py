import logging
import sys
import time

import psycopg

from . import erp_client as erp
from .config import settings
from .logging_config import configure_logging

logger = logging.getLogger(__name__)


def run() -> int:
    started_at = time.monotonic()
    logger.info("inventory sync started")
    updated = 0

    with psycopg.connect(settings.database_url) as conn:
        with conn.transaction():
            # Блокируем строки склада, чтобы резервирование не пересекалось
            # с перезаписью остатка.
            rows = conn.execute(
                "SELECT product_id, quantity FROM catalog.stock ORDER BY product_id FOR UPDATE"
            ).fetchall()
            for product_id, current in rows:
                try:
                    qty = erp.get_stock(str(product_id))
                except erp.StockNotFound:
                    logger.warning("product not found in 1C, skipping", extra={"product_id": product_id})
                    continue
                if qty != current:
                    conn.execute(
                        "UPDATE catalog.stock SET quantity = %s, updated_at = now() WHERE product_id = %s",
                        (qty, product_id),
                    )
                    updated += 1

    duration = time.monotonic() - started_at
    logger.info("inventory sync finished", extra={"updated": updated, "duration_seconds": round(duration, 3)})
    return 0


def main() -> int:
    configure_logging(settings.log_level)
    try:
        return run()
    except Exception:
        logger.exception("inventory sync failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
