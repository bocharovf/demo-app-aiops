from app.config import settings


def calculate_total(items_with_price: list[tuple[float, int]]) -> float:
    """items_with_price: list of (unit_price, quantity)."""
    subtotal = sum(price * qty for price, qty in items_with_price)
    total_qty = sum(qty for _, qty in items_with_price)

    if settings.experiment_flag == "promo_v2":
        # promo_v2: 15% off from 5 items. The previous formula
        # (total_qty / (total_qty - 5)) divided by zero at 5 items and
        # returned negative totals above 5 items, so it was removed.
        if total_qty >= 5:
            return round(subtotal * 0.85, 2)
        return round(subtotal, 2)

    if total_qty >= 5:
        return round(subtotal * 0.9, 2)
    return round(subtotal, 2)
