"""Tests for Phase 4: Order Idempotency Handling."""
from starlette.testclient import TestClient


def test_duplicate_ai_order_idempotency(client: TestClient):
    m_res = client.post(
        "/api/v1/merchants",
        json={"name": "Idempotent Store", "email": "idem_test@sports.com", "currency": "INR"},
    )
    m_id = m_res.json()["id"]

    p_res = client.post(
        "/api/v1/products",
        json={
            "merchant_id": m_id,
            "name": "Limited Edition Sneaker",
            "category": "Footwear",
            "price": 5000.0,
            "stock_quantity": 10,
            "sku": "SNK-LIM-001",
        },
    )
    p_id = p_res.json()["id"]

    idempotency_key = "unique-buyer-request-key-9999"

    # First request
    res1 = client.post(
        "/api/v1/ai/orders",
        json={"merchant_id": m_id, "items": [{"product_id": p_id, "quantity": 1}]},
        headers={"Idempotency-Key": idempotency_key},
    )
    assert res1.status_code == 201
    order1 = res1.json()

    # Verify inventory was deducted from 10 to 9
    p_after_1 = client.get(f"/api/v1/ai/products/{p_id}").json()
    assert p_after_1["stock_quantity"] == 9

    # Duplicate second request with same Idempotency-Key
    res2 = client.post(
        "/api/v1/ai/orders",
        json={"merchant_id": m_id, "items": [{"product_id": p_id, "quantity": 1}]},
        headers={"Idempotency-Key": idempotency_key},
    )
    assert res2.status_code == 200 or res2.status_code == 201
    order2 = res2.json()

    # Must return identical order_id
    assert order1["order_id"] == order2["order_id"]
    assert order1["total_amount"] == order2["total_amount"]

    # Stock must NOT be deducted a second time
    p_after_2 = client.get(f"/api/v1/ai/products/{p_id}").json()
    assert p_after_2["stock_quantity"] == 9
