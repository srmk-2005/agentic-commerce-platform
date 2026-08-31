"""Tests for Phase 4: Deterministic Ranked Product Search."""
from starlette.testclient import TestClient


def _setup_search_env(client: TestClient):
    m_res = client.post(
        "/api/v1/merchants",
        json={"name": "Search Test Merchant", "email": "srch_test@sports.com", "currency": "INR"},
    )
    m_id = m_res.json()["id"]

    # 1. Exact match product in stock
    p1 = client.post(
        "/api/v1/products",
        json={
            "merchant_id": m_id,
            "name": "Trail Running Shoes",
            "category": "Running",
            "price": 2799.0,
            "stock_quantity": 15,
            "sku": "TR-RUN-001",
            "description": "Durable all-terrain trail running shoes",
        },
    ).json()

    # 2. Premium Running Shoes (higher price)
    p2 = client.post(
        "/api/v1/products",
        json={
            "merchant_id": m_id,
            "name": "Elite Carbon Running Shoes",
            "category": "Running",
            "price": 6999.0,
            "stock_quantity": 5,
            "sku": "EL-RUN-002",
            "description": "Carbon plate marathon racers",
        },
    ).json()

    # 3. Running Socks (lower price)
    p3 = client.post(
        "/api/v1/products",
        json={
            "merchant_id": m_id,
            "name": "Anti-Blister Running Socks",
            "category": "Running",
            "price": 499.0,
            "stock_quantity": 40,
            "sku": "SK-RUN-003",
            "description": "Breathable running socks",
        },
    ).json()

    # 4. Football Boot (different category)
    p4 = client.post(
        "/api/v1/products",
        json={
            "merchant_id": m_id,
            "name": "Striker Football Boots",
            "category": "Football",
            "price": 2499.0,
            "stock_quantity": 20,
            "sku": "FT-BOT-004",
            "description": "Firm ground football cleats",
        },
    ).json()

    return m_id, p1["id"], p2["id"], p3["id"], p4["id"]


def test_deterministic_ranked_search_relevance(client: TestClient):
    m_id, p1_id, p2_id, p3_id, p4_id = _setup_search_env(client)

    # Search for "running shoes" with max price 3000
    res = client.get(f"/api/v1/ai/search?merchant_id={m_id}&query=running%20shoes&max_price=3000")
    assert res.status_code == 200
    data = res.json()

    # Trail Running Shoes (p1) should be #1 because exact match + in stock + under 3000
    assert data["total_matches"] >= 1
    top_hit = data["results"][0]
    assert top_hit["product"]["id"] == p1_id
    assert top_hit["relevance_score"] >= 80.0  # Exact name + in stock + price range

    # Elite Carbon (p2) is excluded by max_price=3000
    ids_returned = [r["product"]["id"] for r in data["results"]]
    assert p2_id not in ids_returned


def test_search_category_and_keyword_scoring(client: TestClient):
    m_id, p1_id, p2_id, p3_id, p4_id = _setup_search_env(client)

    # Search category "Football"
    res = client.get(f"/api/v1/ai/search?merchant_id={m_id}&category=Football")
    assert res.status_code == 200
    results = res.json()["results"]
    assert len(results) == 1
    assert results[0]["product"]["id"] == p4_id
