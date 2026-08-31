"""Discovery and Manifest Services for AI Commerce."""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.commerce.policies import COMMERCE_VERSION
from app.commerce.schemas import AIMerchantManifest, AIMerchantProfile
from app.db.models import Merchant, Product


def get_merchant_manifest(db: Session, merchant_id: int) -> AIMerchantManifest:
    """Generate machine-readable capability manifest for the requested merchant."""
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant with ID {merchant_id} not found."
        )

    return AIMerchantManifest(
        merchant_id=merchant.id,
        name=merchant.name,
        version=COMMERCE_VERSION,
        capabilities={
            "catalog": True,
            "search": True,
            "product_details": True,
            "inventory": True,
            "order_creation": True,
            "payment": False,  # Payments strictly deferred to Phase 5
        },
        endpoints={
            "manifest": f"/api/v1/ai/merchant/{merchant_id}/manifest",
            "profile": f"/api/v1/ai/merchant/{merchant_id}/profile",
            "catalog": "/api/v1/ai/catalog",
            "search": "/api/v1/ai/search",
            "product": "/api/v1/ai/products/{{product_id}}",
            "orders": "/api/v1/ai/orders",
        },
    )


def get_merchant_profile(db: Session, merchant_id: int) -> AIMerchantProfile:
    """Generate structured profile of merchant with available categories and capabilities."""
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant with ID {merchant_id} not found."
        )

    # Query distinct categories
    categories = [
        r[0]
        for r in db.query(Product.category)
        .filter(Product.merchant_id == merchant_id)
        .filter(Product.is_active.is_(True))
        .distinct()
        .all()
    ]

    return AIMerchantProfile(
        merchant_id=merchant.id,
        merchant_name=merchant.name,
        description=merchant.description or "Retail Merchant Store",
        currency=merchant.currency,
        categories=sorted(categories),
        commerce_capabilities={
            "catalog": True,
            "inventory": True,
            "ordering": True,
            "payments": False,
        },
    )
