"""Tests for Phase 3 Failure Handling Simulation and Resilient Audit Logging."""
from app.db.models import AgentAction, AgentActionStatus, Approval, ApprovalStatus, Merchant, MerchantAiPolicy, Product
from app.schemas.growth import ActionProposalCreate
from app.services.growth_service import GrowthService


def test_simulated_failure_handling(client, db_session):
    m = Merchant(name="FailSafe Store", email="fail@store.com", currency="INR", is_active=True)
    db_session.add(m)
    db_session.flush()

    policy = MerchantAiPolicy(merchant_id=m.id, is_enabled=True)
    db_session.add(policy)
    db_session.flush()

    p = Product(merchant_id=m.id, name="Shoes", category="Footwear", price=1500.0, stock_quantity=20, sku="FAIL-01", is_active=True)
    db_session.add(p)
    db_session.commit()

    prop = GrowthService.propose_action(
        db_session,
        ActionProposalCreate(
            merchant_id=m.id,
            action_type="CREATE_CAMPAIGN",
            title="Promo To Fail",
            target_product_ids=[p.id],
            discount_type="PERCENTAGE",
            discount_value=10.0,
            campaign_duration_days=7,
        ),
    )

    # Call simulated failure endpoint
    res = client.post(f"/api/v1/approvals/{prop.approval_id}/simulate-failure")
    assert res.status_code == 500
    detail = res.json()["detail"]
    assert "Zero financial transactions attempted" in detail

    # Verify audit log captures failure
    logs_res = client.get(f"/api/v1/audit/logs?merchant_id={m.id}")
    assert logs_res.status_code == 200
    logs = logs_res.json()
    assert any(log["status"] == "FAILED" for log in logs)

    # Verify agent action recorded failure
    action = db_session.query(AgentAction).filter(AgentAction.id == prop.agent_action_id).first()
    assert action.status == AgentActionStatus.FAILED
