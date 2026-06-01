from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models
from app.security import get_pending_password_placeholder


def get_user(db: Session, user_id: int) -> models.User | None:
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> models.User | None:
    return db.query(models.User).filter(models.User.email == email).first()


def normalize_email(email: str) -> str:
    return email.strip().lower()


def get_or_create_default_portfolio(db: Session, user_id: int) -> models.Portfolio:
    portfolio = (
        db.query(models.Portfolio)
        .filter(models.Portfolio.user_id == user_id)
        .order_by(models.Portfolio.id.asc())
        .first()
    )
    if portfolio is not None:
        return portfolio

    portfolio = models.Portfolio(user_id=user_id, name="Default")
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio


def create_user(db: Session, email: str, password_hash: str) -> models.User:
    db_user = models.User(email=email, password_hash=password_hash)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    get_or_create_default_portfolio(db, db_user.id)
    db.refresh(db_user)
    return db_user


def create_user_without_password(db: Session, email: str) -> models.User:
    db_user = models.User(email=email, password_hash=get_pending_password_placeholder())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    get_or_create_default_portfolio(db, db_user.id)
    db.refresh(db_user)
    return db_user


def get_or_create_legacy_portfolio(db: Session) -> models.Portfolio:
    existing = db.query(models.Portfolio).order_by(models.Portfolio.id.asc()).first()
    if existing is not None:
        return existing
    user = get_user_by_email(db, "legacy-owner@local")
    if user is None:
        user = create_user(db, email="legacy-owner@local", password_hash=get_pending_password_placeholder())
    return get_or_create_default_portfolio(db, user.id)


def set_user_password(db: Session, user: models.User, password_hash: str) -> models.User:
    user.password_hash = password_hash
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_magic_link_token(
    db: Session,
    email: str,
    token_hash: str,
    expires_at: datetime,
    purpose: str = "register",
) -> models.MagicLinkToken:
    db_token = models.MagicLinkToken(
        email=email,
        token_hash=token_hash,
        expires_at=expires_at,
        purpose=purpose,
    )
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token


def count_recent_magic_link_requests(
    db: Session,
    email: str,
    since: datetime,
) -> int:
    return (
        db.query(func.count(models.MagicLinkToken.id))
        .filter(models.MagicLinkToken.email == email, models.MagicLinkToken.created_at >= since)
        .scalar()
        or 0
    )


def get_magic_link_token_by_hash(db: Session, token_hash: str) -> models.MagicLinkToken | None:
    return db.query(models.MagicLinkToken).filter(models.MagicLinkToken.token_hash == token_hash).first()


def consume_magic_link_token(db: Session, token: models.MagicLinkToken) -> models.MagicLinkToken:
    now = datetime.now(timezone.utc)
    updated_rows = (
        db.query(models.MagicLinkToken)
        .filter(
            models.MagicLinkToken.id == token.id,
            models.MagicLinkToken.used_at.is_(None),
            models.MagicLinkToken.expires_at >= now,
        )
        .update({models.MagicLinkToken.used_at: now}, synchronize_session=False)
    )
    db.commit()
    if updated_rows != 1:
        raise ValueError("Magic link already used or expired")
    db.refresh(token)
    return token


def mark_magic_link_setup_used(db: Session, token: models.MagicLinkToken) -> models.MagicLinkToken:
    token.setup_used = True
    db.add(token)
    db.commit()
    db.refresh(token)
    return token
