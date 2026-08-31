"""Standardized Merchant Discovery and Capability Negotiation."""
from typing import Optional
from sqlalchemy.orm import Session
from app.agent_commerce.protocol import SUPPORTED_ACTIONS, SUPPORTED_PROTOCOL_VERSION
from app.agent_commerce.schemas import AgentCommerceContract
from app.db.models import Merchant, MerchantAiPolicy


def get_merchant_contract(db: Session, merchant_id: int) -> Optional[AgentCommerceContract]:
    """Generate standardized, machine-readable AgentCommerceContract."""
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not merchant:
        return None

    policy = db.query(MerchantAiPolicy).filter(MerchantAiPolicy.merchant_id == merchant_id).first()
    
    max_tx = policy.max_ai_transaction_amount if policy else 5000.0
    daily_limit = policy.daily_ai_transaction_limit if policy else 25000.0
    approval_req = policy.require_payment_approval if policy else True
    allow_pay = policy.allow_ai_payment if policy else True

    capabilities = {
        "catalog": True,
        "search": True,
        "inventory": True,
        "orders": True,
        "payments": allow_pay,
        "refunds": False,
        "capability_negotiation": True,
    }

    endpoints = {
        "sessions": "/api/v1/agent-commerce/sessions",
        "message": "/api/v1/agent-commerce/message",
        "catalog": "/api/v1/ai/catalog",
        "search": "/api/v1/ai/search",
        "orders": "/api/v1/ai/orders",
        "payments": "/api/v1/ai/payments/propose",
        "timeline": f"/api/v1/agent-commerce/sessions/{{session_id}}/timeline",
    }

    payment_policy = {
        "approval_required": approval_req,
        "max_ai_transaction_amount": max_tx,
        "daily_ai_transaction_limit": daily_limit,
        "allow_ai_payment": allow_pay,
        "currency": merchant.currency,
        "test_mode": True,
    }

    return AgentCommerceContract(
        protocol_version=SUPPORTED_PROTOCOL_VERSION,
        merchant_id=merchant.id,
        merchant_name=merchant.name,
        currency=merchant.currency,
        capabilities=capabilities,
        endpoints=endpoints,
        payment_policy=payment_policy,
        supported_actions=SUPPORTED_ACTIONS,
    )
