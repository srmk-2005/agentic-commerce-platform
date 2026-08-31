"""Tests for Phase 4: Dynamic Inventory Failure Scenarios and Graceful Recovery."""
from starlette.testclient import TestClient


def test_insufficient_stock_failure_handling(client: TestClient):
    m_res = client.post(
        "/api/v1/merchants",
        json={"name": "Stock Fail Merchant", "email": "fail_test@sports.com", "currency": "INR"},
    )
    m_id = m_res.json()["id"]

    p_res = client.post(
        "/api/v1/products",
        json={
            "merchant_id": m_id,
            "name": "Single Stock Jersey",
            "category": "Apparel",
            "price": 1500.0,
            "stock_quantity": 1,
            "sku": "JRS-001",
        },
    )
    p_id = p_res.json()["id"]

    # Attempt to order 2 units when only 1 is available
    res = client.post(
        "/api/v1/ai/orders",
        json={"merchant_id": m_id, "items": [{"product_id": p_id, "quantity": 2}]},
    )
    assert res.status_code == 400
    assert "greater than available inventory" in res.json()["detail"]

    # Verify inventory is untouched
    p_check = client.get(f"/api/v1/ai/products/{p_id}").json()
    assert p_check["stock_quantity"] == 1


def test_simulate_order_out_of_stock_recovery(client: TestClient):
    m_res = client.post(
        "/api/v1/merchants",
        json={"name": "Buyer Sim Merchant", "email": "buyer_sim@sports.com", "currency": "INR"},
    )
    m_id = m_res.json()["id"]

    p_res = client.post(
        "/api/v1/products",
        json={
            "merchant_id": m_id,
            "name": "Sold Out Shoes",
            "category": "Running",
            "price": 3000.0,
            "stock_quantity": 0,
            "sku": "OUT-SH-001",
        },
    )
    p_id = p_res.json()["id"]

    res = client.post(
        "/api/v1/buyer/simulate-order",
        json={"merchant_id": m_id, "product_id": p_id, "quantity": 1},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is False
    assert "Insufficient stock" in data["error_message"]
    assert "Zero payments attempted" in data["explainability"]
