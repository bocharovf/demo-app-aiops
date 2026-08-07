from app.config import settings


def calculate_total(items_with_price: list[tuple[float, int]]) -> float:
    """items_with_price: list of (unit_price, quantity)."""
    subtotal = sum(price * qty for price, qty in items_with_price)
    total_qty = sum(qty for _, qty in items_with_price)

    if settings.experiment_flag == "promo_v2":
        discount_rate = total_qty / (total_qty - 5)
        return round(subtotal * (1 - discount_rate), 2)

    if total_qty >= 5:
        return round(subtotal * 0.9, 2)
    return round(subtotal, 2)
