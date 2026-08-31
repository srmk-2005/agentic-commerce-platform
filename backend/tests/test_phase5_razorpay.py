"""Tests for Phase 5: Razorpay Test-Mode Orders and HMAC Signature Verification."""
from starlette.testclient import TestClient
from app.payments.razorpay_service import razorpay_adapter


def _setup_razorpay_env(client: TestClient):
    m_res = client.post(
        "/api/v1/merchants",
        json={"name": "Razorpay Test Merchant", "email": "rzp_test@sports.com", "currency": "INR"},
    )
    m_id = m_res.json()["id"]

    p = client.post(
        "/api/v1/products",
        json={"merchant_id": m_id, "name": "Speed Shoes", "category": "Footwear", "price": 1500.0, "stock_quantity": 10, "sku": "RZP-SH-01"},
    ).json()

    order = client.post(
        "/api/v1/ai/orders",
        json={"merchant_id": m_id, "items": [{"product_id": p["id"], "quantity": 1}]},
    ).json()

    prop = client.post(
        "/api/v1/ai/payments/propose",
        json={"merchant_id": m_id, "order_id": order["order_id"]},
    ).json()

    appr = client.post(f"/api/v1/ai/payments/{prop['id']}/approve").json()

    return prop["id"], order["order_id"], appr["razorpay_order_id"]


def test_razorpay_signature_verification_success(client: TestClient):
    intent_id, order_id, rzp_order_id = _setup_razorpay_env(client)
    rzp_payment_id = "pay_test_99887766"

    # Generate valid HMAC signature
    valid_signature = razorpay_adapter.generate_test_signature(rzp_order_id, rzp_payment_id)

    verify_req = {
        "payment_intent_id": intent_id,
        "razorpay_order_id": rzp_order_id,
        "razorpay_payment_id": rzp_payment_id,
        "razorpay_signature": valid_signature,
    }

    res = client.post("/api/v1/payments/verify", json=verify_req)
    assert res.status_code == 200
    data = res.json()

    assert data["success"] is True
    assert data["status"] == "CAPTURED"
    assert data["order_id"] == order_id

    # Check order is marked as PAID
    order_check = client.get(f"/api/v1/orders/{order_id}").json()
    assert order_check["status"] == "PAID"


def test_razorpay_invalid_signature_rejected(client: TestClient):
    intent_id, order_id, rzp_order_id = _setup_razorpay_env(client)
    rzp_payment_id = "pay_test_invalid_001"

    verify_req = {
        "payment_intent_id": intent_id,
        "razorpay_order_id": rzp_order_id,
        "razorpay_payment_id": rzp_payment_id,
        "razorpay_signature": "invalid_forged_signature_hex",
    }

    res = client.post("/api/v1/payments/verify", json=verify_req)
    assert res.status_code == 400
    assert "signature verification failed" in res.json()["detail"].lower()
