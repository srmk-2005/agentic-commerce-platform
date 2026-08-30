"""Tests for Phase 3 Merchant Approval and Rejection Workflows."""
from fastapi import HTTPException
import pytest
from app.db.models import (
    Approval,
    ApprovalStatus,
    Campaign,
    CampaignStatus,
    Merchant,
    MerchantAiPolicy,
    Offer,
    Product,
)
from app.schemas.growth import ActionProposalCreate
from app.services.growth_service import GrowthService


def _setup_approval_env(db_session):
    m = Merchant(name="Approval Store", email="m@approval.com", currency="INR", is_active=True)
    db_session.add(m)
    db_session.flush()

    policy = MerchantAiPolicy(
        merchant_id=m.id,
        max_discount_percentage=20.0,
        max_discount_amount=1000.0,
        max_campaign_duration_days=30,
        is_enabled=True,
    )
    db_session.add(policy)
    db_session.flush()

    p1 = Product(merchant_id=m.id, name="Shoes", category="Footwear", price=2000.0, stock_quantity=15, sku="APP-01", is_active=True)
    p2 = Product(merchant_id=m.id, name="Socks", category="Accessories", price=200.0, stock_quantity=40, sku="APP-02", is_active=True)
    db_session.add_all([p1, p2])
    db_session.commit()

    return m.id, p1.id, p2.id


def test_create_and_approve_action(db_session):
    m_id, p1_id, p2_id = _setup_approval_env(db_session)

    proposal = ActionProposalCreate(
        merchant_id=m_id,
        action_type="CREATE_BUNDLE",
        title="Runner Combo",
        target_product_ids=[p1_id, p2_id],
        primary_product_id=p1_id,
        recommended_product_ids=[p2_id],
        discount_type="PERCENTAGE",
        discount_value=10.0,
        campaign_duration_days=7,
    )

    created_prop = GrowthService.propose_action(db_session, proposal)
    assert created_prop.approval_id is not None

    approval = db_session.query(Approval).filter(Approval.id == created_prop.approval_id).first()
    assert approval.status == ApprovalStatus.PENDING

    # Merchant approves
    exec_res = GrowthService.approve_action(db_session, approval.id, reviewed_by="Store Owner")
    assert exec_res["status"] == "ACTIVE"
    assert exec_res["campaign_id"] is not None

    # Check Campaign in DB
    camp = db_session.query(Campaign).filter(Campaign.id == exec_res["campaign_id"]).first()
    assert camp.status == CampaignStatus.ACTIVE
    assert len(camp.products) == 2

    # Check Offer in DB
    offer = db_session.query(Offer).filter(Offer.campaign_id == camp.id).first()
    assert offer is not None
    assert offer.discount_value == 10.0


def test_reject_action_workflow(db_session):
    m_id, p1_id, p2_id = _setup_approval_env(db_session)

    proposal = ActionProposalCreate(
        merchant_id=m_id,
        action_type="CREATE_CAMPAIGN",
        title="Rejected Promo",
        target_product_ids=[p1_id],
        discount_type="PERCENTAGE",
        discount_value=15.0,
        campaign_duration_days=5,
    )

    prop = GrowthService.propose_action(db_session, proposal)
    rej_res = GrowthService.reject_action(db_session, prop.approval_id, reason="Do not discount this product.", reviewed_by="Store Owner")
    assert rej_res["status"] == "REJECTED"
    assert rej_res["reason"] == "Do not discount this product."

    # Verify cannot approve a rejected action
    with pytest.raises(HTTPException) as exc_info:
        GrowthService.approve_action(db_session, prop.approval_id, reviewed_by="Store Owner")
    assert exc_info.value.status_code == 400
    assert "REJECTED" in exc_info.value.detail


def test_revalidation_catches_pre_execution_stock_out(db_session):
    m_id, p1_id, p2_id = _setup_approval_env(db_session)

    proposal = ActionProposalCreate(
        merchant_id=m_id,
        action_type="CREATE_CAMPAIGN",
        title="Valid Promo Initially",
        target_product_ids=[p1_id],
        discount_type="PERCENTAGE",
        discount_value=10.0,
        campaign_duration_days=7,
    )
    prop = GrowthService.propose_action(db_session, proposal)

    # Simulate stock running out before merchant clicks Approve
    product = db_session.query(Product).filter(Product.id == p1_id).first()
    product.stock_quantity = 0
    db_session.commit()

    # Re-validation must reject the approval
    with pytest.raises(HTTPException) as exc_info:
        GrowthService.approve_action(db_session, prop.approval_id)
    assert exc_info.value.status_code == 400
    assert "zero available inventory" in exc_info.value.detail

    # Check approval marked REJECTED
    approval = db_session.query(Approval).filter(Approval.id == prop.approval_id).first()
    assert approval.status == ApprovalStatus.REJECTED
