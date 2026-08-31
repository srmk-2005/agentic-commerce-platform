"""API Routers package."""
from app.routers.agent import router as agent_router
from app.routers.approvals import router as approvals_router
from app.routers.audit import router as audit_router
from app.routers.buyer import router as buyer_router
from app.routers.campaigns import router as campaigns_router
from app.routers.commerce import router as commerce_router
from app.routers.customers import router as customers_router
from app.routers.growth import router as growth_router
from app.routers.merchants import router as merchants_router
from app.routers.offers import router as offers_router
from app.routers.orders import router as orders_router
from app.routers.products import router as products_router

__all__ = [
    "merchants_router",
    "products_router",
    "customers_router",
    "orders_router",
    "agent_router",
    "growth_router",
    "approvals_router",
    "campaigns_router",
    "offers_router",
    "audit_router",
    "commerce_router",
    "buyer_router",
]
