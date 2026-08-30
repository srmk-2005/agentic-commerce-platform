"""Main FastAPI application entry point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.database import Base, engine
from app.routers import (
    agent_router,
    approvals_router,
    audit_router,
    campaigns_router,
    customers_router,
    growth_router,
    merchants_router,
    offers_router,
    orders_router,
    products_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API Foundation for AI Merchant Growth & Agentic Commerce Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(f"{settings.API_V1_STR}/health", tags=["Health"])
def health_check():
    """Health check endpoint confirming operational service status."""
    return {
        "status": "ok",
        "service": "ai-merchant-commerce-api",
    }


# Register v1 routers
app.include_router(merchants_router, prefix=settings.API_V1_STR)
app.include_router(products_router, prefix=settings.API_V1_STR)
app.include_router(customers_router, prefix=settings.API_V1_STR)
app.include_router(orders_router, prefix=settings.API_V1_STR)
app.include_router(agent_router, prefix=settings.API_V1_STR)
app.include_router(growth_router, prefix=settings.API_V1_STR)
app.include_router(approvals_router, prefix=settings.API_V1_STR)
app.include_router(campaigns_router, prefix=settings.API_V1_STR)
app.include_router(offers_router, prefix=settings.API_V1_STR)
app.include_router(audit_router, prefix=settings.API_V1_STR)


@app.get("/", include_in_schema=False)
def root():
    """Root redirect message."""
    return {
        "message": "AI Merchant Commerce Platform API",
        "health_check": f"{settings.API_V1_STR}/health",
        "docs": "/docs",
    }
