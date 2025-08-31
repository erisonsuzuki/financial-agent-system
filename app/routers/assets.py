from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import crud, schemas
from app.database import get_db

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
