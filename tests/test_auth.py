from datetime import datetime, timedelta, timezone
from fastapi import status
from app import models
from app import crud
from app.security import get_password_hash
from app.services.magic_link_service import hash_magic_token


def test_login_flow_for_user_with_password(client, db_session):
    payload = {"email": "user@example.com", "password": "secret123"}
    crud.create_user(
        db_session,
        email=payload["email"],
        password_hash=get_password_hash(payload["password"]),
    )
    login_response = client.post("/auth/login", json=payload)
    assert login_response.status_code == status.HTTP_200_OK
    assert "access_token" in login_response.json()


def test_magic_link_request_returns_202(client):
    response = client.post("/auth/register/magic-link", json={"email": "new@example.com"})
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert "message" in response.json()


def test_login_with_invalid_credentials(client, db_session):
    payload = {"email": "missing@example.com", "password": "secret123"}
    crud.create_user(
        db_session,
        email=payload["email"],
        password_hash=get_password_hash(payload["password"]),
    )
    invalid = client.post("/auth/login", json={"email": payload["email"], "password": "wrong"})
    assert invalid.status_code == status.HTTP_401_UNAUTHORIZED
    assert invalid.json()["detail"] == "Invalid credentials"


def test_magic_link_requires_password_setup_for_new_user(client, db_session):
    email = "magic-new@example.com"
    request_response = client.post("/auth/register/magic-link", json={"email": email})
    assert request_response.status_code == status.HTTP_202_ACCEPTED

    token_record = db_session.query(models.MagicLinkToken).filter(models.MagicLinkToken.email == email).first()
    assert token_record is not None

    raw_token = "token-not-known"
    invalid_consume = client.post("/auth/register/magic-link/consume", json={"token": raw_token})
    assert invalid_consume.status_code == status.HTTP_400_BAD_REQUEST


def test_magic_link_create_password_flow(client, db_session):
    raw_token = "test-magic-token"
    email = "magic-flow@example.com"
    db_session.add(
        models.MagicLinkToken(
            email=email,
            token_hash=hash_magic_token(raw_token),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
            purpose="register",
        )
    )
    db_session.commit()

    consume_response = client.post("/auth/register/magic-link/consume", json={"token": raw_token})
    assert consume_response.status_code == status.HTTP_200_OK
    payload = consume_response.json()
    assert payload["requires_password_setup"] is True
    assert "setup_token" in payload

    set_password_response = client.post(
        "/auth/register/magic-link/set-password",
        json={"setup_token": payload["setup_token"], "password": "secret123"},
    )
    assert set_password_response.status_code == status.HTTP_200_OK
    assert "access_token" in set_password_response.json()
