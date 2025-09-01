from sqlalchemy.orm import Session
from . import models, schemas

# --- Asset CRUD ---
def get_asset_by_ticker(db: Session, ticker: str) -> models.Asset | None:
    return db.query(models.Asset).filter(models.Asset.ticker == ticker).first()

def create_asset(db: Session, asset: schemas.AssetCreate) -> models.Asset:
    db_asset = models.Asset(**asset.model_dump())
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset

# --- Transaction CRUD ---
def create_asset_transaction(db: Session, transaction: schemas.TransactionCreate, asset_id: int) -> models.Transaction:
    db_transaction = models.Transaction(**transaction.model_dump(), asset_id=asset_id)
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def get_transactions_for_asset(db: Session, asset_id: int, skip: int = 0, limit: int = 100) -> list[models.Transaction]:
    return db.query(models.Transaction).filter(models.Transaction.asset_id == asset_id).offset(skip).limit(limit).all()

# --- Dividend CRUD ---
def create_asset_dividend(db: Session, dividend: schemas.DividendCreate, asset_id: int) -> models.Dividend:
    db_dividend = models.Dividend(**dividend.model_dump(), asset_id=asset_id)
    db.add(db_dividend)
    db.commit()
    db.refresh(db_dividend)
    return db_dividend

def get_dividends_for_asset(db: Session, asset_id: int, skip: int = 0, limit: int = 100) -> list[models.Dividend]:
    return db.query(models.Dividend).filter(models.Dividend.asset_id == asset_id).offset(skip).limit(limit).all()
