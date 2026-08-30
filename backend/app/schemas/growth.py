"""Pydantic schemas for AI Revenue Growth Action Proposals and Safety Policies."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SafetyCheckItem(BaseModel):
    check_name: str
    passed: bool
    details: str


class SafetyCheckResult(BaseModel):
    is_safe: bool
    checks: List[SafetyCheckItem]
    rejection_reasons: List[str] = Field(default_factory=list)


class ActionProposalCreate(BaseModel):
    merchant_id: int = Field(..., gt=0)
    action_type: str = Field(..., description="CREATE_CAMPAIGN, CREATE_OFFER, CREATE_BUNDLE, SLOW_MOVING_PROMOTION")
    opportunity_id: Optional[str] = None
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    campaign_type: str = Field(default="CROSS_SELL", description="CROSS_SELL, UPSELL, BUNDLE, SLOW_MOVING_PRODUCT")
    target_product_ids: List[int] = Field(..., min_length=1)
    primary_product_id: Optional[int] = None
    recommended_product_ids: List[int] = Field(default_factory=list)
    discount_type: str = Field(default="PERCENTAGE", description="PERCENTAGE or FIXED_AMOUNT")
    discount_value: float = Field(..., description="Proposed discount percentage or amount")
    campaign_duration_days: int = Field(default=7)
    expected_benefit: Optional[str] = None
    reasoning: Optional[str] = None
    risk_level: str = Field(default="LOW", description="LOW, MEDIUM, HIGH")


class ActionProposal(BaseModel):
    id: str
    merchant_id: int
    action_type: str
    opportunity_id: Optional[str] = None
    title: str
    description: str
    campaign_type: str
    target_product_ids: List[int]
    target_product_names: List[str] = Field(default_factory=list)
    primary_product_id: Optional[int] = None
    primary_product_name: Optional[str] = None
    recommended_product_ids: List[int] = Field(default_factory=list)
    recommended_product_names: List[str] = Field(default_factory=list)
    discount_type: str
    discount_value: float
    original_bundle_price: Optional[float] = None
    discounted_bundle_price: Optional[float] = None
    campaign_duration_days: int
    expected_benefit: str
    reasoning: str
    risk_level: str
    requires_approval: bool
    safety_check: SafetyCheckResult
    approval_id: Optional[int] = None
    agent_action_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class MerchantAiPolicyResponse(BaseModel):
    id: int
    merchant_id: int
    max_discount_percentage: float
    max_discount_amount: float
    auto_approve_non_financial: bool
    require_approval_for_campaigns: bool
    require_approval_for_discounts: bool
    max_campaign_duration_days: int
    is_enabled: bool

    model_config = ConfigDict(from_attributes=True)


class MerchantAiPolicyUpdate(BaseModel):
    max_discount_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    max_discount_amount: Optional[float] = Field(None, ge=0.0)
    auto_approve_non_financial: Optional[bool] = None
    require_approval_for_campaigns: Optional[bool] = None
    require_approval_for_discounts: Optional[bool] = None
    max_campaign_duration_days: Optional[int] = Field(None, gt=0, le=365)
    is_enabled: Optional[bool] = None
