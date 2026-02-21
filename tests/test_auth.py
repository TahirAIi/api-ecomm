def test_register_user(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "new@test.com", "password": "password123", "full_name": "New User"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "new@test.com"
    assert "uuid" in data
    assert "password" not in data
    assert "hashed_password" not in data


def test_register_duplicate_email(client, regular_user):
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "user@test.com", "password": "password123", "full_name": "Dup User"},
    )
    assert resp.status_code == 400


def test_login_success(client, regular_user):
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "user@test.com", "password": "password123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data


def test_login_wrong_password(client, regular_user):
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "user@test.com", "password": "wrongpassword"},
    )
    assert resp.status_code == 401


def test_login_nonexistent_user(client):
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "nobody@test.com", "password": "password123"},
    )
    assert resp.status_code == 401
