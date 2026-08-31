"""Phase 7: Comprehensive End-to-End Integration Test Suite.

Verifies complete commerce lifecycle:
Merchant Creation -> AI Session -> Discovery -> Search -> Stock Check ->
Create Order -> Propose Payment -> Policy Check -> Human Approval ->
Razorpay Test Payment -> HMAC Verification -> Order Confirmation -> Audit Trail.
"""
import hashlib
import hmac
import pytest
from starlette.testclient import TestClient
from app.core.config import settings


def test_complete_e2e_agent_commerce_lifecycle(client: TestClient):
    """Full end-to-end integration test validating all 6 phases working in harmony."""
    # 1. Create Merchant
    m_res = client.post(
        "/api/v1/merchants",
        json={
            "name": "Integration Superstore",
            "email": "integration_master@store.com",
            "description": "Full lifecycle testing store",
            "currency": "INR",
        },
    )
    assert m_res.status_code == 201
    m_id = m_res.json()["id"]

    # 2. Create Products
    p_res = client.post(
        "/api/v1/products",
        json={
            "merchant_id": m_id,
            "name": "Pro Marathon Shoes",
            "category": "Footwear",
            "price": 2499.0,
            "stock_quantity": 25,
            "sku": "PRO-RUN-01",
        },
    )
    assert p_res.status_code == 201
    p_id = p_res.json()["id"]

    # 3. Create Customer
    c_res = client.post(
        "/api/v1/customers",
        json={
            "name": "AI Agent Customer",
            "email": "buyer_ai@agent.com",
        },
    )
    assert c_res.status_code == 201
    c_id = c_res.json()["id"]

    # 4. Initialize Stateful Agent Session
    sess_res = client.post(
        "/api/v1/agent-commerce/sessions",
        json={"merchant_id": m_id, "buyer_id": "integration_ai_buyer"},
    )
    assert sess_res.status_code == 201
    session_id = sess_res.json()["session_id"]
    trace_id = sess_res.json()["trace_id"]

    # 5. Discover Merchant Capabilities
    disc_res = client.post(
        "/api/v1/agent-commerce/message",
        json={
            "protocol_version": "1.0",
            "message_id": f"msg_disc_{session_id}",
            "session_id": session_id,
            "trace_id": trace_id,
            "sender": {"type": "AI_BUYER", "id": "integration_ai_buyer"},
            "recipient": {"type": "MERCHANT", "id": str(m_id)},
            "action": "DISCOVER",
        },
    )
    assert disc_res.status_code == 200
    disc_data = disc_res.json()
    assert disc_data["success"] is True
    assert disc_data["data"]["capabilities"]["orders"] is True
    assert disc_data["data"]["capabilities"]["payments"] is True

    # 6. Ranked Multi-Factor Catalog Search
    search_res = client.post(
        "/api/v1/agent-commerce/message",
        json={
            "protocol_version": "1.0",
            "message_id": f"msg_search_{session_id}",
            "session_id": session_id,
            "trace_id": trace_id,
            "sender": {"type": "AI_BUYER", "id": "integration_ai_buyer"},
            "recipient": {"type": "MERCHANT", "id": str(m_id)},
            "action": "SEARCH",
            "payload": {"query": "Marathon", "max_price": 3000.0},
        },
    )
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert search_data["success"] is True
    assert len(search_data["data"]["products"]) >= 1

    # 7. Check Inventory Real-Time
    inv_res = client.post(
        "/api/v1/agent-commerce/message",
        json={
            "protocol_version": "1.0",
            "message_id": f"msg_inv_{session_id}",
            "session_id": session_id,
            "trace_id": trace_id,
            "sender": {"type": "AI_BUYER", "id": "integration_ai_buyer"},
            "recipient": {"type": "MERCHANT", "id": str(m_id)},
            "action": "CHECK_INVENTORY",
            "payload": {"product_id": p_id, "quantity": 1},
        },
    )
    assert inv_res.status_code == 200
    assert inv_res.json()["data"]["in_stock"] is True

    # 8. Create Server-Side Order
    ord_res = client.post(
        "/api/v1/agent-commerce/message",
        json={
            "protocol_version": "1.0",
            "message_id": f"msg_ord_{session_id}",
            "session_id": session_id,
            "trace_id": trace_id,
            "sender": {"type": "AI_BUYER", "id": "integration_ai_buyer"},
            "recipient": {"type": "MERCHANT", "id": str(m_id)},
            "action": "CREATE_ORDER",
            "payload": {"product_id": p_id, "quantity": 1, "idempotency_key": f"e2e-ord-{session_id}"},
        },
    )
    assert ord_res.status_code == 200
    order_id = ord_res.json()["data"]["order_id"]
    assert order_id is not None

    # 9. Propose Payment Intent to Policy Engine
    prop_res = client.post(
        "/api/v1/agent-commerce/message",
        json={
            "protocol_version": "1.0",
            "message_id": f"msg_pay_{session_id}",
            "session_id": session_id,
            "trace_id": trace_id,
            "sender": {"type": "AI_BUYER", "id": "integration_ai_buyer"},
            "recipient": {"type": "MERCHANT", "id": str(m_id)},
            "action": "PROPOSE_PAYMENT",
            "payload": {"order_id": order_id},
        },
    )
    assert prop_res.status_code == 200
    intent_data = prop_res.json()["data"]
    intent_id = intent_data["id"]
    assert intent_data["amount"] == 2499.0
    assert intent_data["requires_approval"] is True

    # 10. Human Approval Gate
    appr_res = client.post(
        f"/api/v1/ai/payments/{intent_id}/approve",
        json={"reviewed_by": "Integration Tester", "reason": "Authorized via E2E Integration Suite"},
    )
    assert appr_res.status_code == 200
    rzp_data = appr_res.json()
    rzp_order_id = rzp_data["razorpay_order_id"]
    assert rzp_order_id.startswith("order_test_")

    # 11. Generate Cryptographic Signature & Verify
    mock_pay_id = f"pay_test_{session_id}"
    secret = settings.RAZORPAY_KEY_SECRET
    msg_bytes = f"{rzp_order_id}|{mock_pay_id}".encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), msg_bytes, hashlib.sha256).hexdigest()

    verify_res = client.post(
        "/api/v1/payments/verify",
        json={
            "razorpay_order_id": rzp_order_id,
            "razorpay_payment_id": mock_pay_id,
            "razorpay_signature": sig,
            "payment_intent_id": intent_id,
        },
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["status"] == "CAPTURED"

    # 12. Check Final Payment Status via Agent Message
    status_res = client.post(
        "/api/v1/agent-commerce/message",
        json={
            "protocol_version": "1.0",
            "message_id": f"msg_stat_{session_id}",
            "session_id": session_id,
            "trace_id": trace_id,
            "sender": {"type": "AI_BUYER", "id": "integration_ai_buyer"},
            "recipient": {"type": "MERCHANT", "id": str(m_id)},
            "action": "GET_PAYMENT_STATUS",
            "payload": {"payment_intent_id": intent_id},
        },
    )
    assert status_res.status_code == 200
    assert status_res.json()["data"]["payment_status"] == "PAID"
    assert status_res.json()["data"]["order_status"] == "PAID"

    # 13. Verify Audit Trail Events
    audit_res = client.get(f"/api/v1/audit?merchant_id={m_id}")
    assert audit_res.status_code == 200
    actions = [a["action"] for a in audit_res.json()]
    assert "AGENT_SESSION_CREATED" in actions
    assert "AGENT_CATALOG_SEARCH" in actions
    assert "AGENT_ORDER_CREATED" in actions
    assert "AGENT_PAYMENT_PROPOSED" in actions
    assert "PAYMENT_VERIFIED" in actions
