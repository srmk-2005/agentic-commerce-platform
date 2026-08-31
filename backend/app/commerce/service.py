"""AI Commerce Service for Deterministic Ranked Product Search and Product Lookup."""
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.commerce.catalog import format_ai_product
from app.commerce.schemas import AIProduct, AISearchResponse, AISearchResult, ProductAvailability
from app.db.models import Product


def get_ai_product_details(db: Session, product_id: int) -> AIProduct:
    """Retrieve detailed, machine-readable product state from current database truth."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found."
        )

    return format_ai_product(product)


def search_ai_products(
    db: Session,
    query: Optional[str] = None,
    merchant_id: Optional[int] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
) -> AISearchResponse:
    """
    Deterministic ranked product search for AI buyer agents.
    
    Ranking Weights:
    - Exact product-name match: +50
    - Category match: +30
    - Available in stock: +20
    - Within price range: +20
    - Partial word/token match: +10
    """
    db_query = db.query(Product).filter(Product.is_active.is_(True))

    if merchant_id:
        db_query = db_query.filter(Product.merchant_id == merchant_id)

    if category:
        db_query = db_query.filter(Product.category.ilike(f"%{category.strip()}%"))

    products = db_query.all()
    results: List[AISearchResult] = []

    clean_query = (query or "").strip().lower()
    query_tokens = clean_query.split() if clean_query else []

    for p in products:
        score = 0.0
        reasons = []

        p_name = p.name.lower()
        p_desc = (p.description or "").lower()
        p_cat = p.category.lower()

        # 1. Exact name match
        if clean_query and clean_query in p_name:
            score += 50.0
            reasons.append(f"Name matches '{clean_query}' (+50)")

        # 2. Category match
        if category and category.lower() in p_cat:
            score += 30.0
            reasons.append(f"Category matches '{category}' (+30)")
        elif any(tok in p_cat for tok in query_tokens):
            score += 30.0
            reasons.append(f"Query aligns with category '{p.category}' (+30)")

        # 3. Available in stock
        if p.stock_quantity > 0:
            score += 20.0
            reasons.append(f"In stock ({p.stock_quantity} units) (+20)")
        else:
            reasons.append("Out of stock (0 units)")

        # 4. Price compatibility
        price_matched = True
        if min_price is not None and p.price < min_price:
            price_matched = False
        if max_price is not None and p.price > max_price:
            price_matched = False

        if price_matched and (min_price is not None or max_price is not None):
            score += 20.0
            reasons.append(f"Price ₹{p.price} within target range (+20)")
        elif price_matched:
            score += 10.0

        # 5. Partial token match in description or sku
        for tok in query_tokens:
            if len(tok) > 2 and (tok in p_desc or tok in p.sku.lower()):
                score += 10.0
                reasons.append(f"Keyword '{tok}' found in product specs (+10)")
                break

        # Filter out if explicit price filter failed or score is 0 with a query
        if not price_matched and (min_price is not None or max_price is not None):
            continue

        if clean_query and score <= 0:
            continue

        formatted_prod = format_ai_product(p)
        results.append(
            AISearchResult(
                product=formatted_prod,
                relevance_score=round(score, 1),
                match_reasons=reasons,
            )
        )

    # Sort descending by relevance_score, then by price
    results.sort(key=lambda x: (x.relevance_score, -x.product.price), reverse=True)

    return AISearchResponse(
        query=query,
        total_matches=len(results),
        results=results,
    )
