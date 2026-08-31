"""Tests for Phase 4: AI Commerce Order Creation & Safety Guardrails."""
from starlette.testclient import TestClient


def _setup_order_env(client: TestClient):
    m_res = client.post(
        "/api/v1/merchants",
        json={"name": "Order Test Merchant", "email": "ord_test@sports.com", "currency": "INR"},
    )
    m_id = m_res.json()["id"]

    p1 = client.post(
        "/api/v1/products",
        json={
            "merchant_id": m_id,
            "name": "Road Runner Pro",
            "category": "Running",
            "price": 2999.0,
            "stock_quantity": 10,
            "sku": "ORD-SH-001",
        },
    ).json()

    p2 = client.post(
        "/api/v1/products",
        json={
            "merchant_id": m_id,
            "name": "Sports Water Bottle",
            "category": "Accessories",
            "price": 499.0,
            "stock_quantity": 2,
            "sku": "ORD-BOT-002",
        },
    ).json()

    # Another merchant's product
    m2_res = client.post(
        "/api/v1/merchants",
        json={"name": "Rival Store", "email": "rival@sports.com", "currency": "INR"},
    )
    m2_id = m2_res.json()["id"]
    p_rival = client.post(
        "/api/v1/products",
        json={
            "merchant_id": m2_id,
            "name": "Rival Product",
            "category": "Gear",
            "price": 1200.0,
            "stock_quantity": 10,
            "sku": "RIV-001",
        },
    ).json()

    return m_id, p1["id"], p2["id"], p_rival["id"]


def test_ai_order_creation_and_price_calculation(client: TestClient):
    m_id, p1_id, p2_id, _ = _setup_order_env(client)

    # Place order for 2x p1 (₹2999 each) and 1x p2 (₹499 each)
    order_req = {
        "merchant_id": m_id,
        "items": [
            {"product_id": p1_id, "quantity": 2},
            {"product_id": p2_id, "quantity": 1},
        ],
    }

    res = client.post("/api/v1/ai/orders", json=order_req)
    assert res.status_code == 201
    order = res.json()

    assert order["merchant_id"] == m_id
    assert order["status"] == "PENDING"
    assert order["payment_status"] == "NOT_AVAILABLE"

    # Server calculates 2 * 2999 + 1 * 499 = 5998 + 499 = 6497
    assert order["total_amount"] == 6497.0

    # Verify inventory was automatically deducted
    p1_check = client.get(f"/api/v1/ai/products/{p1_id}").json()
    assert p1_check["stock_quantity"] == 8  # 10 - 2

    p2_check = client.get(f"/api/v1/ai/products/{p2_id}").json()
    assert p2_check["stock_quantity"] == 1  # 2 - 1


def test_ai_order_rejects_foreign_merchant_product(client: TestClient):
    m_id, p1_id, _, p_rival_id = _setup_order_env(client)

    order_req = {
        "merchant_id": m_id,
        "items": [{"product_id": p_rival_id, "quantity": 1}],
    }

    res = client.post("/api/v1/ai/orders", json=order_req)
    assert res.status_code == 400
    assert "does not belong to merchant" in res.json()["detail"]


def test_ai_order_rejects_exceeding_purchase_constraint_limit(client: TestClient):
    m_id, p1_id, _, _ = _setup_order_env(client)

    # Attempt to order 8 units (max limit is 5)
    order_req = {
        "merchant_id": m_id,
        "items": [{"product_id": p1_id, "quantity": 8}],
    }

    res = client.post("/api/v1/ai/orders", json=order_req)
    assert res.status_code == 400
    assert "exceeds maximum limit" in res.json()["detail"]
