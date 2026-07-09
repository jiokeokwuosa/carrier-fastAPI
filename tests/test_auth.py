async def test_login_returns_tokens(client):
    response = await client.post(
        "/auth/login",
        json={"email": "admin@test.com", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "accessToken" in data
    assert "refreshToken" in data
    assert data["expiresIn"] > 0


async def test_login_rejects_invalid_credentials(client):
    response = await client.post(
        "/auth/login",
        json={"email": "admin@test.com", "password": "wrong"},
    )
    assert response.status_code == 401


async def test_me_returns_current_user(client, auth_headers):
    response = await client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "admin@test.com"
