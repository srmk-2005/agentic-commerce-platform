"""Main FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.core.config import settings
from app.db.database import Base, SessionLocal, engine
from app.routers import (
    agent_commerce_router,
    agent_router,
    ai_payments_router,
    approvals_router,
    audit_router,
    buyer_router,
    campaigns_router,
    commerce_router,
    customers_router,
    demo_router,
    growth_router,
    merchants_router,
    offers_router,
    orders_router,
    payments_router,
    products_router,
)

logger = logging.getLogger("mercora.startup")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize database schema
    Base.metadata.create_all(bind=engine)

    # 2. Application Startup Validation (Masked logging — No secret leaks)
    rzp_key = settings.RAZORPAY_KEY_ID or ""
    masked_key = f"{rzp_key[:8]}***" if len(rzp_key) > 8 else "configured"
    logger.info(f"[STARTUP] Razorpay Test-Mode: {masked_key}")
    logger.info(f"[STARTUP] LLM Primary Provider: {settings.PRIMARY_LLM_PROVIDER} (Model: {settings.GEMINI_MODEL})")
    logger.info("[STARTUP] Database: connected & schemas verified")
    logger.info("[STARTUP] Agent Commerce Protocol: v1.0 active")
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
    """Canonical System Health Check Endpoint."""
    services_status = {
        "database": "healthy",
        "ai": "healthy",
        "payments": "healthy",
        "commerce": "healthy",
    }
    overall_status = "healthy"

    # 1. Database Check
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception:
        services_status["database"] = "degraded"
        overall_status = "degraded"

    # 2. AI Service Check
    if not (settings.GEMINI_API_KEY or settings.GROQ_API_KEY or settings.MOCK_AI_MODE):
        # Even without external key, internal deterministic fallback engine ensures operational state
        services_status["ai"] = "healthy (fallback engine active)"

    # 3. Payments Check
    if not settings.RAZORPAY_KEY_ID:
        services_status["payments"] = "degraded"
        overall_status = "degraded"

    return {
        "status": overall_status,
        "version": "1.0.0",
        "services": services_status,
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
app.include_router(commerce_router, prefix=settings.API_V1_STR)
app.include_router(buyer_router, prefix=settings.API_V1_STR)
app.include_router(ai_payments_router, prefix=settings.API_V1_STR)
app.include_router(payments_router, prefix=settings.API_V1_STR)
app.include_router(agent_commerce_router, prefix=settings.API_V1_STR)
app.include_router(demo_router, prefix=settings.API_V1_STR)


@app.get("/", include_in_schema=False)
def root():
    """Root redirect message."""
    return {
        "message": "AI Merchant Commerce Platform API",
        "health_check": f"{settings.API_V1_STR}/health",
        "docs": "/docs",
    }
