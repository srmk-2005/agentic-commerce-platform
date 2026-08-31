"""Tests for Phase 5: Security Boundaries, Role Isolation, and Failure Recovery."""
from starlette.testclient import TestClient
from app.payments.razorpay_service import razorpay_adapter


def _setup_sec_env(client: TestClient):
    m_res = client.post(
        "/api/v1/merchants",
        json={"name": "Sec Test Merchant", "email": "sec_test@sports.com", "currency": "INR"},
    )
    m_id = m_res.json()["id"]

    p = client.post(
        "/api/v1/products",
        json={"merchant_id": m_id, "name": "Sec Shoes", "category": "Footwear", "price": 1200.0, "stock_quantity": 10, "sku": "SEC-SH-01"},
    ).json()

    order = client.post(
        "/api/v1/ai/orders",
        json={"merchant_id": m_id, "items": [{"product_id": p["id"], "quantity": 1}]},
    ).json()

    return m_id, order["order_id"]


def test_cannot_execute_unapproved_payment(client: TestClient):
    m_id, order_id = _setup_sec_env(client)

    # 1. Propose payment
    prop = client.post(
        "/api/v1/ai/payments/propose",
        json={"merchant_id": m_id, "order_id": order_id},
    ).json()
    intent_id = prop["id"]

    # 2. Attempt direct execution without approval
    res = client.post(f"/api/v1/payments/create?payment_intent_id={intent_id}")
    assert res.status_code == 403
    assert "approved payment intent" in res.json()["detail"]


def test_idempotent_duplicate_verification(client: TestClient):
    m_id, order_id = _setup_sec_env(client)

    prop = client.post(
        "/api/v1/ai/payments/propose",
        json={"merchant_id": m_id, "order_id": order_id},
    ).json()

    appr = client.post(f"/api/v1/ai/payments/{prop['id']}/approve").json()
    rzp_order_id = appr["razorpay_order_id"]
    rzp_payment_id = "pay_idem_0011"
    sig = razorpay_adapter.generate_test_signature(rzp_order_id, rzp_payment_id)

    verify_req = {
        "payment_intent_id": prop["id"],
        "razorpay_order_id": rzp_order_id,
        "razorpay_payment_id": rzp_payment_id,
        "razorpay_signature": sig,
    }

    # 1st verification
    res1 = client.post("/api/v1/payments/verify", json=verify_req)
    assert res1.status_code == 200
    assert res1.json()["status"] == "CAPTURED"

    # 2nd duplicate verification -> must be idempotent success
    res2 = client.post("/api/v1/payments/verify", json=verify_req)
    assert res2.status_code == 200
    assert res2.json()["status"] == "CAPTURED"
    assert "already verified" in res2.json()["message"]


def test_simulated_payment_failure_does_not_mark_order_paid(client: TestClient):
    m_id, order_id = _setup_sec_env(client)

    prop = client.post(
        "/api/v1/ai/payments/propose",
        json={"merchant_id": m_id, "order_id": order_id},
    ).json()

    client.post(f"/api/v1/ai/payments/{prop['id']}/approve")

    # Simulate payment failure
    fail_res = client.post(
        f"/api/v1/payments/simulate-failure?payment_intent_id={prop['id']}&failure_reason=Simulated%20Bank%20Decline"
    )
    assert fail_res.status_code == 200
    assert fail_res.json()["status"] == "FAILED"

    # Verify order is PAYMENT_FAILED, NOT marked PAID
    order_check = client.get(f"/api/v1/orders/{order_id}").json()
    assert order_check["status"] == "PAYMENT_FAILED"
