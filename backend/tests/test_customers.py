"""Tests for Customer API endpoints."""
def test_create_customer(client):
    payload = {
        "name": "Ananya Sharma",
        "email": "ananya.sharma@example.com",
    }
    response = client.post("/api/v1/customers", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["name"] == "Ananya Sharma"
    assert data["email"] == "ananya.sharma@example.com"
    assert "created_at" in data


def test_create_customer_duplicate_email(client):
    payload = {
        "name": "User One",
        "email": "duplicate@customer.com",
    }
    res1 = client.post("/api/v1/customers", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/customers", json=payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


def test_get_customer_by_id(client):
    res = client.post(
        "/api/v1/customers",
        json={"name": "Rajesh Kumar", "email": "rajesh@example.com"},
    )
    c_id = res.json()["id"]

    get_res = client.get(f"/api/v1/customers/{c_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Rajesh Kumar"


def test_list_customers(client):
    for i in range(3):
        client.post(
            "/api/v1/customers",
            json={"name": f"Customer {i}", "email": f"cust{i}@example.com"},
        )
    res = client.get("/api/v1/customers")
    assert res.status_code == 200
    assert len(res.json()) == 3
