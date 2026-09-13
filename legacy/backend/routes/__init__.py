# Routes module
from routes.auth import router as auth_router
from routes.products import router as products_router
from routes.cart import router as cart_router
from routes.orders import router as orders_router
from routes.payments import router as payments_router
from routes.inventory import router as inventory_router

__all__ = [
    'auth_router',
    'products_router',
    'cart_router',
    'orders_router',
    'payments_router',
    'inventory_router',
]
