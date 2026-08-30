"""Tests for LangGraph execution, opportunity generation, and agent endpoints."""
from app.agent.graph import create_merchant_agent_graph
from app.db.models import Customer, Merchant, Order, OrderItem, OrderStatus, Product


def _setup_graph_environment(client):
    # 1. Create Merchant
    m_res = client.post(
        "/api/v1/merchants",
        json={"name": "Chennai Sports Store", "email": "agent_test@sports.com", "currency": "INR"},
    )
    m_id = m_res.json()["id"]

    # 2. Create Customer
    c_res = client.post(
        "/api/v1/customers",
        json={"name": "Priya", "email": "priya@agent.com"},
    )
    c_id = c_res.json()["id"]

    # 3. Create Products (2 in Footwear for upsell, 1 in Accessories for cross-sell)
    p1 = client.post(
        "/api/v1/products",
        json={"merchant_id": m_id, "name": "Running Shoes", "category": "Footwear", "price": 2500.0, "stock_quantity": 50, "sku": "CSS-RUN-01"},
    ).json()

    p2 = client.post(
        "/api/v1/products",
        json={"merchant_id": m_id, "name": "Pro Marathon Shoes", "category": "Footwear", "price": 4500.0, "stock_quantity": 30, "sku": "CSS-RUN-02"},
    ).json()

    p3 = client.post(
        "/api/v1/products",
        json={"merchant_id": m_id, "name": "Compression Socks", "category": "Accessories", "price": 300.0, "stock_quantity": 100, "sku": "CSS-ACC-01"},
    ).json()

    # 4. Create Historical Orders linking Running Shoes + Compression Socks
    client.post(
        "/api/v1/orders",
        json={
            "merchant_id": m_id,
            "customer_id": c_id,
            "items": [
                {"product_id": p1["id"], "quantity": 1},
                {"product_id": p3["id"], "quantity": 2},
            ],
        },
    )

    return m_id, p1["id"], p2["id"], p3["id"]


def test_agent_graph_execution(db_session, client):
    m_id, p1_id, p2_id, p3_id = _setup_graph_environment(client)
    
    app_graph = create_merchant_agent_graph(db_session)
    state = app_graph.invoke({
        "merchant_id": m_id,
        "user_request": "How can I increase sales?",
    })

    assert state.get("error") is None
    assert state.get("merchant_context") is not None
    assert state["merchant_context"]["name"] == "Chennai Sports Store"

    opps = state.get("validated_opportunities", [])
    assert len(opps) >= 1

    # Verify cross-sell and upsell presence
    opp_types = [o["type"] for o in opps]
    assert "CROSS_SELL" in opp_types or "UPSELL" in opp_types

    assert state.get("final_response") is not None
    assert len(state["final_response"]) > 0


def test_agent_graph_invalid_merchant(db_session):
    app_graph = create_merchant_agent_graph(db_session)
    state = app_graph.invoke({
        "merchant_id": 99999,
        "user_request": "How can I grow?",
    })

    assert state.get("error") is not None
    assert "not found" in state["error"]


def test_agent_analyze_api_endpoint(client):
    m_id, _, _, _ = _setup_graph_environment(client)

    response = client.post(
        "/api/v1/agent/analyze",
        json={"merchant_id": m_id, "request": "Give me growth ideas"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["merchant_id"] == m_id
    assert len(data["opportunities"]) >= 1
    assert "summary" in data
    assert "provider_used" in data

    # Check opportunity structure and FACT / AI INTERPRETATION separation
    opp = data["opportunities"][0]
    assert opp["id"] is not None
    assert opp["title"] is not None
    assert opp["fact_statement"] is not None
    assert opp["ai_interpretation"] is not None
    assert opp["confidence"] >= 0.0
    assert opp["requires_merchant_approval"] is True


def test_agent_chat_api_endpoint(client):
    m_id, _, _, _ = _setup_graph_environment(client)

    response = client.post(
        "/api/v1/agent/chat",
        json={"merchant_id": m_id, "message": "What products are bought together?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert len(data["response"]) > 0
    assert isinstance(data["opportunities"], list)


def test_agent_metrics_api_endpoint(client):
    m_id, _, _, _ = _setup_graph_environment(client)

    response = client.get(f"/api/v1/agent/metrics/{m_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total_opportunities"] >= 1
    assert data["potential_revenue_impact"] >= 0.0
