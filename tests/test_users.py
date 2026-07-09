async def test_register_user(client):
    response = await client.post(
        "/users/register",
        json={"email": "newuser@test.com", "password": "password123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@test.com"
    assert data["roles"] == ["USER"]


async def test_register_duplicate_email(client):
    payload = {"email": "duplicate@test.com", "password": "password123"}
    assert (await client.post("/users/register", json=payload)).status_code == 201
    assert (await client.post("/users/register", json=payload)).status_code == 409


async def test_admin_stats(client, auth_headers):
    response = await client.get("/users/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["totalUsers"] >= 1
    assert "ADMIN" in data["usersByRole"]


async def test_stats_requires_admin(client):
    await client.post(
        "/users/register",
        json={"email": "regular@test.com", "password": "password123"},
    )
    login = await client.post(
        "/auth/login",
        json={"email": "regular@test.com", "password": "password123"},
    )
    headers = {"Authorization": f"Bearer {login.json()['accessToken']}"}
    response = await client.get("/users/stats", headers=headers)
    assert response.status_code == 403
