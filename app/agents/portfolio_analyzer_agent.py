from sqlalchemy.orm import Session
from decimal import Decimal, ROUND_HALF_UP
from app import models, schemas, crud
from app.agents import market_data_agent

def analyze_asset(db: Session, asset: models.Asset) -> schemas.AssetAnalysis:
    """
    Performs a complete financial analysis for a single asset using Decimal for precision.
    """
    transactions = crud.get_transactions_for_asset(db=db, asset_id=asset.id, limit=10000)
    dividends = crud.get_dividends_for_asset(db=db, asset_id=asset.id, limit=10000)

    # Calculate portfolio state from transactions
    total_quantity = sum(Decimal(str(t.quantity)) for t in transactions)
    
    average_price = Decimal("0.00")
    total_invested = Decimal("0.00")

    if total_quantity > 0:
        buy_transactions = [t for t in transactions if t.quantity > 0]
        total_cost = sum(Decimal(str(t.quantity)) * t.price for t in buy_transactions)
        total_shares_bought = sum(Decimal(str(t.quantity)) for t in buy_transactions)
        
        if total_shares_bought > 0:
            average_price = (total_cost / total_shares_bought).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        
        total_invested = (total_quantity * average_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Calculate total dividends
    total_dividends_received = sum(d.amount_per_share * total_quantity for d in dividends).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Fetch current market data
    price_float = market_data_agent.get_current_price(ticker=asset.ticker)
    current_market_price = Decimal(str(price_float)) if price_float is not None else None

    # Calculate metrics that depend on market data
    current_market_value = None
    financial_return_value = None
    financial_return_percent = None

    if current_market_price is not None:
        current_market_value = (total_quantity * current_market_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if total_invested > 0:
            financial_return_value = current_market_value - total_invested
            financial_return_percent = ((financial_return_value / total_invested) * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return schemas.AssetAnalysis(
        ticker=asset.ticker,
        total_quantity=float(total_quantity),
        average_price=average_price,
        total_invested=total_invested,
        current_market_price=current_market_price,
        current_market_value=current_market_value,
        financial_return_value=financial_return_value,
        financial_return_percent=financial_return_percent,
        total_dividends_received=total_dividends_received,
    )
