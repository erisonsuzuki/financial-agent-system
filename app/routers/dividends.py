from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas
from app.database import get_db

router = APIRouter(
    prefix="/dividends",
    tags=["Dividends"],
)

@router.post("/", response_model=schemas.Dividend, status_code=status.HTTP_201_CREATED)
def add_dividend(dividend: schemas.DividendCreate, db: Session = Depends(get_db)):
    # Check if asset exists
    db_asset = crud.get_asset(db, asset_id=dividend.asset_id)
    if not db_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return crud.create_asset_dividend(db=db, dividend=dividend)

@router.get("/{dividend_id}", response_model=schemas.Dividend)
def read_dividend(dividend_id: int, db: Session = Depends(get_db)):
    db_dividend = crud.get_dividend(db, dividend_id=dividend_id)
    if db_dividend is None:
        raise HTTPException(status_code=404, detail="Dividend not found")
    return db_dividend

@router.put("/{dividend_id}", response_model=schemas.Dividend)
def update_existing_dividend(dividend_id: int, dividend_in: schemas.DividendUpdate, db: Session = Depends(get_db)):
    db_dividend = crud.get_dividend(db, dividend_id=dividend_id)
    if not db_dividend:
        raise HTTPException(status_code=404, detail="Dividend not found")
    return crud.update_dividend(db=db, db_dividend=db_dividend, dividend_in=dividend_in)

@router.delete("/{dividend_id}", response_model=schemas.Dividend)
def delete_existing_dividend(dividend_id: int, db: Session = Depends(get_db)):
    db_dividend = crud.delete_dividend(db, dividend_id=dividend_id)
    if not db_dividend:
        raise HTTPException(status_code=404, detail="Dividend not found")
    return db_dividend
