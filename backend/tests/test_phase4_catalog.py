"""Tests for Phase 4: AI Catalog API and Product Representation."""
from starlette.testclient import TestClient


def _setup_catalog_env(client: TestClient):
    # Create merchant
    m_res = client.post(
        "/api/v1/merchants",
        json={"name": "Catalog Test Merchant", "email": "cat_test@sports.com", "currency": "INR"},
    )
    m_id = m_res.json()["id"]

    # Product 1: In Stock Running Shoes
    p1 = client.post(
        "/api/v1/products",
        json={
            "merchant_id": m_id,
            "name": "Velocity Running Shoes",
            "category": "Running",
            "price": 2499.0,
            "stock_quantity": 25,
            "sku": "RUN-VEL-001",
            "is_active": True,
        },
    ).json()

    # Product 2: Low Stock Premium Shoes
    p2 = client.post(
        "/api/v1/products",
        json={
            "merchant_id": m_id,
            "name": "Marathon Pro Shoes",
            "category": "Running",
            "price": 4999.0,
            "stock_quantity": 3,
            "sku": "RUN-MAR-002",
            "is_active": True,
        },
    ).json()

    # Product 3: Out of Stock Socks
    p3 = client.post(
        "/api/v1/products",
        json={
            "merchant_id": m_id,
            "name": "Cushioned Running Socks",
            "category": "Running",
            "price": 399.0,
            "stock_quantity": 0,
            "sku": "ACC-SOC-003",
            "is_active": True,
        },
    ).json()

    # Product 4: Inactive T-Shirt
    p4 = client.post(
        "/api/v1/products",
        json={
            "merchant_id": m_id,
            "name": "Archived Jersey",
            "category": "Sportswear",
            "price": 999.0,
            "stock_quantity": 50,
            "sku": "APP-JER-004",
            "is_active": False,
        },
    ).json()

    return m_id, p1["id"], p2["id"], p3["id"], p4["id"]


def test_ai_catalog_returns_canonical_ai_products(client: TestClient):
    m_id, p1_id, p2_id, p3_id, p4_id = _setup_catalog_env(client)

    res = client.get(f"/api/v1/ai/catalog?merchant_id={m_id}")
    assert res.status_code == 200
    data = res.json()

    assert data["merchant_id"] == m_id
    assert data["total_count"] == 3  # Inactive item p4 is excluded

    prod_map = {p["id"]: p for p in data["products"]}
    assert p1_id in prod_map
    assert prod_map[p1_id]["availability"] == "IN_STOCK"
    assert prod_map[p1_id]["stock_quantity"] == 25
    assert prod_map[p1_id]["attributes"]["brand"] == "ProSport India"
    assert prod_map[p1_id]["purchase_constraints"]["max_quantity_per_order"] == 5

    # Check Low Stock
    assert prod_map[p2_id]["availability"] == "LOW_STOCK"

    # Check Out of Stock
    assert prod_map[p3_id]["availability"] == "OUT_OF_STOCK"


def test_ai_catalog_filters(client: TestClient):
    m_id, p1_id, p2_id, p3_id, _ = _setup_catalog_env(client)

    # 1. In Stock Filter
    res_stock = client.get(f"/api/v1/ai/catalog?merchant_id={m_id}&in_stock=true")
    assert res_stock.status_code == 200
    stock_prods = res_stock.json()["products"]
    assert len(stock_prods) == 2  # p1 and p2 (p3 is 0 stock)

    # 2. Price Filter (max_price = 3000)
    res_price = client.get(f"/api/v1/ai/catalog?merchant_id={m_id}&max_price=3000")
    assert res_price.status_code == 200
    price_prods = res_price.json()["products"]
    assert all(p["price"] <= 3000 for p in price_prods)

    # 3. Search Filter
    res_search = client.get(f"/api/v1/ai/catalog?merchant_id={m_id}&search=Marathon")
    assert res_search.status_code == 200
    search_prods = res_search.json()["products"]
    assert len(search_prods) == 1
    assert search_prods[0]["id"] == p2_id
