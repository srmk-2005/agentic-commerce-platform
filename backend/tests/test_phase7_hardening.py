"""Phase 7: System Hardening, Health Check, State Machine & Webhook Security Tests."""
import hashlib
import hmac
import pytest
from starlette.testclient import TestClient
from app.core.config import settings
from app.db.models import Order, OrderStatus


def test_system_health_check_endpoint(client: TestClient):
    """Verify GET /api/v1/health conforms to canonical Phase 7 schema."""
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()

    assert data["status"] in ["healthy", "degraded"]
    assert data["version"] == "1.0.0"
    assert "services" in data
    assert "database" in data["services"]
    assert "ai" in data["services"]
    assert "payments" in data["services"]
    assert "commerce" in data["services"]
    assert data["services"]["database"] == "healthy"
    assert data["services"]["payments"] == "healthy"


def test_demo_reset_endpoint(client: TestClient):
    """Verify POST /api/v1/demo/reset cleanly resets demo state."""
    res = client.post("/api/v1/demo/reset")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["status"] in ["ready", "degraded"]


def test_payment_proposal_rejects_cancelled_order(client: TestClient):
    """Verify attempting to propose payment on a cancelled order is rejected."""
    # 1. Create merchant
    m_res = client.post("/api/v1/merchants", json={"name": "Cancel Store", "email": "cancel@test.com"})
    m_id = m_res.json()["id"]

    # 2. Create product
    p_res = client.post(
        "/api/v1/products",
        json={"merchant_id": m_id, "name": "Item", "category": "Test", "price": 500.0, "stock_quantity": 10, "sku": "CNL-01"},
    )
    p_id = p_res.json()["id"]

    # 3. Create order
    ord_res = client.post(
        "/api/v1/ai/orders",
        json={"merchant_id": m_id, "items": [{"product_id": p_id, "quantity": 1}]},
    )
    ord_id = ord_res.json()["order_id"]

    # 4. Cancel order directly via PATCH
    patch_res = client.patch(f"/api/v1/orders/{ord_id}/status", json={"status": "CANCELLED"})
    assert patch_res.status_code == 200

    # 5. Attempt payment proposal on cancelled order
    prop_res = client.post(
        "/api/v1/ai/payments/propose",
        json={"merchant_id": m_id, "order_id": ord_id},
    )
    assert prop_res.status_code in [400, 422]
    assert "cancelled" in prop_res.json()["detail"].lower()


def test_webhook_signature_security(client: TestClient):
    """Verify webhook endpoint accepts valid HMAC signatures and rejects tampering."""
    payload = b'{"event": "payment.captured", "payload": {"payment": {"id": "pay_test_001"}}}'
    secret = settings.RAZORPAY_WEBHOOK_SECRET or settings.RAZORPAY_KEY_SECRET

    valid_sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    # Valid signature
    res_valid = client.post(
        "/api/v1/payments/webhook",
        content=payload,
        headers={"x-razorpay-signature": valid_sig, "content-type": "application/json"},
    )
    assert res_valid.status_code == 200
    assert res_valid.json()["status"] == "received"

    # Invalid signature
    res_invalid = client.post(
        "/api/v1/payments/webhook",
        content=payload,
        headers={"x-razorpay-signature": "tampered_signature_hex_12345", "content-type": "application/json"},
    )
    assert res_invalid.status_code == 400
    assert "invalid" in res_invalid.json()["detail"].lower()
