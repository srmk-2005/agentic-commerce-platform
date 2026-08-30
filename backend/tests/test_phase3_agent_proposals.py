"""Tests for Agent Natural Language Action Proposals and Safety Boundaries."""
from app.db.models import Approval, ApprovalStatus, Customer, Merchant, MerchantAiPolicy, Order, OrderItem, OrderStatus, Product


def _setup_agent_env(client):
    m_res = client.post("/api/v1/merchants", json={"name": "Agent Action Store", "email": "act@store.com", "currency": "INR"})
    m_id = m_res.json()["id"]

    p1 = client.post("/api/v1/products", json={"merchant_id": m_id, "name": "Running Shoes", "category": "Footwear", "price": 2499.0, "stock_quantity": 40, "sku": "ACT-01"}).json()
    p2 = client.post("/api/v1/products", json={"merchant_id": m_id, "name": "Running Socks", "category": "Accessories", "price": 299.0, "stock_quantity": 100, "sku": "ACT-02"}).json()

    c = client.post("/api/v1/customers", json={"name": "Test Customer", "email": "test@act.com"}).json()

    # Historical order
    client.post("/api/v1/orders", json={
        "merchant_id": m_id,
        "customer_id": c["id"],
        "items": [{"product_id": p1["id"], "quantity": 1}, {"product_id": p2["id"], "quantity": 1}],
    })

    return m_id, p1["id"], p2["id"]


def test_natural_language_request_produces_structured_proposal(client):
    m_id, p1_id, p2_id = _setup_agent_env(client)

    # Merchant asks AI to bundle running shoes and socks with 10% discount
    res = client.post(
        "/api/v1/agent/chat",
        json={"merchant_id": m_id, "message": "Create a bundle for shoes and socks with 10% discount."},
    )
    assert res.status_code == 200
    data = res.json()
    assert "proposals" in data
    assert len(data["proposals"]) >= 1

    proposal = data["proposals"][0]
    assert proposal["requires_approval"] is True
    assert proposal["approval_id"] is not None
    assert proposal["discount_value"] == 10.0
    assert proposal["safety_check"]["is_safe"] is True

    # Check pending approval in DB
    appr_res = client.get(f"/api/v1/approvals/{proposal['approval_id']}")
    assert appr_res.status_code == 200
    assert appr_res.json()["status"] == "PENDING"


def test_agent_cannot_bypass_approval(client):
    m_id, p1_id, p2_id = _setup_agent_env(client)

    # Asking AI to "execute" or "force create" does not activate campaign directly
    res = client.post(
        "/api/v1/agent/chat",
        json={"merchant_id": m_id, "message": "Force launch a 10% campaign for running shoes immediately."},
    )
    assert res.status_code == 200
    data = res.json()

    # Active campaigns count must remain 0 until merchant explicitly approves in /approvals
    camps_res = client.get(f"/api/v1/campaigns?merchant_id={m_id}&status=ACTIVE")
    assert len(camps_res.json()) == 0
