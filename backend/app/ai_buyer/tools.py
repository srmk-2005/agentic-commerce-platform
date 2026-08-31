"""Simulated AI Buyer Tools.

CRITICAL ARCHITECTURAL BOUNDARY:
This module simulates an external AI buyer. It does NOT import SQLAlchemy ORM models directly.
All communication flows through structured AI Commerce service interfaces / API contracts.
"""
from typing import Any, Dict, List, Optional
from app.commerce.catalog import get_ai_catalog
from app.commerce.discovery import get_merchant_manifest
from app.commerce.order_service import create_ai_order
from app.commerce.schemas import AIOrderCreateRequest, AIOrderItemCreate
from app.commerce.service import get_ai_product_details, search_ai_products


class AICommerceClient:
    """Client proxy for external AI Buyer to interact with merchant's AI Commerce Interface."""

    def __init__(self, db_session=None):
        self.db = db_session

    def discover_merchant(self, merchant_id: int) -> Dict[str, Any]:
        """Query merchant capability manifest."""
        manifest = get_merchant_manifest(self.db, merchant_id)
        return manifest.model_dump()

    def get_catalog(
        self,
        merchant_id: int,
        category: Optional[str] = None,
        in_stock: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch merchant AI catalog."""
        catalog_resp = get_ai_catalog(
            self.db,
            merchant_id=merchant_id,
            category=category,
            in_stock=in_stock,
        )
        return [p.model_dump() for p in catalog_resp.products]

    def search_products(
        self,
        query: str,
        merchant_id: int,
        category: Optional[str] = None,
        max_price: Optional[float] = None,
        min_price: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Perform ranked search on merchant catalog."""
        search_resp = search_ai_products(
            self.db,
            query=query,
            merchant_id=merchant_id,
            category=category,
            min_price=min_price,
            max_price=max_price,
        )
        return [r.model_dump() for r in search_resp.results]

    def get_product(self, product_id: int) -> Dict[str, Any]:
        """Fetch ground-truth product details & current inventory."""
        prod = get_ai_product_details(self.db, product_id)
        return prod.model_dump()

    def create_order(
        self,
        merchant_id: int,
        items: List[Dict[str, int]],
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Place an order via the AI Commerce ordering interface."""
        order_req = AIOrderCreateRequest(
            merchant_id=merchant_id,
            items=[
                AIOrderItemCreate(product_id=it["product_id"], quantity=it["quantity"])
                for it in items
            ],
            idempotency_key=idempotency_key,
        )
        order_resp = create_ai_order(self.db, order_req, idempotency_key=idempotency_key)
        return order_resp.model_dump()
