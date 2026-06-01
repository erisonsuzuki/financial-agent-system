from datetime import date

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models, schemas
from app.repositories.asset_repository import get_asset_unscoped


def get_dividend(db: Session, dividend_id: int, portfolio_id: int | None = None) -> models.Dividend | None:
    if portfolio_id is None:
        raise ValueError("portfolio_id is required for scoped dividend queries")
    query = db.query(models.Dividend).filter(models.Dividend.id == dividend_id)
    query = query.filter(models.Dividend.portfolio_id == portfolio_id)
    return query.first()


def get_dividends(
    db: Session,
    asset_id: int | None = None,
    payment_date: date | None = None,
    skip: int = 0,
    limit: int = 100,
    portfolio_id: int | None = None,
) -> list[models.Dividend]:
    if portfolio_id is None:
        raise ValueError("portfolio_id is required for scoped dividend queries")
    query = db.query(models.Dividend)
    query = query.filter(models.Dividend.portfolio_id == portfolio_id)
    if asset_id is not None:
        query = query.filter(models.Dividend.asset_id == asset_id)
    if payment_date is not None:
        query = query.filter(models.Dividend.payment_date == payment_date)
    return query.order_by(models.Dividend.payment_date.desc(), models.Dividend.id.desc()).offset(skip).limit(limit).all()


def create_asset_dividend(db: Session, dividend: schemas.DividendCreate, portfolio_id: int | None = None) -> models.Dividend:
    if portfolio_id is None:
        asset = get_asset_unscoped(db, dividend.asset_id)
        if asset is None:
            raise ValueError("Asset not found")
        portfolio_id = asset.portfolio_id
    db_dividend = models.Dividend(**dividend.model_dump(), portfolio_id=portfolio_id)
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


def delete_dividend(db: Session, dividend_id: int, portfolio_id: int | None = None) -> models.Dividend | None:
    if portfolio_id is None:
        raise ValueError("portfolio_id is required for scoped dividend deletion")
    db_dividend = get_dividend(db, dividend_id=dividend_id, portfolio_id=portfolio_id)
    if db_dividend:
        db.delete(db_dividend)
        db.commit()
    return db_dividend


def get_dividends_for_asset(
    db: Session,
    asset_id: int,
    skip: int = 0,
    limit: int = 100,
    portfolio_id: int | None = None,
) -> list[models.Dividend]:
    if portfolio_id is None:
        raise ValueError("portfolio_id is required for scoped dividend queries")
    query = db.query(models.Dividend).filter(models.Dividend.asset_id == asset_id)
    query = query.filter(models.Dividend.portfolio_id == portfolio_id)
    return query.offset(skip).limit(limit).all()


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
