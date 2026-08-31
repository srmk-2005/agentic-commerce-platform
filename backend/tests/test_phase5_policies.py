"""Tests for Phase 5: Deterministic Payment Policy & Safety Verification Engine."""
from starlette.testclient import TestClient


def _setup_policy_merchant(client: TestClient, max_tx=5000.0, daily_limit=25000.0, allow_ai=True):
    m_res = client.post(
        "/api/v1/merchants",
        json={"name": "Policy Merchant Store", "email": "policy_test@sports.com", "currency": "INR"},
    )
    m_id = m_res.json()["id"]

    # Products
    p1 = client.post(
        "/api/v1/products",
        json={"merchant_id": m_id, "name": "Standard Shoes", "category": "Footwear", "price": 2499.0, "stock_quantity": 20, "sku": "POL-SH-01"},
    ).json()

    p_expensive = client.post(
        "/api/v1/products",
        json={"merchant_id": m_id, "name": "Luxury Carbon Shoes", "category": "Footwear", "price": 8000.0, "stock_quantity": 10, "sku": "POL-LUX-02"},
    ).json()

    return m_id, p1["id"], p_expensive["id"]


def test_payment_policy_allows_within_bounds(client: TestClient):
    m_id, p1_id, _ = _setup_policy_merchant(client)

    # 1. Create order for ₹2,499 (limit is ₹5,000)
    order_res = client.post(
        "/api/v1/ai/orders",
        json={"merchant_id": m_id, "items": [{"product_id": p1_id, "quantity": 1}]},
    )
    assert order_res.status_code == 201
    order_id = order_res.json()["order_id"]

    # 2. Propose payment intent
    prop_res = client.post(
        "/api/v1/ai/payments/propose",
        json={"merchant_id": m_id, "order_id": order_id},
    )
    assert prop_res.status_code == 201
    data = prop_res.json()

    assert data["order_id"] == order_id
    assert data["amount"] == 2499.0
    assert data["currency"] == "INR"
    assert data["status"] == "PENDING_APPROVAL"
    assert data["risk_level"] in ["LOW", "MEDIUM"]
    assert data["requires_approval"] is True
    assert "within the configured single-transaction limit" in data["explainability"]


def test_payment_policy_blocks_amount_exceeding_transaction_limit(client: TestClient):
    m_id, _, p_lux_id = _setup_policy_merchant(client, max_tx=5000.0)

    # 1. Create order for ₹8,000 (exceeds ₹5,000 max limit)
    order_res = client.post(
        "/api/v1/ai/orders",
        json={"merchant_id": m_id, "items": [{"product_id": p_lux_id, "quantity": 1}]},
    )
    assert order_res.status_code == 201
    order_id = order_res.json()["order_id"]

    # 2. Propose payment intent -> Must be blocked
    prop_res = client.post(
        "/api/v1/ai/payments/propose",
        json={"merchant_id": m_id, "order_id": order_id},
    )
    assert prop_res.status_code == 400
    err_detail = prop_res.json()["detail"]
    assert "exceeds maximum allowed AI transaction limit" in err_detail
