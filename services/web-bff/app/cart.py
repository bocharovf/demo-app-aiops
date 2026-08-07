from itsdangerous import BadSignature, URLSafeSerializer

from app.config import settings

_serializer = URLSafeSerializer(settings.cookie_secret, salt="minishop-cart")
COOKIE_NAME = "minishop_cart"


def load_cart(cookie_value: str | None) -> dict[int, int]:
    """Returns {product_id: quantity}."""
    if not cookie_value:
        return {}
    try:
        data = _serializer.loads(cookie_value)
    except BadSignature:
        return {}
    return {int(k): int(v) for k, v in data.items()}


def dump_cart(cart: dict[int, int]) -> str:
    return _serializer.dumps({str(k): v for k, v in cart.items()})
