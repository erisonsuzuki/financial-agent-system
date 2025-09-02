from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from app import crud, schemas
from app.database import get_db

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"],
)

@router.post("/", response_model=schemas.Transaction, status_code=status.HTTP_201_CREATED)
def add_transaction(transaction: schemas.TransactionCreate, db: Session = Depends(get_db)):
    db_asset = crud.get_asset(db, asset_id=transaction.asset_id)
    if not db_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return crud.create_asset_transaction(db=db, transaction=transaction)

@router.get("/", response_model=List[schemas.Transaction])
def list_transactions(asset_id: Optional[int] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    transactions = crud.get_transactions(db=db, asset_id=asset_id, skip=skip, limit=limit)
    return transactions

@router.get("/{transaction_id}", response_model=schemas.Transaction)
def read_transaction(transaction_id: int, db: Session = Depends(get_db)):
    db_transaction = crud.get_transaction(db, transaction_id=transaction_id)
    if db_transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return db_transaction

@router.put("/{transaction_id}", response_model=schemas.Transaction)
def update_existing_transaction(transaction_id: int, transaction_in: schemas.TransactionUpdate, db: Session = Depends(get_db)):
    db_transaction = crud.get_transaction(db, transaction_id=transaction_id)
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return crud.update_transaction(db=db, db_transaction=db_transaction, transaction_in=transaction_in)

@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_transaction(transaction_id: int, db: Session = Depends(get_db)):
    db_transaction = crud.delete_transaction(db, transaction_id=transaction_id)
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
