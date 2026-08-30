"""Tests for Product API endpoints."""
def _create_sample_merchant(client):
    res = client.post(
        "/api/v1/merchants",
        json={
            "name": "Sports Hub",
            "email": "info@sportshub.com",
            "currency": "INR",
        },
    )
    return res.json()["id"]


def test_create_product(client):
    m_id = _create_sample_merchant(client)
    payload = {
        "merchant_id": m_id,
        "name": "Running Shoes",
        "description": "Cushioned road running shoes",
        "category": "Footwear",
        "price": 2499.0,
        "currency": "INR",
        "stock_quantity": 50,
        "sku": "CSS-RUN-001",
        "is_active": True,
    }
    response = client.post("/api/v1/products", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["name"] == "Running Shoes"
    assert data["price"] == 2499.0
    assert data["stock_quantity"] == 50
    assert data["sku"] == "CSS-RUN-001"


def test_create_product_invalid_merchant(client):
    payload = {
        "merchant_id": 9999,
        "name": "Ghost Shoes",
        "category": "Footwear",
        "price": 1000.0,
        "sku": "GHOST-001",
    }
    response = client.post("/api/v1/products", json=payload)
    assert response.status_code == 400
    assert "does not exist" in response.json()["detail"]


def test_get_products_list_and_filters(client):
    m_id = _create_sample_merchant(client)
    
    # Create 3 products
    p1 = {
        "merchant_id": m_id,
        "name": "Running Shoes",
        "category": "Footwear",
        "price": 2499.0,
        "sku": "CSS-RUN-001",
        "stock_quantity": 50,
        "is_active": True,
    }
    p2 = {
        "merchant_id": m_id,
        "name": "Running Socks",
        "category": "Accessories",
        "price": 299.0,
        "sku": "CSS-ACC-001",
        "stock_quantity": 100,
        "is_active": True,
    }
    p3 = {
        "merchant_id": m_id,
        "name": "Discontinued Bag",
        "category": "Bags & Gear",
        "price": 999.0,
        "sku": "CSS-BAG-OLD",
        "stock_quantity": 0,
        "is_active": False,
    }
    client.post("/api/v1/products", json=p1)
    client.post("/api/v1/products", json=p2)
    client.post("/api/v1/products", json=p3)

    # All products
    res = client.get("/api/v1/products")
    assert res.status_code == 200
    assert len(res.json()) == 3

    # Filter by category
    res_cat = client.get("/api/v1/products?category=Footwear")
    assert res_cat.status_code == 200
    assert len(res_cat.json()) == 1
    assert res_cat.json()[0]["sku"] == "CSS-RUN-001"

    # Filter by is_active=true
    res_active = client.get("/api/v1/products?is_active=true")
    assert res_active.status_code == 200
    assert len(res_active.json()) == 2


def test_search_products(client):
    m_id = _create_sample_merchant(client)
    p1 = {
        "merchant_id": m_id,
        "name": "Premium Marathon Running Shoes",
        "description": "High tier footwear for runners",
        "category": "Footwear",
        "price": 3499.0,
        "sku": "CSS-RUN-002",
    }
    p2 = {
        "merchant_id": m_id,
        "name": "Sports T-Shirt",
        "description": "Breathable gym shirt",
        "category": "Apparel",
        "price": 999.0,
        "sku": "CSS-APP-001",
    }
    client.post("/api/v1/products", json=p1)
    client.post("/api/v1/products", json=p2)

    # Search for shoe
    res = client.get("/api/v1/products?search=shoe")
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["sku"] == "CSS-RUN-002"

    # Search for shirt
    res_shirt = client.get("/api/v1/products?search=shirt")
    assert res_shirt.status_code == 200
    assert len(res_shirt.json()) == 1
    assert res_shirt.json()[0]["sku"] == "CSS-APP-001"


def test_update_product(client):
    m_id = _create_sample_merchant(client)
    create_res = client.post(
        "/api/v1/products",
        json={
            "merchant_id": m_id,
            "name": "Original Shoes",
            "category": "Footwear",
            "price": 2000.0,
            "stock_quantity": 10,
            "sku": "ORIG-001",
        },
    )
    p_id = create_res.json()["id"]

    res = client.put(
        f"/api/v1/products/{p_id}",
        json={"price": 2299.0, "stock_quantity": 25},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["price"] == 2299.0
    assert data["stock_quantity"] == 25
    assert data["name"] == "Original Shoes"


def test_delete_product(client):
    m_id = _create_sample_merchant(client)
    create_res = client.post(
        "/api/v1/products",
        json={
            "merchant_id": m_id,
            "name": "Temp Shoes",
            "category": "Footwear",
            "price": 1500.0,
            "sku": "TEMP-001",
        },
    )
    p_id = create_res.json()["id"]

    del_res = client.delete(f"/api/v1/products/{p_id}")
    assert del_res.status_code == 200

    get_res = client.get(f"/api/v1/products/{p_id}")
    assert get_res.status_code == 404
