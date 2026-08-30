"""Tests for Phase 3 Idempotent Execution and Duplicate Safety."""
from app.db.models import Campaign, Merchant, MerchantAiPolicy, Product
from app.schemas.growth import ActionProposalCreate
from app.services.growth_service import GrowthService


def test_idempotent_duplicate_approvals(db_session):
    m = Merchant(name="Idempotent Store", email="idem@store.com", currency="INR", is_active=True)
    db_session.add(m)
    db_session.flush()

    policy = MerchantAiPolicy(merchant_id=m.id, is_enabled=True)
    db_session.add(policy)
    db_session.flush()

    p = Product(merchant_id=m.id, name="Shoes", category="Footwear", price=1500.0, stock_quantity=10, sku="IDEM-01", is_active=True)
    db_session.add(p)
    db_session.commit()

    prop = GrowthService.propose_action(
        db_session,
        ActionProposalCreate(
            merchant_id=m.id,
            action_type="CREATE_CAMPAIGN",
            title="Idempotent Promo",
            target_product_ids=[p.id],
            discount_type="PERCENTAGE",
            discount_value=10.0,
            campaign_duration_days=7,
        ),
    )

    # First approval -> creates campaign
    res1 = GrowthService.approve_action(db_session, prop.approval_id, reviewed_by="Admin")
    camp1_id = res1["campaign_id"]
    assert res1["is_duplicate"] is False

    # Second approval (rapid duplicate click) -> returns existing campaign
    res2 = GrowthService.approve_action(db_session, prop.approval_id, reviewed_by="Admin")
    assert res2["campaign_id"] == camp1_id
    assert res2["is_duplicate"] is True

    # Total campaigns in DB should be exactly 1
    total_camps = db_session.query(Campaign).filter(Campaign.merchant_id == m.id).count()
    assert total_camps == 1
