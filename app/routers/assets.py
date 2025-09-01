from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
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

@router.get("/{ticker}", response_model=schemas.Asset)
def read_asset(ticker: str, db: Session = Depends(get_db)):
    db_asset = crud.get_asset_by_ticker(db, ticker=ticker)
    if db_asset is None:
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
