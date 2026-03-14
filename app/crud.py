from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from typing import Optional
from datetime import datetime, timezone, date
from decimal import Decimal
from . import models, schemas

# --- User CRUD ---
def get_user(db: Session, user_id: int) -> models.User | None:
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> models.User | None:
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, email: str, password_hash: str, google_sub: str | None = None) -> models.User:
    db_user = models.User(email=email, password_hash=password_hash, google_sub=google_sub)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- Asset CRUD ---
def get_asset(db: Session, asset_id: int) -> models.Asset | None:
    return db.query(models.Asset).filter(models.Asset.id == asset_id).first()

def get_asset_by_ticker(db: Session, ticker: str) -> models.Asset | None:
    return db.query(models.Asset).filter(models.Asset.ticker == ticker).first()

def get_assets(db: Session, ticker: Optional[str] = None, skip: int = 0, limit: int = 100) -> list[models.Asset]:
    query = db.query(models.Asset)
    if ticker is not None:
        query = query.filter(models.Asset.ticker == ticker)
    return query.offset(skip).limit(limit).all()

def create_asset(db: Session, asset: schemas.AssetCreate) -> models.Asset:
    db_asset = models.Asset(**asset.model_dump())
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset

def update_asset(db: Session, db_asset: models.Asset, asset_in: schemas.AssetUpdate) -> models.Asset:
    update_data = asset_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_asset, key, value)
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset

def delete_asset(db: Session, asset_id: int) -> models.Asset:
    db_asset = db.query(models.Asset).filter(models.Asset.id == asset_id).first()
    if db_asset:
        db.delete(db_asset)
        db.commit()
    return db_asset

# --- Transaction CRUD ---
def get_transaction(db: Session, transaction_id: int) -> models.Transaction | None:
    return db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()

def get_transactions(db: Session, asset_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> list[models.Transaction]:
    query = db.query(models.Transaction).options(joinedload(models.Transaction.asset)).order_by(models.Transaction.transaction_date.desc())
    if asset_id is not None:
        query = query.filter(models.Transaction.asset_id == asset_id)
    return query.offset(skip).limit(limit).all()

def create_asset_transaction(db: Session, transaction: schemas.TransactionCreate) -> models.Transaction:
    db_transaction = models.Transaction(**transaction.model_dump())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def update_transaction(db: Session, db_transaction: models.Transaction, transaction_in: schemas.TransactionUpdate) -> models.Transaction:
    update_data = transaction_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_transaction, key, value)
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def delete_transaction(db: Session, transaction_id: int) -> models.Transaction:
    db_transaction = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if db_transaction:
        db.delete(db_transaction)
        db.commit()
    return db_transaction

def get_transactions_for_asset(db: Session, asset_id: int, skip: int = 0, limit: int = 100) -> list[models.Transaction]:
    return db.query(models.Transaction).filter(models.Transaction.asset_id == asset_id).offset(skip).limit(limit).all()

# --- Dividend CRUD ---
def get_dividend(db: Session, dividend_id: int) -> models.Dividend | None:
    return db.query(models.Dividend).filter(models.Dividend.id == dividend_id).first()


def get_dividends(
    db: Session,
    asset_id: int | None = None,
    payment_date: date | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[models.Dividend]:
    query = db.query(models.Dividend)
    if asset_id is not None:
        query = query.filter(models.Dividend.asset_id == asset_id)
    if payment_date is not None:
        query = query.filter(models.Dividend.payment_date == payment_date)
    return query.order_by(models.Dividend.payment_date.desc(), models.Dividend.id.desc()).offset(skip).limit(limit).all()

def create_asset_dividend(db: Session, dividend: schemas.DividendCreate) -> models.Dividend:
    db_dividend = models.Dividend(**dividend.model_dump())
    db.add(db_dividend)
    try:
        db.commit()
        db.refresh(db_dividend)
        return db_dividend
    except IntegrityError:
        db.rollback()
        existing_dividend = get_dividend_for_asset_on_date(
            db=db,
            asset_id=dividend.asset_id,
            payment_date=dividend.payment_date,
        )
        if existing_dividend is None:
            raise
        return existing_dividend

def update_dividend(db: Session, db_dividend: models.Dividend, dividend_in: schemas.DividendUpdate) -> models.Dividend:
    update_data = dividend_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_dividend, key, value)
    db.add(db_dividend)
    db.commit()
    db.refresh(db_dividend)
    return db_dividend

