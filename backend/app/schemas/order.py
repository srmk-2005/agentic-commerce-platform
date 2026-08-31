"""Pydantic schemas for Order and OrderItem entities."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.db.models import OrderStatus
from app.schemas.customer import CustomerResponse
from app.schemas.merchant import MerchantResponse
from app.schemas.product import ProductResponse


class OrderItemCreate(BaseModel):
    product_id: int = Field(..., gt=0, description="ID of product being ordered")
    quantity: int = Field(..., gt=0, description="Quantity to purchase (must be > 0)")


class OrderItemResponse(BaseModel):
    id: int
    order_id: int
    product_id: int
    quantity: int
    unit_price: float
    subtotal: float
    product: Optional[ProductResponse] = None

    model_config = ConfigDict(from_attributes=True)


class OrderCreate(BaseModel):
    merchant_id: int = Field(..., gt=0, description="Target Merchant ID")
    customer_id: int = Field(..., gt=0, description="Customer placing the order")
    items: List[OrderItemCreate] = Field(..., min_length=1, description="List of items to order")


class OrderStatusUpdate(BaseModel):
    status: OrderStatus = Field(..., description="New order status")


class OrderResponse(BaseModel):
    id: int
    merchant_id: int
    customer_id: int
    status: OrderStatus
    total_amount: float
    currency: str
    payment_status: Optional[str] = "NOT_AVAILABLE"
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = []
    customer: Optional[CustomerResponse] = None
    merchant: Optional[MerchantResponse] = None

    model_config = ConfigDict(from_attributes=True)
