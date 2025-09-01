from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas
from app.database import get_db
from app.agents import market_data_agent, portfolio_analyzer_agent

router = APIRouter(
    prefix="/assets",
    tags=["Assets"],
)

@router.post("/", response_model=schemas.Asset, status_code=status.HTTP_201_CREATED)
def create_new_asset(asset: schemas.AssetCreate, db: Session = Depends(get_db)):
    db_asset = crud.get_asset_by_ticker(db, ticker=asset.ticker)
    if db_asset:
        raise HTTPException(status_code=400, detail="Asset with this ticker already exists")
    return crud.create_asset(db=db, asset=asset)

@router.get("/", response_model=List[schemas.Asset])
def list_assets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    assets = crud.get_assets(db, skip=skip, limit=limit)
    return assets

@router.get("/{asset_id}", response_model=schemas.Asset)
def read_asset(asset_id: int, db: Session = Depends(get_db)):
    db_asset = crud.get_asset(db, asset_id=asset_id)
    if db_asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    return db_asset

@router.put("/{asset_id}", response_model=schemas.Asset)
def update_existing_asset(asset_id: int, asset_in: schemas.AssetUpdate, db: Session = Depends(get_db)):
    db_asset = crud.get_asset(db, asset_id=asset_id)
    if not db_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return crud.update_asset(db=db, db_asset=db_asset, asset_in=asset_in)

@router.delete("/{asset_id}", response_model=schemas.Asset)
def delete_existing_asset(asset_id: int, db: Session = Depends(get_db)):
    db_asset = crud.delete_asset(db, asset_id=asset_id)
    if not db_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return db_asset

@router.get("/{ticker}/price", response_model=schemas.AssetPrice)
def get_asset_price(ticker: str):
    price = market_data_agent.get_current_price(ticker=ticker)
    if price is None:
        raise HTTPException(status_code=404, detail=f"Could not retrieve price for ticker {ticker}")
    return schemas.AssetPrice(ticker=ticker, price=price)

@router.get("/{ticker}/analysis", response_model=schemas.AssetAnalysis)
def get_asset_analysis(ticker: str, db: Session = Depends(get_db)):
    db_asset = crud.get_asset_by_ticker(db, ticker=ticker)
    if db_asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    analysis = portfolio_analyzer_agent.analyze_asset(db=db, asset=db_asset)
    return analysis
