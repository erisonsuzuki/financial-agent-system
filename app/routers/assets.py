from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app import crud, schemas, models
from app.database import get_db
from app.agents import market_data_agent, portfolio_analyzer_agent
from app.dependencies import get_current_user, get_current_portfolio
from app.routers.utils import require_found

router = APIRouter(
    prefix="/assets",
    tags=["Assets"],
)


@router.post("/", response_model=schemas.Asset, status_code=status.HTTP_201_CREATED)
def create_new_asset(
    asset: schemas.AssetCreate,
    db: Session = Depends(get_db),
    portfolio: models.Portfolio = Depends(get_current_portfolio),
):
    db_asset = crud.get_asset_by_ticker(db, ticker=asset.ticker, portfolio_id=portfolio.id)
    if db_asset:
        raise HTTPException(status_code=400, detail="Asset with this ticker already exists")
    return crud.create_asset(db=db, asset=asset, portfolio_id=portfolio.id)


@router.get("/", response_model=List[schemas.Asset])
def list_assets(
    ticker: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    portfolio: models.Portfolio = Depends(get_current_portfolio),
):
    assets = crud.get_assets(db, ticker=ticker, skip=skip, limit=limit, portfolio_id=portfolio.id)
    return assets


@router.get("/summary", response_model=List[schemas.AssetSummary])
def list_assets_summary(
    refresh: bool = False,
    db: Session = Depends(get_db),
    portfolio: models.Portfolio = Depends(get_current_portfolio),
):
    assets = crud.get_assets(db, portfolio_id=portfolio.id)
    results: list[schemas.AssetSummary] = []

    for asset in assets:
        try:
            analysis = portfolio_analyzer_agent.analyze_asset(db=db, asset=asset, refresh=refresh)
            total_return_value = None
            total_return_percent = None

            if analysis.financial_return_value is not None:
                total_return_value = analysis.financial_return_value + analysis.total_dividends_received
                if analysis.total_invested > 0:
                    total_return_percent = ((total_return_value / analysis.total_invested) * Decimal("100")).quantize(Decimal("0.01"))

            results.append(
                schemas.AssetSummary(
                    id=asset.id,
                    name=asset.name,
                    ticker=asset.ticker,
                    units=analysis.total_quantity,
                    average_price=analysis.average_price,
                    current_price=analysis.current_market_price,
                    pl_value=analysis.financial_return_value,
                    pl_percent=analysis.financial_return_percent,
                    dividends=analysis.total_dividends_received,
                    total_return_value=total_return_value,
                    total_return_percent=total_return_percent,
                    price_fetched_at=analysis.fetched_at,
                    is_stale=analysis.is_stale,
                )
            )
        except Exception:
            results.append(
                schemas.AssetSummary(
                    id=asset.id,
                    name=asset.name,
                    ticker=asset.ticker,
                    units=0,
                    average_price=Decimal("0.00"),
                    current_price=None,
                    pl_value=None,
                    pl_percent=None,
                    dividends=Decimal("0.00"),
                    total_return_value=None,
                    total_return_percent=None,
                    price_fetched_at=None,
                    is_stale=False,
                    error="analysis_unavailable",
                )
            )

    return results


@router.get("/{asset_id}", response_model=schemas.Asset)
def read_asset(asset_id: int, db: Session = Depends(get_db), portfolio: models.Portfolio = Depends(get_current_portfolio)):
    db_asset = crud.get_asset(db, asset_id=asset_id, portfolio_id=portfolio.id)
    return require_found(db_asset, "Asset not found")


@router.put("/{asset_id}", response_model=schemas.Asset)
def update_existing_asset(asset_id: int, asset_in: schemas.AssetUpdate, db: Session = Depends(get_db), portfolio: models.Portfolio = Depends(get_current_portfolio)):
    db_asset = crud.get_asset(db, asset_id=asset_id, portfolio_id=portfolio.id)
    require_found(db_asset, "Asset not found")
    return crud.update_asset(db=db, db_asset=db_asset, asset_in=asset_in)


@router.delete("/{asset_id}", response_model=schemas.Asset)
def delete_existing_asset(asset_id: int, db: Session = Depends(get_db), portfolio: models.Portfolio = Depends(get_current_portfolio)):
    db_asset = crud.delete_asset(db, asset_id=asset_id, portfolio_id=portfolio.id)
    return require_found(db_asset, "Asset not found")


@router.get("/{ticker}/price", response_model=schemas.AssetPrice)
def get_asset_price(ticker: str, refresh: bool = False, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    price, is_stale = market_data_agent.get_current_price(ticker=ticker, db=db, force_refresh=refresh)
    if price is None:
        raise HTTPException(status_code=404, detail=f"Could not retrieve price for ticker {ticker}")
    cached = crud.get_cached_price(db, ticker)
    return schemas.AssetPrice(
        ticker=ticker,
        price=price,
        source=cached.source if cached is not None else "yfinance",
        fetched_at=cached.fetched_at if cached is not None else None,
        is_stale=is_stale,
    )


@router.get("/{ticker}/analysis", response_model=schemas.AssetAnalysis)
def get_asset_analysis(ticker: str, refresh: bool = False, db: Session = Depends(get_db), portfolio: models.Portfolio = Depends(get_current_portfolio)):
    db_asset = crud.get_asset_by_ticker(db, ticker=ticker, portfolio_id=portfolio.id)
    require_found(db_asset, "Asset not found")

    analysis = portfolio_analyzer_agent.analyze_asset(db=db, asset=db_asset, refresh=refresh)
    return analysis


@router.get("/{asset_id}/transactions", response_model=List[schemas.Transaction])
def list_transactions_for_asset(asset_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db), portfolio: models.Portfolio = Depends(get_current_portfolio)):
    db_asset = crud.get_asset(db, asset_id=asset_id, portfolio_id=portfolio.id)
    require_found(db_asset, "Asset not found")
    transactions = crud.get_transactions(db=db, asset_id=asset_id, skip=skip, limit=limit, portfolio_id=portfolio.id)
    return transactions
