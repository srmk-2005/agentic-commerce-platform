"""Pydantic schemas for Machine-Readable AI Commerce Interface."""
import enum
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ProductAvailability(str, enum.Enum):
    IN_STOCK = "IN_STOCK"
    LOW_STOCK = "LOW_STOCK"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    INACTIVE = "INACTIVE"


class AIProduct(BaseModel):
    id: int
    merchant_id: int
    name: str
    description: Optional[str] = None
    category: str
    price: float
    currency: str = "INR"
    availability: ProductAvailability
    stock_quantity: int
    sku: str
    attributes: Dict[str, Any] = Field(default_factory=dict)
    purchase_constraints: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class AIMerchantProfile(BaseModel):
    merchant_id: int
    merchant_name: str
    description: Optional[str] = None
    currency: str = "INR"
    categories: List[str] = Field(default_factory=list)
    commerce_capabilities: Dict[str, bool] = Field(
        default_factory=lambda: {
            "catalog": True,
            "search": True,
            "product_details": True,
            "inventory": True,
            "ordering": True,
            "payments": False,  # Phase 4 explicitly specifies payments = false
        }
    )

    model_config = ConfigDict(from_attributes=True)


class AIMerchantManifest(BaseModel):
    merchant_id: int
    name: str
    version: str = "1.0"
    capabilities: Dict[str, bool] = Field(
        default_factory=lambda: {
            "catalog": True,
            "search": True,
            "product_details": True,
            "inventory": True,
            "order_creation": True,
            "payment": False,
        }
    )
    endpoints: Dict[str, str] = Field(
        default_factory=lambda: {
            "manifest": "/api/v1/ai/merchant/{merchant_id}/manifest",
            "profile": "/api/v1/ai/merchant/{merchant_id}/profile",
            "catalog": "/api/v1/ai/catalog",
            "search": "/api/v1/ai/search",
            "product": "/api/v1/ai/products/{product_id}",
            "orders": "/api/v1/ai/orders",
        }
    )


class AICatalogResponse(BaseModel):
    merchant_id: Optional[int] = None
    total_count: int
    products: List[AIProduct]


class AISearchResult(BaseModel):
    product: AIProduct
    relevance_score: float
    match_reasons: List[str] = Field(default_factory=list)


class AISearchResponse(BaseModel):
    query: Optional[str] = None
    total_matches: int
    results: List[AISearchResult]


class AIOrderItemCreate(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)


class AIOrderCreateRequest(BaseModel):
    merchant_id: int = Field(..., gt=0)
    items: List[AIOrderItemCreate] = Field(..., min_length=1)
    idempotency_key: Optional[str] = Field(None, description="Client-supplied idempotency key")


class AIOrderItemResponse(BaseModel):
    product_id: int
    name: str
    quantity: int
    unit_price: float
    subtotal: float

    model_config = ConfigDict(from_attributes=True)


class AIOrderResponse(BaseModel):
    order_id: int
    merchant_id: int
    status: str
    items: List[AIOrderItemResponse]
    total_amount: float
    currency: str = "INR"
    payment_status: str = "NOT_AVAILABLE"
    idempotency_key: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
