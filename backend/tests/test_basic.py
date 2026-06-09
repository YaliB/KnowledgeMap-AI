def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register_invalid_email(client):
    response = client.post("/auth/register", json={
        "name": "Test",
        "email": "not-an-email",
        "password": "Password123!"
    })
    assert response.status_code == 422
