"""Tests for Phase 4: Simulated AI Buyer Agent LangGraph Execution."""
from starlette.testclient import TestClient


def _setup_buyer_agent_env(client: TestClient):
    m_res = client.post(
        "/api/v1/merchants",
        json={"name": "Buyer Graph Store", "email": "bgraph@sports.com", "currency": "INR"},
    )
    m_id = m_res.json()["id"]

    p1 = client.post(
        "/api/v1/products",
        json={
            "merchant_id": m_id,
            "name": "Aero Running Shoes",
            "category": "Running",
            "price": 2499.0,
            "stock_quantity": 10,
            "sku": "AER-RUN-001",
        },
    ).json()

    p2 = client.post(
        "/api/v1/products",
        json={
            "merchant_id": m_id,
            "name": "Ultra Running Shoes",
            "category": "Running",
            "price": 4500.0,
            "stock_quantity": 10,
            "sku": "ULT-RUN-002",
        },
    ).json()

    return m_id, p1["id"], p2["id"]


def test_ai_buyer_chat_intent_and_candidate_discovery(client: TestClient):
    m_id, p1_id, p2_id = _setup_buyer_agent_env(client)

    # Prompt: "I need running shoes under ₹3000"
    res = client.post(
        "/api/v1/buyer/chat",
        json={"merchant_id": m_id, "message": "I need running shoes under ₹3000."},
    )
    assert res.status_code == 200
    data = res.json()

    assert len(data["candidates"]) >= 1
    assert data["selected_product"] is not None
    assert data["selected_product"]["id"] == p1_id
    assert data["selected_product"]["price"] == 2499.0

    # Execution trace has steps
    assert len(data["execution_steps"]) >= 4
    assert any("Discovered merchant" in s for s in data["execution_steps"])
    assert any("Queried AI Catalog" in s for s in data["execution_steps"])


def test_ai_buyer_chat_places_order_when_requested(client: TestClient):
    m_id, p1_id, _ = _setup_buyer_agent_env(client)

    # Prompt: "Buy the Aero Running Shoes"
    res = client.post(
        "/api/v1/buyer/chat",
        json={"merchant_id": m_id, "message": "Buy the Aero Running Shoes."},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["order_created"] is not None
    assert data["order_created"]["total_amount"] == 2499.0
    assert "Order Created" in data["response"]