def delete_dividend(db: Session, dividend_id: int) -> models.Dividend:
    db_dividend = db.query(models.Dividend).filter(models.Dividend.id == dividend_id).first()
    if db_dividend:
        db.delete(db_dividend)
        db.commit()
    return db_dividend

def get_dividends_for_asset(db: Session, asset_id: int, skip: int = 0, limit: int = 100) -> list[models.Dividend]:
    return db.query(models.Dividend).filter(models.Dividend.asset_id == asset_id).offset(skip).limit(limit).all()


def get_latest_dividend_for_asset(db: Session, asset_id: int) -> models.Dividend | None:
    return (
        db.query(models.Dividend)
        .filter(models.Dividend.asset_id == asset_id)
        .order_by(models.Dividend.payment_date.desc(), models.Dividend.id.desc())
        .first()
    )


def get_dividend_for_asset_on_date(db: Session, asset_id: int, payment_date: date) -> models.Dividend | None:
    return (
        db.query(models.Dividend)
        .filter(models.Dividend.asset_id == asset_id, models.Dividend.payment_date == payment_date)
        .order_by(models.Dividend.id.desc())
        .first()
    )


# --- Asset Price Cache CRUD ---
def normalize_ticker(ticker: str) -> str:
    normalized_ticker = ticker.strip().upper()
    if not normalized_ticker:
        raise ValueError("Ticker must not be empty")
    return normalized_ticker


def get_cached_price(db: Session, ticker: str) -> models.AssetPriceCache | None:
    normalized_ticker = normalize_ticker(ticker)
    return db.query(models.AssetPriceCache).filter(models.AssetPriceCache.ticker == normalized_ticker).first()


def upsert_cached_price(
    db: Session,
    ticker: str,
    price: Decimal,
    source: str = "yfinance",
    fetched_at: datetime | None = None,
) -> models.AssetPriceCache:
    normalized_ticker = normalize_ticker(ticker)
    cached_price = models.AssetPriceCache(
        ticker=normalized_ticker,
        price=price,
        source=source,
        fetched_at=fetched_at or datetime.now(timezone.utc),
    )
    merged_cached_price = db.merge(cached_price)
    db.commit()
    db.refresh(merged_cached_price)
    return merged_cached_price


def is_cached_price_fresh(
    cached_price: models.AssetPriceCache | None,
    ttl_seconds: int = 3600,
    now: datetime | None = None,
) -> bool:
    if cached_price is None:
        return False

    current_time = now or datetime.now(timezone.utc)
    fetched_at = cached_price.fetched_at
    if fetched_at.tzinfo is None:
        fetched_at = fetched_at.replace(tzinfo=timezone.utc)

    age_seconds = (current_time - fetched_at).total_seconds()
    return age_seconds <= ttl_seconds

# --- Agent Action CRUD ---
def create_agent_action(db: Session, user_id: int, payload: schemas.AgentActionCreate) -> models.AgentAction:
    db_action = models.AgentAction(user_id=user_id, **payload.model_dump())
    db.add(db_action)
    db.commit()
    db.refresh(db_action)
    return db_action

def get_agent_actions(db: Session, user_id: int, limit: int = 100) -> list[models.AgentAction]:
    return (
        db.query(models.AgentAction)
        .filter(models.AgentAction.user_id == user_id)
        .order_by(models.AgentAction.created_at.desc())
        .limit(limit)
        .all()
    )
