from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from app import crud, schemas, models
from app.database import get_db
from app.dependencies import get_current_portfolio
from app.routers.utils import require_found

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"],
)


@router.post("/", response_model=schemas.Transaction, status_code=status.HTTP_201_CREATED)
def add_transaction(
    transaction: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    portfolio: models.Portfolio = Depends(get_current_portfolio),
):
    db_asset = crud.get_asset(db, asset_id=transaction.asset_id, portfolio_id=portfolio.id)
    require_found(db_asset, "Asset not found")
    return crud.create_asset_transaction(db=db, transaction=transaction, portfolio_id=portfolio.id)


@router.get("/", response_model=List[schemas.Transaction])
def list_transactions(
    asset_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    portfolio: models.Portfolio = Depends(get_current_portfolio),
):
    transactions = crud.get_transactions(db=db, asset_id=asset_id, skip=skip, limit=limit, portfolio_id=portfolio.id)
    return transactions


@router.get("/{transaction_id}", response_model=schemas.Transaction)
def read_transaction(transaction_id: int, db: Session = Depends(get_db), portfolio: models.Portfolio = Depends(get_current_portfolio)):
    db_transaction = crud.get_transaction(db, transaction_id=transaction_id, portfolio_id=portfolio.id)
    return require_found(db_transaction, "Transaction not found")


@router.put("/{transaction_id}", response_model=schemas.Transaction)
def update_existing_transaction(
    transaction_id: int,
    transaction_in: schemas.TransactionUpdate,
    db: Session = Depends(get_db),
    portfolio: models.Portfolio = Depends(get_current_portfolio),
):
    db_transaction = crud.get_transaction(db, transaction_id=transaction_id, portfolio_id=portfolio.id)
    require_found(db_transaction, "Transaction not found")
    return crud.update_transaction(db=db, db_transaction=db_transaction, transaction_in=transaction_in)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_transaction(transaction_id: int, db: Session = Depends(get_db), portfolio: models.Portfolio = Depends(get_current_portfolio)):
    db_transaction = crud.delete_transaction(db, transaction_id=transaction_id, portfolio_id=portfolio.id)
    require_found(db_transaction, "Transaction not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
