"""Pydantic schemas for Product entity."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Product title/name")
    description: Optional[str] = Field(None, description="Detailed product description")
    category: str = Field(..., min_length=1, max_length=100, description="Product category name")
    price: float = Field(..., ge=0.0, description="Product unit price (non-negative)")
    currency: str = Field("INR", min_length=3, max_length=3, description="Currency code")
    stock_quantity: int = Field(0, ge=0, description="Available inventory stock quantity")
    sku: str = Field(..., min_length=1, max_length=100, description="Stock Keeping Unit (SKU)")
    is_active: bool = Field(True, description="Whether product is listed and active")


class ProductCreate(ProductBase):
    merchant_id: int = Field(..., gt=0, description="Merchant ID owning this product")


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    price: Optional[float] = Field(None, ge=0.0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    stock_quantity: Optional[int] = Field(None, ge=0)
    sku: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    id: int
    merchant_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
