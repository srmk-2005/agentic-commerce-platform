"""Tests for Phase 5: Payment Approval Gate, Revalidation, and Rejection."""
from starlette.testclient import TestClient


def _setup_approval_env(client: TestClient):
    m_res = client.post(
        "/api/v1/merchants",
        json={"name": "Approval Gate Merchant", "email": "appr_gate@sports.com", "currency": "INR"},
    )
    m_id = m_res.json()["id"]

    p1 = client.post(
        "/api/v1/products",
        json={"merchant_id": m_id, "name": "Race Shoes", "category": "Footwear", "price": 2000.0, "stock_quantity": 10, "sku": "APP-RCE-01"},
    ).json()

    order_res = client.post(
        "/api/v1/ai/orders",
        json={"merchant_id": m_id, "items": [{"product_id": p1["id"], "quantity": 1}]},
    ).json()

    return m_id, p1["id"], order_res["order_id"]


def test_payment_approval_workflow_success(client: TestClient):
    m_id, _, order_id = _setup_approval_env(client)

    # 1. Propose payment
    prop = client.post(
        "/api/v1/ai/payments/propose",
        json={"merchant_id": m_id, "order_id": order_id},
    ).json()
    intent_id = prop["id"]

    # 2. Approve payment
    appr_res = client.post(
        f"/api/v1/ai/payments/{intent_id}/approve",
        json={"reviewed_by": "Test Store Owner", "reason": "Authorized payment"},
    )
    assert appr_res.status_code == 200
    rzp_data = appr_res.json()

    assert rzp_data["payment_intent_id"] == intent_id
    assert rzp_data["amount"] == 200000  # 2000 INR = 200000 paise
    assert rzp_data["currency"] == "INR"
    assert "razorpay_order_id" in rzp_data
    assert rzp_data["is_test_mode"] is True


def test_payment_rejection_workflow(client: TestClient):
    m_id, _, order_id = _setup_approval_env(client)

    # 1. Propose payment
    prop = client.post(
        "/api/v1/ai/payments/propose",
        json={"merchant_id": m_id, "order_id": order_id},
    ).json()
    intent_id = prop["id"]

    # 2. Reject payment
    rej_res = client.post(
        f"/api/v1/ai/payments/{intent_id}/reject",
        json={"reviewed_by": "Test Store Owner", "reason": "Customer cancelled request"},
    )
    assert rej_res.status_code == 200
    data = rej_res.json()
    assert data["status"] == "REJECTED"
    assert data["approved_by"] == "Test Store Owner"
