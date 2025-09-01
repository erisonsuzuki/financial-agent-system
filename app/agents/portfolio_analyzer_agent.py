from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.orm import Session
from app import models, schemas, crud
from app.agents import market_data_agent

def analyze_asset(db: Session, asset: models.Asset) -> schemas.AssetAnalysis:
    """
    Performs a complete financial analysis for a single asset.
    """
    transactions = crud.get_transactions_for_asset(db=db, asset_id=asset.id, limit=1000)
    dividends = crud.get_dividends_for_asset(db=db, asset_id=asset.id, limit=1000)

    # Calculate portfolio state from transactions
    total_quantity = 0.0
    total_invested = 0.0
    for t in transactions:
        total_quantity += t.quantity # Assuming buys are positive, sells are negative
    
    if total_quantity > 0:
        # Calculate weighted average price only for buy transactions
        buy_transactions = [t for t in transactions if t.quantity > 0]
        total_cost = sum(t.quantity * t.price for t in buy_transactions)
        total_shares_bought = sum(t.quantity for t in buy_transactions)
        average_price = total_cost / total_shares_bought if total_shares_bought > 0 else 0.0
        # Total invested reflects the cost of the currently held shares
        total_invested = total_quantity * average_price
    else:
        average_price = 0.0
        total_invested = 0.0

    # Calculate total dividends
    total_dividends_received = sum(d.amount_per_share * total_quantity for d in dividends) # Simplified for now

    # Fetch current market data
    current_market_price = market_data_agent.get_current_price(ticker=asset.ticker)

    # Calculate metrics that depend on market data
    current_market_value = None
    financial_return_value = None
    financial_return_percent = None

    if current_market_price is not None:
        current_market_value = total_quantity * current_market_price
        if total_invested > 0:
            financial_return_value = Decimal(str(current_market_value)) - Decimal(str(total_invested))
            financial_return_percent = (financial_return_value / Decimal(str(total_invested)) * 100).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )

    return schemas.AssetAnalysis(
        ticker=asset.ticker,
        total_quantity=total_quantity,
        average_price=average_price,
        total_invested=total_invested,
        current_market_price=current_market_price,
        current_market_value=current_market_value,
        financial_return_value=financial_return_value,
        financial_return_percent=financial_return_percent,
        total_dividends_received=total_dividends_received,
    )
