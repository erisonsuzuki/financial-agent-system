from sqlalchemy.orm import Session, joinedload

from app import models, schemas
from app.repositories.asset_repository import get_asset_unscoped


def get_transaction(db: Session, transaction_id: int, portfolio_id: int | None = None) -> models.Transaction | None:
    if portfolio_id is None:
        raise ValueError("portfolio_id is required for scoped transaction queries")
    query = db.query(models.Transaction).filter(models.Transaction.id == transaction_id)
    query = query.filter(models.Transaction.portfolio_id == portfolio_id)
    return query.first()


def get_transactions(
    db: Session,
    asset_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
    portfolio_id: int | None = None,
) -> list[models.Transaction]:
    if portfolio_id is None:
        raise ValueError("portfolio_id is required for scoped transaction queries")
    query = db.query(models.Transaction).options(joinedload(models.Transaction.asset)).order_by(models.Transaction.transaction_date.desc())
    query = query.filter(models.Transaction.portfolio_id == portfolio_id)
    if asset_id is not None:
        query = query.filter(models.Transaction.asset_id == asset_id)
    return query.offset(skip).limit(limit).all()


def create_asset_transaction(
    db: Session,
    transaction: schemas.TransactionCreate,
    portfolio_id: int | None = None,
) -> models.Transaction:
    if portfolio_id is None:
        asset = get_asset_unscoped(db, transaction.asset_id)
        if asset is None:
            raise ValueError("Asset not found")
        portfolio_id = asset.portfolio_id
    db_transaction = models.Transaction(**transaction.model_dump(), portfolio_id=portfolio_id)
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


def delete_transaction(db: Session, transaction_id: int, portfolio_id: int | None = None) -> models.Transaction | None:
    if portfolio_id is None:
        raise ValueError("portfolio_id is required for scoped transaction deletion")
    db_transaction = get_transaction(db, transaction_id=transaction_id, portfolio_id=portfolio_id)
    if db_transaction:
        db.delete(db_transaction)
        db.commit()
    return db_transaction


def get_transactions_for_asset(
    db: Session,
    asset_id: int,
    skip: int = 0,
    limit: int = 100,
    portfolio_id: int | None = None,
) -> list[models.Transaction]:
    if portfolio_id is None:
        raise ValueError("portfolio_id is required for scoped transaction queries")
    query = db.query(models.Transaction).filter(models.Transaction.asset_id == asset_id)
    query = query.filter(models.Transaction.portfolio_id == portfolio_id)
    return query.offset(skip).limit(limit).all()
