"""Standardized Pydantic Schemas for Agent Commerce Protocol Layer."""
import enum
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ProtocolAction(str, enum.Enum):
    DISCOVER = "DISCOVER"
    SEARCH = "SEARCH"
    GET_PRODUCT = "GET_PRODUCT"
    CHECK_INVENTORY = "CHECK_INVENTORY"
    CREATE_ORDER = "CREATE_ORDER"
    PROPOSE_PAYMENT = "PROPOSE_PAYMENT"
    GET_PAYMENT_STATUS = "GET_PAYMENT_STATUS"


class AgentSenderRecipient(BaseModel):
    type: str = Field(..., description="Entity type: AI_BUYER, MERCHANT, or SYSTEM")
    id: str = Field(..., description="Unique identifier of agent or merchant")


class AgentMessage(BaseModel):
    protocol_version: str = Field(default="1.0", description="Protocol version must be '1.0'")
    message_id: str = Field(..., description="Unique message identifier")
    session_id: str = Field(..., description="Commerce session identifier (e.g. acs_...)")
    trace_id: Optional[str] = Field(default=None, description="End-to-end transaction trace identifier")
    sender: AgentSenderRecipient
    recipient: AgentSenderRecipient
    action: ProtocolAction
    payload: Dict[str, Any] = Field(default_factory=dict)


class AgentError(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    success: bool
    protocol_version: str = "1.0"
    message_id: str
    session_id: str
    trace_id: str
    action: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[AgentError] = None


class AgentCommerceContract(BaseModel):
    protocol_version: str = "1.0"
    merchant_id: int
    merchant_name: str
    currency: str = "INR"
    capabilities: Dict[str, bool]
    endpoints: Dict[str, str]
    payment_policy: Dict[str, Any]
    supported_actions: List[str]

    model_config = ConfigDict(from_attributes=True)


class SessionCreateRequest(BaseModel):
    merchant_id: int = Field(default=1, gt=0)
    buyer_id: str = Field(default="demo_ai_buyer", min_length=1)


class SessionResponse(BaseModel):
    session_id: str
    trace_id: str
    merchant_id: int
    buyer_id: str
    status: str
    created_at: datetime
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SessionTimelineEvent(BaseModel):
    timestamp: str
    action: str
    actor: str
    status: str
    details: Dict[str, Any] = Field(default_factory=dict)


class SessionTimelineResponse(BaseModel):
    session_id: str
    trace_id: str
    status: str
    merchant_id: int
    buyer_id: str
    timeline: List[SessionTimelineEvent] = Field(default_factory=list)


class CommerceReadinessScoreItem(BaseModel):
    category: str
    name: str
    weight: int
    passed: bool
    details: str


class CommerceReadinessResponse(BaseModel):
    merchant_id: int
    merchant_name: str
    readiness_score: int  # 0 to 100
    is_ready: bool
    checklist: List[CommerceReadinessScoreItem]
    recommendations: List[str] = Field(default_factory=list)


class AgentCommerceStatsResponse(BaseModel):
    active_sessions: int
    orders_via_ai: int
    ai_revenue: float
    successful_payments: int
    blocked_transactions: int
    currency: str = "INR"
