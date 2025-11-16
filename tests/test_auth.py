from fastapi import status


def test_register_and_login_flow(client):
    payload = {"email": "user@example.com", "password": "secret123"}
    register_response = client.post("/auth/register", json=payload)
    assert register_response.status_code == status.HTTP_201_CREATED
    assert "access_token" in register_response.json()

    login_response = client.post("/auth/login", json=payload)
    assert login_response.status_code == status.HTTP_200_OK
    assert "access_token" in login_response.json()


def test_duplicate_registration_returns_400(client):
    payload = {"email": "duplicate@example.com", "password": "secret123"}
    assert client.post("/auth/register", json=payload).status_code == status.HTTP_201_CREATED
    duplicate = client.post("/auth/register", json=payload)
    assert duplicate.status_code == status.HTTP_400_BAD_REQUEST
    assert duplicate.json()["detail"] == "Email already registered"


def test_login_with_invalid_credentials(client):
    payload = {"email": "missing@example.com", "password": "secret123"}
    # ensure user exists
    client.post("/auth/register", json=payload)
    invalid = client.post("/auth/login", json={"email": payload["email"], "password": "wrong"})
    assert invalid.status_code == status.HTTP_401_UNAUTHORIZED
    assert invalid.json()["detail"] == "Invalid credentials"
