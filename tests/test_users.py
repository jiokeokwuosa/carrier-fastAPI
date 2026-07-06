def test_register_user(client):
    response = client.post(
        "/users/register",
        json={"email": "newuser@test.com", "password": "password123"},
    )
    assert response.status_code == 201
    assert response.json()["email"] == "newuser@test.com"


def test_register_duplicate_email(client):
    payload = {"email": "duplicate@test.com", "password": "password123"}
    assert client.post("/users/register", json=payload).status_code == 201
    assert client.post("/users/register", json=payload).status_code == 409
