"""Pydantic schemas for Razorpay Test-Mode Payments and Bounded Money Actions."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.db.models import PaymentIntentStatus, PaymentStatus, RiskLevel


class PaymentPolicyCheck(BaseModel):
    is_allowed: bool
    amount: float
    currency: str = "INR"
    max_transaction_limit: float
    daily_limit: float
    today_spent: float
    remaining_daily_limit: float
    risk_level: str
    requires_approval: bool = True
    reasons: List[str] = Field(default_factory=list)
    explainability: str

    model_config = ConfigDict(from_attributes=True)


class PaymentIntentCreate(BaseModel):
    order_id: int = Field(..., gt=0)
    merchant_id: int = Field(default=1, gt=0)
    idempotency_key: Optional[str] = None


class PaymentIntentResponse(BaseModel):
    id: int
    order_id: int
    merchant_id: int
    amount: float
    currency: str
    status: str
    risk_level: str
    reason: str
    requires_approval: bool
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    idempotency_key: Optional[str] = None
    created_at: datetime
    explainability: Optional[str] = None
    policy_check: Optional[PaymentPolicyCheck] = None

    model_config = ConfigDict(from_attributes=True)


class PaymentApprovalRequest(BaseModel):
    reviewed_by: str = Field(default="Merchant Owner / User", min_length=1)
    reason: Optional[str] = Field(default="Explicit human authorization for AI payment request.")


class PaymentRejectionRequest(BaseModel):
    reviewed_by: str = Field(default="Merchant Owner / User", min_length=1)
    reason: str = Field(..., min_length=2)


class RazorpayOrderResponse(BaseModel):
    razorpay_order_id: str
    razorpay_key_id: str
    amount: int  # In smallest currency unit (paise)
    currency: str = "INR"
    payment_intent_id: int
    order_id: int
    status: str = "CREATED"
    is_test_mode: bool = True


class PaymentVerificationRequest(BaseModel):
    razorpay_order_id: str = Field(..., min_length=1)
    razorpay_payment_id: str = Field(..., min_length=1)
    razorpay_signature: str = Field(..., min_length=1)
    payment_intent_id: int = Field(..., gt=0)


class PaymentVerificationResponse(BaseModel):
    success: bool
    payment_id: int
    order_id: int
    status: str
    amount: float
    currency: str
    message: str
    verified_at: datetime


class PaymentResponse(BaseModel):
    id: int
    order_id: int
    merchant_id: int
    payment_intent_id: Optional[int] = None
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    amount: float
    currency: str
    status: str
    payment_method: str
    failure_reason: Optional[str] = None
    created_at: datetime
    verified_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class MoneyActionResponse(BaseModel):
    id: int
    merchant_id: int
    order_id: Optional[int] = None
    action_type: str
    amount: float
    currency: str
    status: str
    risk_level: str
    reason: str
    requires_approval: bool
    approved_by: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransactionDetailResponse(BaseModel):
    payment: PaymentResponse
    order: Dict[str, Any]
    payment_intent: Optional[PaymentIntentResponse] = None
    decision_chain: List[str] = Field(default_factory=list)
    audit_events: List[Dict[str, Any]] = Field(default_factory=list)
