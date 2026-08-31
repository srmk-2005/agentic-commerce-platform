"""Catalog retrieval and AIProduct formatting for AI Commerce."""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.commerce.policies import determine_availability, get_product_attributes, get_purchase_constraints
from app.commerce.schemas import AICatalogResponse, AIProduct, ProductAvailability
from app.db.models import Product


def format_ai_product(product: Product) -> AIProduct:
    """Format SQLAlchemy Product model into canonical AI-readable AIProduct schema."""
    availability = determine_availability(product.stock_quantity, product.is_active)
    attributes = get_product_attributes(product)
    constraints = get_purchase_constraints(product)

    return AIProduct(
        id=product.id,
        merchant_id=product.merchant_id,
        name=product.name,
        description=product.description,
        category=product.category,
        price=float(product.price),
        currency=product.currency,
        availability=availability,
        stock_quantity=product.stock_quantity,
        sku=product.sku,
        attributes=attributes,
        purchase_constraints=constraints,
    )


get_canonical_product = format_ai_product


def get_ai_catalog(
    db: Session,
    merchant_id: Optional[int] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock: Optional[bool] = None,
) -> AICatalogResponse:
    """Retrieve filtered catalog of active products formatted for AI consumption."""
    query = db.query(Product).filter(Product.is_active.is_(True))

    if merchant_id:
        query = query.filter(Product.merchant_id == merchant_id)

    if category:
        query = query.filter(Product.category.ilike(f"%{category.strip()}%"))

    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            (Product.name.ilike(search_term))
            | (Product.description.ilike(search_term))
            | (Product.sku.ilike(search_term))
            | (Product.category.ilike(search_term))
        )

    if min_price is not None:
        query = query.filter(Product.price >= min_price)

    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    if in_stock is True:
        query = query.filter(Product.stock_quantity > 0)
    elif in_stock is False:
        query = query.filter(Product.stock_quantity == 0)

    products = query.order_by(Product.id.asc()).all()
    ai_products = [format_ai_product(p) for p in products]

    return AICatalogResponse(
        merchant_id=merchant_id,
        total_count=len(ai_products),
        products=ai_products,
    )
