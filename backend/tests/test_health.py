"""Tests for Health check API."""
def test_health_check(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ok", "healthy"]
    assert "services" in data or data.get("service") == "ai-merchant-commerce-api"
