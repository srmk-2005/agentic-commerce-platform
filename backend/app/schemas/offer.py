"""Pydantic schemas for Offers."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.db.models import DiscountType, OfferType


class OfferCreate(BaseModel):
    merchant_id: int = Field(..., gt=0)
    campaign_id: int = Field(..., gt=0)
    product_id: Optional[int] = None
    offer_type: OfferType
    discount_type: DiscountType = DiscountType.PERCENTAGE
    discount_value: float = Field(..., ge=0.0)
    maximum_discount_amount: Optional[float] = None
    status: str = "ACTIVE"


class OfferResponse(BaseModel):
    id: int
    merchant_id: int
    campaign_id: int
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    offer_type: OfferType
    discount_type: DiscountType
    discount_value: float
    maximum_discount_amount: Optional[float] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
