from decimal import Decimal

from sqlalchemy.orm import Session

from app import models, schemas


def get_asset_unscoped(db: Session, asset_id: int) -> models.Asset | None:
    return db.query(models.Asset).filter(models.Asset.id == asset_id).first()


def get_asset_by_ticker_unscoped(db: Session, ticker: str) -> models.Asset | None:
    return db.query(models.Asset).filter(models.Asset.ticker == ticker).first()


def get_asset(db: Session, asset_id: int, portfolio_id: int | None = None) -> models.Asset | None:
    if portfolio_id is None:
        raise ValueError("portfolio_id is required for scoped asset queries")
    query = db.query(models.Asset).filter(models.Asset.id == asset_id)
    query = query.filter(models.Asset.portfolio_id == portfolio_id)
    return query.first()


def get_asset_by_ticker(db: Session, ticker: str, portfolio_id: int | None = None) -> models.Asset | None:
    if portfolio_id is None:
        raise ValueError("portfolio_id is required for scoped asset queries")
    query = db.query(models.Asset).filter(models.Asset.ticker == ticker)
    query = query.filter(models.Asset.portfolio_id == portfolio_id)
    return query.first()


def get_assets(
    db: Session,
    ticker: str | None = None,
    skip: int = 0,
    limit: int = 100,
    portfolio_id: int | None = None,
) -> list[models.Asset]:
    if portfolio_id is None:
        raise ValueError("portfolio_id is required for scoped asset queries")
    query = db.query(models.Asset)
    query = query.filter(models.Asset.portfolio_id == portfolio_id)
    if ticker is not None:
        query = query.filter(models.Asset.ticker == ticker)
    return query.offset(skip).limit(limit).all()


def create_asset(db: Session, asset: schemas.AssetCreate, portfolio_id: int | None = None) -> models.Asset:
    if portfolio_id is None:
        from app.repositories.user_repository import get_or_create_legacy_portfolio

        portfolio_id = get_or_create_legacy_portfolio(db).id
    db_asset = models.Asset(**asset.model_dump(), portfolio_id=portfolio_id)
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


def delete_asset(db: Session, asset_id: int, portfolio_id: int | None = None) -> models.Asset | None:
    if portfolio_id is None:
        raise ValueError("portfolio_id is required for scoped asset deletion")
    db_asset = get_asset(db, asset_id=asset_id, portfolio_id=portfolio_id)
    if db_asset:
        db.delete(db_asset)
        db.commit()
    return db_asset


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
    fetched_at=None,
) -> models.AssetPriceCache:
    from datetime import datetime, timezone

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
    now=None,
) -> bool:
    from datetime import datetime, timezone

    if cached_price is None:
        return False

    current_time = now or datetime.now(timezone.utc)
    fetched_at = cached_price.fetched_at
    if fetched_at.tzinfo is None:
        fetched_at = fetched_at.replace(tzinfo=timezone.utc)

    age_seconds = (current_time - fetched_at).total_seconds()
    return age_seconds <= ttl_seconds
