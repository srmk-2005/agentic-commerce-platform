"""Tests for Phase 3 Deterministic Safety Policy Validation."""
import pytest
from app.db.models import Customer, Merchant, MerchantAiPolicy, Product
from app.schemas.growth import ActionProposalCreate
from app.services.safety_service import SafetyService


def _setup_safety_env(db_session):
    m1 = Merchant(name="Store 1", email="m1@safety.com", currency="INR", is_active=True)
    m2 = Merchant(name="Store 2", email="m2@safety.com", currency="INR", is_active=True)
    db_session.add_all([m1, m2])
    db_session.flush()

    # Create policy with 20% max discount, 30 days max duration
    policy = MerchantAiPolicy(
        merchant_id=m1.id,
        max_discount_percentage=20.0,
        max_discount_amount=1000.0,
        max_campaign_duration_days=30,
        is_enabled=True,
    )
    db_session.add(policy)
    db_session.flush()

    # Active product in stock
    p1 = Product(merchant_id=m1.id, name="Running Shoes", category="Footwear", price=2500.0, stock_quantity=20, sku="SAF-01", is_active=True)
    # Inactive product
    p2 = Product(merchant_id=m1.id, name="Old Model Shoes", category="Footwear", price=2000.0, stock_quantity=10, sku="SAF-02", is_active=False)
    # Out-of-stock product
    p3 = Product(merchant_id=m1.id, name="Limited Socks", category="Accessories", price=300.0, stock_quantity=0, sku="SAF-03", is_active=True)
    # Product belonging to foreign merchant (m2)
    p_foreign = Product(merchant_id=m2.id, name="Foreign Item", category="Gear", price=500.0, stock_quantity=10, sku="SAF-FOR", is_active=True)

    db_session.add_all([p1, p2, p3, p_foreign])
    db_session.commit()

    return m1.id, m2.id, p1.id, p2.id, p3.id, p_foreign.id


def test_reject_discount_above_maximum(db_session):
    m1_id, _, p1_id, _, _, _ = _setup_safety_env(db_session)
    proposal = ActionProposalCreate(
        merchant_id=m1_id,
        action_type="CREATE_CAMPAIGN",
        title="Excessive Discount Promo",
        target_product_ids=[p1_id],
        discount_type="PERCENTAGE",
        discount_value=35.0,  # Limit is 20%
        campaign_duration_days=7,
    )
    res = SafetyService.validate_action_proposal(db_session, proposal)
    assert res.is_safe is False
    assert any("exceeds merchant maximum limit" in r for r in res.rejection_reasons)


def test_reject_negative_discount(db_session):
    m1_id, _, p1_id, _, _, _ = _setup_safety_env(db_session)
    proposal = ActionProposalCreate(
        merchant_id=m1_id,
        action_type="CREATE_CAMPAIGN",
        title="Negative Discount",
        target_product_ids=[p1_id],
        discount_type="PERCENTAGE",
        discount_value=-5.0,
        campaign_duration_days=7,
    )
    res = SafetyService.validate_action_proposal(db_session, proposal)
    assert res.is_safe is False
    assert any("cannot be negative" in r for r in res.rejection_reasons)


def test_reject_invalid_duration(db_session):
    m1_id, _, p1_id, _, _, _ = _setup_safety_env(db_session)
    # Exceeds max 30 days
    prop_long = ActionProposalCreate(
        merchant_id=m1_id,
        action_type="CREATE_CAMPAIGN",
        title="Year-Long Promo",
        target_product_ids=[p1_id],
        discount_type="PERCENTAGE",
        discount_value=10.0,
        campaign_duration_days=60,
    )
    res = SafetyService.validate_action_proposal(db_session, prop_long)
    assert res.is_safe is False
    assert any("exceeds maximum allowed duration" in r for r in res.rejection_reasons)


def test_reject_product_from_another_merchant(db_session):
    m1_id, _, p1_id, _, _, p_foreign_id = _setup_safety_env(db_session)
    proposal = ActionProposalCreate(
        merchant_id=m1_id,
        action_type="CREATE_BUNDLE",
        title="Cross Merchant Bundle",
        target_product_ids=[p1_id, p_foreign_id],
        discount_type="PERCENTAGE",
        discount_value=10.0,
        campaign_duration_days=7,
    )
    res = SafetyService.validate_action_proposal(db_session, proposal)
    assert res.is_safe is False
    assert any("do not belong to merchant" in r for r in res.rejection_reasons)


def test_reject_inactive_product(db_session):
    m1_id, _, _, p2_inactive_id, _, _ = _setup_safety_env(db_session)
    proposal = ActionProposalCreate(
        merchant_id=m1_id,
        action_type="CREATE_CAMPAIGN",
        title="Inactive Item Promo",
        target_product_ids=[p2_inactive_id],
        discount_type="PERCENTAGE",
        discount_value=10.0,
        campaign_duration_days=7,
    )
    res = SafetyService.validate_action_proposal(db_session, proposal)
    assert res.is_safe is False
    assert any("currently inactive" in r for r in res.rejection_reasons)


def test_reject_out_of_stock_product(db_session):
    m1_id, _, _, _, p3_out_of_stock_id, _ = _setup_safety_env(db_session)
    proposal = ActionProposalCreate(
        merchant_id=m1_id,
        action_type="CREATE_CAMPAIGN",
        title="Out of Stock Promo",
        target_product_ids=[p3_out_of_stock_id],
        discount_type="PERCENTAGE",
        discount_value=10.0,
        campaign_duration_days=7,
    )
    res = SafetyService.validate_action_proposal(db_session, proposal)
    assert res.is_safe is False
    assert any("zero available inventory" in r for r in res.rejection_reasons)


def test_valid_proposal_passes_safety_policy(db_session):
    m1_id, _, p1_id, _, _, _ = _setup_safety_env(db_session)
    proposal = ActionProposalCreate(
        merchant_id=m1_id,
        action_type="CREATE_CAMPAIGN",
        title="Valid 10% Promo",
        target_product_ids=[p1_id],
        discount_type="PERCENTAGE",
        discount_value=10.0,
        campaign_duration_days=7,
    )
    res = SafetyService.validate_action_proposal(db_session, proposal)
    assert res.is_safe is True
    assert len(res.rejection_reasons) == 0
