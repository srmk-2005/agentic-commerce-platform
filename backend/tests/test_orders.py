"""Tests for Order API endpoints and calculation/inventory safety logic."""
def _setup_store(client):
    # Create Merchant 1
    m1_res = client.post(
        "/api/v1/merchants",
        json={
            "name": "Chennai Sports Store",
            "email": "contact@chennaisports.com",
            "currency": "INR",
        },
    )
    m1_id = m1_res.json()["id"]

    # Create Merchant 2
    m2_res = client.post(
        "/api/v1/merchants",
        json={
            "name": "Delhi Sports Store",
            "email": "contact@delhisports.com",
            "currency": "INR",
        },
    )
    m2_id = m2_res.json()["id"]

    # Create Customer
    c_res = client.post(
        "/api/v1/customers",
        json={"name": "Ananya Sharma", "email": "ananya@example.com"},
    )
    c_id = c_res.json()["id"]

    # Create Products for Merchant 1
    p1_res = client.post(
        "/api/v1/products",
        json={
            "merchant_id": m1_id,
            "name": "Running Shoes",
            "category": "Footwear",
            "price": 2499.0,
            "stock_quantity": 10,
            "sku": "CSS-RUN-001",
        },
    )
    p1_id = p1_res.json()["id"]

    p2_res = client.post(
        "/api/v1/products",
        json={
            "merchant_id": m1_id,
            "name": "Running Socks",
            "category": "Accessories",
            "price": 299.0,
            "stock_quantity": 5,
            "sku": "CSS-ACC-001",
        },
    )
    p2_id = p2_res.json()["id"]

    # Create Product for Merchant 2
    p3_res = client.post(
        "/api/v1/products",
        json={
            "merchant_id": m2_id,
            "name": "Delhi Cricket Bat",
            "category": "Gear",
            "price": 4999.0,
            "stock_quantity": 20,
            "sku": "DSS-BAT-001",
        },
    )
    p3_id = p3_res.json()["id"]

    return {
        "m1_id": m1_id,
        "m2_id": m2_id,
        "c_id": c_id,
        "p1_id": p1_id,
        "p2_id": p2_id,
        "p3_id": p3_id,
    }


def test_create_valid_order_and_calculate_total(client):
    env = _setup_store(client)
    # Order 2x Running Shoes (2499*2 = 4998) + 3x Running Socks (299*3 = 897) = 5895.0
    payload = {
        "merchant_id": env["m1_id"],
        "customer_id": env["c_id"],
        "items": [
            {"product_id": env["p1_id"], "quantity": 2},
            {"product_id": env["p2_id"], "quantity": 3},
        ],
    }
    response = client.post("/api/v1/orders", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["merchant_id"] == env["m1_id"]
    assert data["customer_id"] == env["c_id"]
    assert data["status"] == "PENDING"
    assert data["currency"] == "INR"
    assert data["total_amount"] == 5895.0
    assert len(data["items"]) == 2

    # Check line items
    item1 = next(item for item in data["items"] if item["product_id"] == env["p1_id"])
    assert item1["quantity"] == 2
    assert item1["unit_price"] == 2499.0
    assert item1["subtotal"] == 4998.0

    item2 = next(item for item in data["items"] if item["product_id"] == env["p2_id"])
    assert item2["quantity"] == 3
    assert item2["unit_price"] == 299.0
    assert item2["subtotal"] == 897.0


def test_reject_invalid_product(client):
    env = _setup_store(client)
    payload = {
        "merchant_id": env["m1_id"],
        "customer_id": env["c_id"],
        "items": [
            {"product_id": 99999, "quantity": 1},
        ],
    }
    response = client.post("/api/v1/orders", json=payload)
    assert response.status_code == 400
    assert "not found" in response.json()["detail"]


def test_reject_insufficient_stock(client):
    env = _setup_store(client)
    # p2 has stock_quantity = 5, request 10
    payload = {
        "merchant_id": env["m1_id"],
        "customer_id": env["c_id"],
        "items": [
            {"product_id": env["p2_id"], "quantity": 10},
        ],
    }
    response = client.post("/api/v1/orders", json=payload)
    assert response.status_code == 400
    assert "Insufficient stock" in response.json()["detail"]


def test_reject_product_belonging_to_another_merchant(client):
    env = _setup_store(client)
    # p3 belongs to Merchant 2, but order is for Merchant 1
    payload = {
        "merchant_id": env["m1_id"],
        "customer_id": env["c_id"],
        "items": [
            {"product_id": env["p3_id"], "quantity": 1},
        ],
    }
    response = client.post("/api/v1/orders", json=payload)
    assert response.status_code == 400
    assert "does not belong to merchant" in response.json()["detail"]


def test_get_order_by_id_and_filters(client):
    env = _setup_store(client)
    payload = {
        "merchant_id": env["m1_id"],
        "customer_id": env["c_id"],
        "items": [
            {"product_id": env["p1_id"], "quantity": 1},
        ],
    }
    create_res = client.post("/api/v1/orders", json=payload)
    order_id = create_res.json()["id"]

    # Get by ID
    get_res = client.get(f"/api/v1/orders/{order_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == order_id
    assert get_res.json()["customer"]["name"] == "Ananya Sharma"

    # List orders by merchant filter
    list_res = client.get(f"/api/v1/orders?merchant_id={env['m1_id']}")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1
