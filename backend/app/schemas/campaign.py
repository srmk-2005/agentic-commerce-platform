"""Pydantic schemas for Campaigns."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.db.models import ActorType, CampaignStatus, CampaignType, ProductCampaignRole


class CampaignProductCreate(BaseModel):
    product_id: int
    role: ProductCampaignRole = ProductCampaignRole.PRIMARY


class CampaignProductResponse(BaseModel):
    id: int
    product_id: int
    product_name: Optional[str] = None
    role: ProductCampaignRole

    model_config = ConfigDict(from_attributes=True)


class CampaignCreate(BaseModel):
    merchant_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    campaign_type: CampaignType
    status: CampaignStatus = CampaignStatus.DRAFT
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_by: ActorType = ActorType.MERCHANT
    products: List[CampaignProductCreate] = Field(default_factory=list)


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CampaignStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class CampaignResponse(BaseModel):
    id: int
    merchant_id: int
    name: str
    description: Optional[str] = None
    campaign_type: CampaignType
    status: CampaignStatus
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_by: ActorType
    created_at: datetime
    updated_at: datetime
    products: List[CampaignProductResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
