"""Pydantic schemas for Simulated AI Buyer Agent."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class BuyerChatRequest(BaseModel):
    merchant_id: int = Field(default=1, gt=0)
    message: str = Field(..., min_length=1, max_length=1000)


class BuyerProductOption(BaseModel):
    id: int
    name: str
    category: str
    price: float
    availability: str
    stock_quantity: int
    relevance_score: float = 0.0
    reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class BuyerChatResponse(BaseModel):
    response: str
    candidates: List[BuyerProductOption] = Field(default_factory=list)
    selected_product: Optional[BuyerProductOption] = None
    order_created: Optional[Dict[str, Any]] = None
    execution_steps: List[str] = Field(default_factory=list)


class BuyerSimulationRequest(BaseModel):
    merchant_id: int = Field(default=1, gt=0)
    product_id: int = Field(..., gt=0)
    quantity: int = Field(default=1, gt=0)
    idempotency_key: Optional[str] = None


class BuyerSimulationResponse(BaseModel):
    success: bool
    order: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    explainability: str
    payment_note: str = "Payment not available in Phase 4. Will be supported in Phase 5."
