"""Pydantic schemas for the Merchant AI Agent."""
import enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.growth import ActionProposal


class OpportunityType(str, enum.Enum):
    UPSELL = "UPSELL"
    CROSS_SELL = "CROSS_SELL"
    BUNDLE = "BUNDLE"
    SLOW_MOVING_PRODUCT = "SLOW_MOVING_PRODUCT"


class SupportingMetric(BaseModel):
    name: str = Field(..., description="Metric key identifier, e.g. co_purchase_count")
    value: Any = Field(..., description="Metric numerical or textual value")
    description: Optional[str] = Field(None, description="Human readable context of metric")


class Opportunity(BaseModel):
    id: str = Field(..., description="Unique opportunity identifier")
    type: OpportunityType = Field(..., description="Category of revenue opportunity")
    title: str = Field(..., description="Concise actionable title")
    description: str = Field(..., description="Detailed merchant-facing recommendation summary")
    primary_product_id: int = Field(..., description="Target or anchor product ID")
    primary_product_name: str = Field(..., description="Target product name")
    recommended_product_ids: List[int] = Field(default_factory=list, description="Recommended products to attach/upsell")
    recommended_product_names: List[str] = Field(default_factory=list, description="Names of recommended items")
    reasoning: str = Field(..., description="Strategic reasoning for the merchant")
    fact_statement: str = Field(..., description="Strictly database-derived factual data (FACT)")
    ai_interpretation: str = Field(..., description="AI reasoned growth hypothesis (AI INTERPRETATION)")
    supporting_metrics: Dict[str, Any] = Field(default_factory=dict, description="Deterministic metrics backing the opportunity")
    estimated_revenue_impact: float = Field(0.0, ge=0.0, description="Estimated gross revenue gain (INR)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    requires_merchant_approval: bool = Field(True, description="Safety flag ensuring bounded execution requires merchant consent")

    model_config = ConfigDict(from_attributes=True)


class AgentAnalysisResponse(BaseModel):
    merchant_id: int
    summary: str
    opportunities: List[Opportunity] = []
    proposals: List[ActionProposal] = []
    provider_used: str = Field("Deterministic Engine", description="LLM provider or fallback engine utilized")
    is_fallback_mode: bool = Field(False, description="Whether deterministic mock fallback mode was used")


class AgentChatRequest(BaseModel):
    merchant_id: int = Field(..., gt=0, description="Target Merchant ID")
    message: str = Field(..., min_length=1, description="Merchant user prompt or question")


class AgentChatResponse(BaseModel):
    response: str = Field(..., description="Conversational explanation and guidance for merchant")
    opportunities: List[Opportunity] = []
    proposals: List[ActionProposal] = []
    provider_used: str = Field("Deterministic Engine")
    is_fallback_mode: bool = False


class AgentSummaryMetrics(BaseModel):
    total_opportunities: int = 0
    high_confidence_count: int = 0
    potential_revenue_impact: float = 0.0
    pending_approvals_count: int = 0
    active_campaigns_count: int = 0
    provider_used: str = "Deterministic Engine"
    is_fallback_mode: bool = False
