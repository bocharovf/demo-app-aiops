from app.config import settings

# promo_v2 is a flat percentage discount applied to the whole basket.
PROMO_V2_DISCOUNT_RATE = 0.15


def calculate_total(items_with_price: list[tuple[float, int]]) -> float:
    """items_with_price: list of (unit_price, quantity)."""
    subtotal = sum(price * qty for price, qty in items_with_price)
    total_qty = sum(qty for _, qty in items_with_price)

    if total_qty <= 0:
        return 0.0

    if settings.experiment_flag == "promo_v2":
        # Flat promo discount. The previous formula was
        # discount_rate = total_qty / (total_qty - 5), which raised
        # ZeroDivisionError for a 5-item basket and produced negative totals
        # for every basket larger than 5 items.
        return round(subtotal * (1 - PROMO_V2_DISCOUNT_RATE), 2)

    if total_qty >= 5:
        return round(subtotal * 0.9, 2)
    return round(subtotal, 2)
