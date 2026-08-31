"""Tests for Phase 4: AI Merchant Discovery and Manifest."""
from starlette.testclient import TestClient


def test_merchant_manifest_and_capabilities(client: TestClient):
    m_res = client.post(
        "/api/v1/merchants",
        json={"name": "Discovery Sports", "email": "disc_test@sports.com", "currency": "INR"},
    )
    m_id = m_res.json()["id"]

    res = client.get(f"/api/v1/ai/merchant/{m_id}/manifest")
    assert res.status_code == 200
    data = res.json()

    assert data["merchant_id"] == m_id
    assert data["name"] == "Discovery Sports"
    assert data["version"] == "1.0"

    # Capability guarantees: ordering supported, payments enabled in Phase 5
    caps = data["capabilities"]
    assert caps["catalog"] is True
    assert caps["search"] is True
    assert caps["product_details"] is True
    assert caps["inventory"] is True
    assert caps["order_creation"] is True
    assert caps["payment"] is True

    # Endpoint routing map
    eps = data["endpoints"]
    assert eps["catalog"] == "/api/v1/ai/catalog"
    assert eps["search"] == "/api/v1/ai/search"
    assert eps["orders"] == "/api/v1/ai/orders"


def test_merchant_profile(client: TestClient):
    m_res = client.post(
        "/api/v1/merchants",
        json={"name": "Profile Sports Store", "email": "prof_test@sports.com", "currency": "INR"},
    )
    m_id = m_res.json()["id"]

    # Add 2 products with different categories
    client.post(
        "/api/v1/products",
        json={"merchant_id": m_id, "name": "Shoe A", "category": "Footwear", "price": 1000, "stock_quantity": 10, "sku": "SH-A"},
    )
    client.post(
        "/api/v1/products",
        json={"merchant_id": m_id, "name": "Bag B", "category": "Accessories", "price": 500, "stock_quantity": 10, "sku": "BG-B"},
    )

    res = client.get(f"/api/v1/ai/merchant/{m_id}/profile")
    assert res.status_code == 200
    prof = res.json()

    assert prof["merchant_id"] == m_id
    assert "Footwear" in prof["categories"]
    assert "Accessories" in prof["categories"]
    assert prof["commerce_capabilities"]["payments"] is True
