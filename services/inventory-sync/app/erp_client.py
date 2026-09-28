import requests

from .config import settings


class StockNotFound(Exception):
    pass


def get_stock(product_id: str) -> int:
    url = f"{settings.erp_base_url}/ut/hs/inventory/v1/stock/{product_id}"
    response = requests.get(url)
    if response.status_code == 404:
        raise StockNotFound(product_id)
    response.raise_for_status()
    return response.json()["quantity"]
