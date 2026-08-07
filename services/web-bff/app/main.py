import logging

import httpx
from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from prometheus_fastapi_instrumentator import Instrumentator

from app import clients
from app.cart import COOKIE_NAME, dump_cart, load_cart
from app.config import settings
from app.logging_config import configure_logging

configure_logging(settings.log_level)
logger = logging.getLogger("web-bff.main")

app = FastAPI(title="web-bff")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

BACKENDS = [
    ("catalog", settings.catalog_url),
    ("order", settings.order_url),
    ("notification", settings.notification_url),
]


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/ready")
async def ready():
    return {"status": "ready"}


@app.get("/")
async def index(request: Request):
    try:
        products = await clients.list_products()
        error = None
    except httpx.HTTPError as exc:
        logger.error("failed to load catalog", extra={"error": str(exc)})
        products, error = [], "Каталог временно недоступен"
    return templates.TemplateResponse(request, "index.html", {"products": products, "error": error})


@app.post("/cart/add")
async def cart_add(request: Request, product_id: int = Form(...), quantity: int = Form(1)):
    cart = load_cart(request.cookies.get(COOKIE_NAME))
    cart[product_id] = cart.get(product_id, 0) + quantity
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(COOKIE_NAME, dump_cart(cart), httponly=True, samesite="lax")
    return response


@app.get("/cart")
async def cart_view(request: Request):
    cart = load_cart(request.cookies.get(COOKIE_NAME))
    items, error = [], None
    try:
        for product_id, quantity in cart.items():
            product = await clients.get_product(product_id)
            items.append({"name": product["name"], "price": product["price"], "quantity": quantity})
    except httpx.HTTPError as exc:
        logger.error("failed to load product for cart", extra={"error": str(exc)})
        error = "Не удалось загрузить содержимое корзины"
    return templates.TemplateResponse(request, "cart.html", {"items": items, "error": error})


@app.post("/cart/checkout")
async def cart_checkout(request: Request, user_email: str = Form(...), user_name: str = Form(...)):
    cart = load_cart(request.cookies.get(COOKIE_NAME))
    items = [{"product_id": pid, "quantity": qty} for pid, qty in cart.items()]

    resp = await clients.create_order(user_email, user_name, items)
    if resp.status_code >= 400:
        logger.error("order creation failed", extra={"status_code": resp.status_code, "body": resp.text})
        return templates.TemplateResponse(
            request, "cart.html", {"items": [], "error": f"Не удалось оформить заказ: {resp.text}"}, status_code=502
        )

    order = resp.json()
    response = RedirectResponse(url=f"/orders/{order['id']}", status_code=303)
    response.delete_cookie(COOKIE_NAME)
    return response


@app.get("/orders/{order_id}")
async def order_status(request: Request, order_id: int):
    resp = await clients.get_order(order_id)
    if resp.status_code == 404:
        return templates.TemplateResponse(request, "order_status.html", {"order": None, "error": "Заказ не найден"})
    resp.raise_for_status()
    return templates.TemplateResponse(request, "order_status.html", {"order": resp.json(), "error": None})


@app.get("/admin")
async def admin(request: Request):
    services = []
    async with httpx.AsyncClient(timeout=3) as client:
        for name, base_url in BACKENDS:
            health_ok = ready_ok = False
            try:
                health_ok = (await client.get(f"{base_url}/health")).status_code == 200
                ready_ok = (await client.get(f"{base_url}/ready")).status_code == 200
            except httpx.HTTPError:
                pass
            services.append({"name": name, "health": health_ok, "ready": ready_ok, "metrics_url": f"{base_url}/metrics"})
    return templates.TemplateResponse(request, "admin.html", {"services": services, "error": None})
