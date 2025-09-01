from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas
from app.database import get_db

router = APIRouter(
    prefix="/assets/{ticker}/dividends",
    tags=["Dividends"],
)

@router.post("/", response_model=schemas.Dividend, status_code=status.HTTP_201_CREATED)
def add_dividend_for_asset(ticker: str, dividend: schemas.DividendCreate, db: Session = Depends(get_db)):
    db_asset = crud.get_asset_by_ticker(db, ticker=ticker)
    if not db_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return crud.create_asset_dividend(db=db, dividend=dividend, asset_id=db_asset.id)

@router.get("/", response_model=List[schemas.Dividend])
def list_dividends_for_asset(ticker: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    db_asset = crud.get_asset_by_ticker(db, ticker=ticker)
    if not db_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    dividends = crud.get_dividends_for_asset(db=db, asset_id=db_asset.id, skip=skip, limit=limit)
    return dividends
