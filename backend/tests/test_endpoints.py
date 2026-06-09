from uuid import uuid4


# --- Health ---

def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_returns_timestamp(client):
    response = client.get("/health")
    assert "timestamp" in response.json()


# --- Auth: invalid input ---

def test_register_invalid_email(client):
    response = client.post("/auth/register", json={
        "name": "Test",
        "email": "not-an-email",
        "password": "Password123!"
    })
    assert response.status_code == 422


def test_register_missing_fields(client):
    response = client.post("/auth/register", json={"name": "Test"})
    assert response.status_code == 422


def test_login_wrong_password(client):
    email = f"test_{uuid4().hex[:8]}@test.com"
    client.post("/auth/register", json={
        "name": "Test",
        "email": email,
        "password": "Password123!"
    })
    response = client.post("/auth/login", json={
        "email": email,
        "password": "WrongPassword!"
    })
    assert response.status_code == 401


def test_login_nonexistent_user(client):
    response = client.post("/auth/login", json={
        "email": "nobody@nowhere.com",
        "password": "Password123!"
    })
    assert response.status_code == 401


def test_register_duplicate_email(client):
    email = f"test_{uuid4().hex[:8]}@test.com"
    client.post("/auth/register", json={
        "name": "Test",
        "email": email,
        "password": "Password123!"
    })
    response = client.post("/auth/register", json={
        "name": "Test",
        "email": email,
        "password": "Password123!"
    })
    assert response.status_code == 409


# --- Auth: valid flow ---

def test_register_and_login(client):
    email = f"test_{uuid4().hex[:8]}@test.com"
    reg = client.post("/auth/register", json={
        "name": "Test User",
        "email": email,
        "password": "Password123!"
    })
    assert reg.status_code == 200
    assert reg.json()["email"] == email

    login = client.post("/auth/login", json={
        "email": email,
        "password": "Password123!"
    })
    assert login.status_code == 200


def test_logout(auth_client):
    response = auth_client.post("/auth/logout")
    assert response.status_code == 200


# --- Documents ---

def test_documents_requires_auth(client):
    response = client.get("/documents")
    assert response.status_code == 401


def test_documents_returns_list(auth_client):
    response = auth_client.get("/documents")
    assert response.status_code == 200
    assert "documents" in response.json()


def test_upload_requires_auth(client):
    response = client.post("/upload", data={"subjects": ["math"]})
    assert response.status_code == 401
