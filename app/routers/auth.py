import os
import logging
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app import crud
from app import models
from app.database import get_db
from app.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_token,
    has_usable_password,
)
from app.services.email_service import send_html_email
from app.services.magic_link_service import build_magic_link, generate_magic_token, hash_magic_token, render_magic_link_email

router = APIRouter(prefix="/auth", tags=["Auth"])
logger = logging.getLogger(__name__)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class MagicLinkRequest(BaseModel):
    email: EmailStr


class MagicLinkConsumeRequest(BaseModel):
    token: str


class MagicLinkConsumeResponse(BaseModel):
    requires_password_setup: bool
    access_token: str | None = None
    token_type: str | None = None
    setup_token: str | None = None


class SetPasswordRequest(BaseModel):
    setup_token: str
    password: str

@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, crud.normalize_email(credentials.email))
    if not user or not has_usable_password(user.password_hash) or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token)

@router.post("/register/magic-link", status_code=status.HTTP_202_ACCEPTED)
def request_magic_link(payload: MagicLinkRequest, db: Session = Depends(get_db)):
    email = crud.normalize_email(payload.email)
    cooldown_seconds = int(os.getenv("MAGIC_LINK_COOLDOWN_SECONDS", "60"))
    since = datetime.now(timezone.utc) - timedelta(seconds=cooldown_seconds)
    recent_requests = crud.count_recent_magic_link_requests(db, email, since)
    if recent_requests > 0:
        return {"message": "If eligible, you will receive a link shortly."}

    raw_token = generate_magic_token()
    token_hash = hash_magic_token(raw_token)
    expire_minutes = int(os.getenv("MAGIC_LINK_EXPIRE_MINUTES", "15"))
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    crud.create_magic_link_token(db, email=email, token_hash=token_hash, expires_at=expires_at)

    magic_link = build_magic_link(raw_token)
    html_body = render_magic_link_email(magic_link)
    text_body = f"Use this link to sign in: {magic_link}"
    try:
        send_html_email(
            to_email=email,
            subject="Sign in to Financial Agent System",
            html_body=html_body,
            text_body=text_body,
        )
    except Exception:
        logger.exception("Failed to send magic link email")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to send magic link email right now",
        )

    return {"message": "If eligible, you will receive a link shortly."}


@router.post("/register/magic-link/consume", response_model=MagicLinkConsumeResponse)
def consume_magic_link(payload: MagicLinkConsumeRequest, db: Session = Depends(get_db)):
    token_hash = hash_magic_token(payload.token)
    token = crud.get_magic_link_token_by_hash(db, token_hash)
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    now = datetime.now(timezone.utc)
    expires_at = token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if token.used_at is not None or expires_at < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    try:
        crud.consume_magic_link_token(db, token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")
    user = crud.get_user_by_email(db, token.email)
    if not user:
        user = crud.create_user_without_password(db, email=token.email)

    if not has_usable_password(user.password_hash):
        setup_expire_minutes = int(os.getenv("MAGIC_LINK_SETUP_EXPIRE_MINUTES", "10"))
        setup_token = create_access_token(
            {"sub": str(user.id), "purpose": "password_setup", "mli": token.id},
            expires_delta=timedelta(minutes=setup_expire_minutes),
        )
        return MagicLinkConsumeResponse(requires_password_setup=True, setup_token=setup_token)

    access_token = create_access_token({"sub": str(user.id)})
    return MagicLinkConsumeResponse(requires_password_setup=False, access_token=access_token, token_type="bearer")


@router.post("/register/magic-link/set-password", response_model=TokenResponse)
def set_password_from_magic_link(payload: SetPasswordRequest, db: Session = Depends(get_db)):
    if len(payload.password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 8 characters")

    claims = decode_token(payload.setup_token)
    if claims.get("purpose") != "password_setup":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid setup token")

    user_id = claims.get("sub")
    token_id = claims.get("mli")
    if not user_id or not token_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid setup token")

    user = crud.get_user(db, int(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid setup token")

    token = db.query(models.MagicLinkToken).filter(models.MagicLinkToken.id == int(token_id)).first()
    if not token or token.setup_used:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid setup token")

    now = datetime.now(timezone.utc)
    expires_at = token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if token.used_at is None or expires_at < now or token.purpose != "register" or token.email != user.email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid setup token")

    if has_usable_password(user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password already configured")

    crud.set_user_password(db, user=user, password_hash=get_password_hash(payload.password))
    crud.mark_magic_link_setup_used(db, token)
    access_token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=access_token)
