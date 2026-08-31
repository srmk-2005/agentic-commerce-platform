"""AI Commerce Interface REST Router for machine-readable discovery, catalog, and ordering."""
import json
from typing import Optional
from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session
from app.commerce.catalog import get_ai_catalog
from app.commerce.discovery import get_merchant_manifest, get_merchant_profile
from app.commerce.order_service import create_ai_order
from app.commerce.schemas import (
    AICatalogResponse,
    AIMerchantManifest,
    AIMerchantProfile,
    AIOrderCreateRequest,
    AIOrderResponse,
    AIProduct,
    AISearchResponse,
)
from app.commerce.service import get_ai_product_details, search_ai_products
from app.db.database import get_db
from app.db.models import ActorType, AuditLog

router = APIRouter(prefix="/ai", tags=["AI Commerce"])


@router.get(
    "/merchant/{merchant_id}/manifest",
    response_model=AIMerchantManifest,
    summary="Get AI Merchant Discovery Manifest",
    description="Machine-readable specification of merchant capabilities, endpoints, and protocol versions.",
)
def get_manifest_endpoint(
    merchant_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve machine-readable capabilities manifest."""
    manifest = get_merchant_manifest(db, merchant_id)

    # Log discovery event
    log = AuditLog(
        merchant_id=merchant_id,
        actor_type=ActorType.AI_BUYER,
        actor_id="simulated-ai-buyer",
        action="AI_MERCHANT_DISCOVERY",
        status="SUCCESS",
        reason="AI Buyer requested merchant discovery manifest",
        metadata_json=json.dumps({"version": manifest.version, "capabilities": manifest.capabilities}),
    )
    db.add(log)
    db.commit()

    return manifest


@router.get(
    "/merchant/{merchant_id}/profile",
    response_model=AIMerchantProfile,
    summary="Get AI Merchant Profile",
    description="Structured overview of merchant categories, store currency, and commerce capabilities.",
)
def get_profile_endpoint(
    merchant_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve structured merchant profile."""
    return get_merchant_profile(db, merchant_id)


@router.get(
    "/catalog",
    response_model=AICatalogResponse,
    summary="Query AI-Readable Product Catalog",
    description="Retrieve canonical AI-readable product listings filtered by merchant, category, price range, or stock status.",
)
def get_catalog_endpoint(
    merchant_id: Optional[int] = Query(None, description="Filter by Merchant ID"),
    category: Optional[str] = Query(None, description="Filter by Product Category"),
    search: Optional[str] = Query(None, description="Fuzzy search text across name/description/sku"),
    min_price: Optional[float] = Query(None, ge=0.0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0.0, description="Maximum price filter"),
    in_stock: Optional[bool] = Query(None, description="Filter by in-stock availability"),
    db: Session = Depends(get_db),
):
    """Query AI-readable catalog."""
    catalog = get_ai_catalog(
        db,
        merchant_id=merchant_id,
        category=category,
        search=search,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
    )

    if merchant_id:
        log = AuditLog(
            merchant_id=merchant_id,
            actor_type=ActorType.AI_BUYER,
            actor_id="simulated-ai-buyer",
            action="AI_CATALOG_SEARCH",
            status="SUCCESS",
            reason=f"Catalog searched with filters: category={category}, search={search}, in_stock={in_stock}",
            metadata_json=json.dumps({
                "category": category,
                "search": search,
                "matches_returned": catalog.total_count,
            }),
        )
        db.add(log)
        db.commit()

    return catalog


@router.get(
    "/search",
    response_model=AISearchResponse,
    summary="Deterministic Ranked AI Product Search",
    description="Search products with weighted deterministic ranking for AI Buyer query matching.",
)
def search_products_endpoint(
    query: Optional[str] = Query(None, description="Natural language search query"),
    merchant_id: Optional[int] = Query(None, description="Filter by Merchant ID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, ge=0.0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0.0, description="Maximum price"),
    db: Session = Depends(get_db),
):
    """Ranked product search."""
    results = search_ai_products(
        db,
        query=query,
        merchant_id=merchant_id,
        category=category,
        min_price=min_price,
        max_price=max_price,
    )

    if merchant_id:
        log = AuditLog(
            merchant_id=merchant_id,
            actor_type=ActorType.AI_BUYER,
            actor_id="simulated-ai-buyer",
            action="AI_CATALOG_SEARCH",
            status="SUCCESS",
            reason=f"Ranked search executed for query '{query}' ({results.total_matches} matches)",
            metadata_json=json.dumps({"query": query, "matches": results.total_matches}),
        )
        db.add(log)
        db.commit()

    return results


@router.get(
    "/products/{product_id}",
    response_model=AIProduct,
    summary="Get AI Product Details & Live Inventory",
    description="Retrieve ground-truth product specifications, attributes, real-time availability, and purchase constraints.",
)
def get_product_endpoint(
    product_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve detailed product state."""
    product = get_ai_product_details(db, product_id)

    log = AuditLog(
        merchant_id=product.merchant_id,
        actor_type=ActorType.AI_BUYER,
        actor_id="simulated-ai-buyer",
        action="AI_PRODUCT_VIEW",
        entity_type="Product",
        entity_id=product.id,
        status="SUCCESS",
        reason=f"Product '{product.name}' viewed. Live availability: {product.availability}",
        metadata_json=json.dumps({
            "product_id": product.id,
            "availability": product.availability,
            "stock_quantity": product.stock_quantity,
            "price": product.price,
        }),
    )
    db.add(log)
    db.commit()

    return product


@router.post(
    "/orders",
    response_model=AIOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Order via AI Commerce Interface",
    description="Place a machine-generated order with backend-calculated prices, stock deduction, and idempotency protection.",
)
def create_order_endpoint(
    order_data: AIOrderCreateRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
):
    """Create order from AI Buyer request."""
    return create_ai_order(db, order_data, idempotency_key=idempotency_key)
