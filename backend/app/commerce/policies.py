"""Deterministic availability, attributes, and purchase constraint policies for AI Commerce."""
from typing import Any, Dict
from app.commerce.schemas import ProductAvailability
from app.db.models import Product

COMMERCE_VERSION = "1.0"
DEFAULT_MAX_QUANTITY_PER_ORDER = 5
DEFAULT_MIN_QUANTITY_PER_ORDER = 1


def determine_availability(stock_quantity: int, is_active: bool) -> ProductAvailability:
    """Deterministically determine product availability enum based on ground-truth inventory."""
    if not is_active:
        return ProductAvailability.INACTIVE
    if stock_quantity <= 0:
        return ProductAvailability.OUT_OF_STOCK
    if stock_quantity <= 5:
        return ProductAvailability.LOW_STOCK
    return ProductAvailability.IN_STOCK


def get_purchase_constraints(product: Product) -> Dict[str, Any]:
    """Return machine-readable purchase constraints for an AI buyer."""
    max_qty = min(DEFAULT_MAX_QUANTITY_PER_ORDER, max(1, product.stock_quantity))
    return {
        "max_quantity_per_order": max_qty,
        "min_quantity_per_order": DEFAULT_MIN_QUANTITY_PER_ORDER,
        "allow_backorders": False,
        "requires_merchant_confirmation": False,
    }


def get_product_attributes(product: Product) -> Dict[str, Any]:
    """Generate structured machine-readable attributes from product metadata."""
    name_lower = product.name.lower()
    cat_lower = product.category.lower()

    sizes = []
    if "shoe" in name_lower or "footwear" in cat_lower:
        sizes = [7, 8, 9, 10, 11]
    elif "shirt" in name_lower or "apparel" in cat_lower or "jersey" in name_lower:
        sizes = ["S", "M", "L", "XL"]

    color = "Standard"
    if "black" in name_lower:
        color = "Black"
    elif "blue" in name_lower:
        color = "Navy Blue"
    elif "red" in name_lower:
        color = "Crimson Red"
    elif "premium" in name_lower:
        color = "Stealth Gray"

    return {
        "brand": "ProSport India",
        "category": product.category,
        "sizes": sizes,
        "color": color,
        "sku": product.sku,
        "currency": product.currency,
    }
