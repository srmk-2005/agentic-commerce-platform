"""Unit tests for Phase 6 Discovery & Capability Negotiation."""
import pytest
from sqlalchemy.orm import Session
from app.agent_commerce.discovery import get_merchant_contract
from app.db.models import Merchant, MerchantAiPolicy


def test_merchant_discovery_contract(db: Session, sample_merchant: Merchant):
    """Test generating standardized discovery contract."""
    contract = get_merchant_contract(db, sample_merchant.id)
    assert contract is not None
    assert contract.protocol_version == "1.0"
    assert contract.merchant_id == sample_merchant.id
    assert contract.merchant_name == sample_merchant.name
    assert contract.capabilities["catalog"] is True
    assert contract.capabilities["search"] is True
    assert contract.capabilities["inventory"] is True
    assert contract.capabilities["orders"] is True
    assert contract.capabilities["payments"] is True
    assert contract.capabilities["refunds"] is False
    assert "sessions" in contract.endpoints
    assert "message" in contract.endpoints
    assert "SEARCH" in contract.supported_actions


def test_discovery_policy_bounds(db: Session, sample_merchant: Merchant):
    """Test contract reflects merchant payment policy bounds."""
    policy = db.query(MerchantAiPolicy).filter(MerchantAiPolicy.merchant_id == sample_merchant.id).first()
    if not policy:
        policy = MerchantAiPolicy(
            merchant_id=sample_merchant.id,
            max_ai_transaction_amount=7500.0,
            daily_ai_transaction_limit=35000.0,
            require_payment_approval=True,
            allow_ai_payment=True,
        )
        db.add(policy)
        db.commit()
    else:
        policy.max_ai_transaction_amount = 7500.0
        policy.daily_ai_transaction_limit = 35000.0
        db.commit()

    contract = get_merchant_contract(db, sample_merchant.id)
    assert contract.payment_policy["max_ai_transaction_amount"] == 7500.0
    assert contract.payment_policy["daily_ai_transaction_limit"] == 35000.0
    assert contract.payment_policy["approval_required"] is True


def test_discovery_nonexistent_merchant(db: Session):
    """Test discovering nonexistent merchant returns None."""
    contract = get_merchant_contract(db, 999999)
    assert contract is None
