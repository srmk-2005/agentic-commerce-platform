"""Pydantic schemas for Merchant entity."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class MerchantBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Business or merchant name")
    email: EmailStr = Field(..., description="Merchant contact email")
    description: Optional[str] = Field(None, description="Detailed business description")
    currency: str = Field("INR", min_length=3, max_length=3, description="ISO currency code, e.g. INR")
    is_active: bool = Field(True, description="Whether merchant account is active")


class MerchantCreate(MerchantBase):
    pass


class MerchantUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    description: Optional[str] = None
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    is_active: Optional[bool] = None


class MerchantResponse(MerchantBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
