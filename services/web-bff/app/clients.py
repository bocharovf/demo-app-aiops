import httpx

from app.config import settings


async def list_products() -> list[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{settings.catalog_url}/products", timeout=5)
        resp.raise_for_status()
        return resp.json()


async def get_product(product_id: int) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{settings.catalog_url}/products/{product_id}", timeout=5)
        resp.raise_for_status()
        return resp.json()


async def create_order(user_email: str, user_name: str, items: list[dict]) -> httpx.Response:
    async with httpx.AsyncClient() as client:
        return await client.post(
            f"{settings.order_url}/orders",
            json={"user_email": user_email, "user_name": user_name, "items": items},
            timeout=15,
        )


async def get_order(order_id: int) -> httpx.Response:
    async with httpx.AsyncClient() as client:
        return await client.get(f"{settings.order_url}/orders/{order_id}", timeout=5)
