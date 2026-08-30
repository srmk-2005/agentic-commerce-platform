"""Tests for Merchant API endpoints."""
def test_create_merchant(client):
    payload = {
        "name": "Chennai Sports Store",
        "email": "contact@chennaisports.com",
        "description": "Premier sports equipment store in Chennai.",
        "currency": "INR",
        "is_active": True,
    }
    response = client.post("/api/v1/merchants", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["name"] == payload["name"]
    assert data["email"] == payload["email"]
    assert data["currency"] == "INR"
    assert data["is_active"] is True
    assert "created_at" in data


def test_create_merchant_duplicate_email(client):
    payload = {
        "name": "Merchant 1",
        "email": "duplicate@example.com",
        "currency": "INR",
        "is_active": True,
    }
    res1 = client.post("/api/v1/merchants", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/merchants", json=payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


def test_get_merchant_by_id(client):
    payload = {
        "name": "Bangalore Gear Store",
        "email": "bangalore@gear.com",
        "currency": "INR",
    }
    create_res = client.post("/api/v1/merchants", json=payload)
    assert create_res.status_code == 201
    m_id = create_res.json()["id"]

    res = client.get(f"/api/v1/merchants/{m_id}")
    assert res.status_code == 200
    assert res.json()["name"] == "Bangalore Gear Store"


def test_get_merchant_not_found(client):
    res = client.get("/api/v1/merchants/9999")
    assert res.status_code == 404


def test_list_merchants(client):
    for i in range(3):
        client.post(
            "/api/v1/merchants",
            json={
                "name": f"Merchant {i}",
                "email": f"m{i}@example.com",
                "currency": "INR",
            },
        )
    res = client.get("/api/v1/merchants")
    assert res.status_code == 200
    assert len(res.json()) == 3


def test_update_merchant(client):
    create_res = client.post(
        "/api/v1/merchants",
        json={
            "name": "Old Merchant Name",
            "email": "old@merchant.com",
            "currency": "INR",
        },
    )
    m_id = create_res.json()["id"]

    update_payload = {"name": "New Merchant Name", "description": "Updated description"}
    res = client.put(f"/api/v1/merchants/{m_id}", json=update_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "New Merchant Name"
    assert data["description"] == "Updated description"
    assert data["email"] == "old@merchant.com"


def test_delete_merchant(client):
    create_res = client.post(
        "/api/v1/merchants",
        json={
            "name": "To Delete",
            "email": "delete@merchant.com",
            "currency": "INR",
        },
    )
    m_id = create_res.json()["id"]

    del_res = client.delete(f"/api/v1/merchants/{m_id}")
    assert del_res.status_code == 200

    get_res = client.get(f"/api/v1/merchants/{m_id}")
    assert get_res.status_code == 404
