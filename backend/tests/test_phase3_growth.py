"""Tests for Growth Action Proposals and Deterministic Financial Pricing."""
from app.db.models import Merchant, MerchantAiPolicy, Product
from app.schemas.growth import ActionProposalCreate
from app.services.growth_service import GrowthService


def _setup_growth_env(db_session):
    m = Merchant(name="Growth Store", email="growth@store.com", currency="INR", is_active=True)
    db_session.add(m)
    db_session.flush()

    policy = MerchantAiPolicy(merchant_id=m.id, is_enabled=True)
    db_session.add(policy)
    db_session.flush()

    p_shoes = Product(merchant_id=m.id, name="Running Shoes", category="Footwear", price=2499.0, stock_quantity=20, sku="GR-01", is_active=True)
    p_socks = Product(merchant_id=m.id, name="Running Socks", category="Accessories", price=299.0, stock_quantity=50, sku="GR-02", is_active=True)
    p_premium = Product(merchant_id=m.id, name="Carbon Pro Shoes", category="Footwear", price=4999.0, stock_quantity=10, sku="GR-03", is_active=True)
    p_bag = Product(merchant_id=m.id, name="Sports Bag", category="Accessories", price=1499.0, stock_quantity=30, sku="GR-04", is_active=True)
    db_session.add_all([p_shoes, p_socks, p_premium, p_bag])
    db_session.commit()

    return m.id, p_shoes.id, p_socks.id, p_premium.id, p_bag.id


def test_bundle_proposal_pricing_calculation(db_session):
    m_id, shoes_id, socks_id, _, _ = _setup_growth_env(db_session)

    # Bundle: Running Shoes (2499) + Running Socks (299) = Original 2798
    # 10% discount = 2798 * 0.90 = 2518.20
    proposal = ActionProposalCreate(
        merchant_id=m_id,
        action_type="CREATE_BUNDLE",
        title="Runner Combo",
        target_product_ids=[shoes_id, socks_id],
        primary_product_id=shoes_id,
        recommended_product_ids=[socks_id],
        discount_type="PERCENTAGE",
        discount_value=10.0,
        campaign_duration_days=7,
    )

    prop = GrowthService.propose_action(db_session, proposal)
    assert prop.original_bundle_price == 2798.0
    assert prop.discounted_bundle_price == 2518.20
    assert prop.safety_check.is_safe is True


def test_cross_sell_proposal_creation(db_session):
    m_id, shoes_id, socks_id, _, _ = _setup_growth_env(db_session)

    proposal = ActionProposalCreate(
        merchant_id=m_id,
        action_type="CREATE_OFFER",
        title="Shoes & Socks Cross-Sell",
        target_product_ids=[shoes_id, socks_id],
        primary_product_id=shoes_id,
        recommended_product_ids=[socks_id],
        discount_type="PERCENTAGE",
        discount_value=15.0,
        campaign_duration_days=14,
    )
    prop = GrowthService.propose_action(db_session, proposal)
    assert prop.id.startswith("prop-")
    assert prop.discount_value == 15.0


def test_upsell_proposal_creation(db_session):
    m_id, shoes_id, _, prem_id, _ = _setup_growth_env(db_session)

    proposal = ActionProposalCreate(
        merchant_id=m_id,
        action_type="CREATE_CAMPAIGN",
        campaign_type="UPSELL",
        title="Upgrade to Carbon Pro",
        target_product_ids=[shoes_id, prem_id],
        primary_product_id=shoes_id,
        recommended_product_ids=[prem_id],
        discount_type="PERCENTAGE",
        discount_value=5.0,
        campaign_duration_days=10,
    )
    prop = GrowthService.propose_action(db_session, proposal)
    assert prop.campaign_type == "UPSELL"
    assert prop.discount_value == 5.0


def test_slow_moving_promotion_creation(db_session):
    m_id, _, _, _, bag_id = _setup_growth_env(db_session)

    proposal = ActionProposalCreate(
        merchant_id=m_id,
        action_type="SLOW_MOVING_PROMOTION",
        campaign_type="SLOW_MOVING_PRODUCT",
        title="Sports Bag Liquidation Promotion",
        target_product_ids=[bag_id],
        primary_product_id=bag_id,
        discount_type="PERCENTAGE",
        discount_value=12.0,
        campaign_duration_days=7,
    )
    prop = GrowthService.propose_action(db_session, proposal)
    assert prop.campaign_type == "SLOW_MOVING_PRODUCT"
    assert prop.discount_value == 12.0
