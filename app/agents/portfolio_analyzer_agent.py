from sqlalchemy.orm import Session
from decimal import Decimal, ROUND_HALF_UP
from app import models, schemas, crud
from app.agents import market_data_agent


def _quantize_dividend_amount(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def _sync_latest_dividend_for_asset(db: Session, asset: models.Asset) -> None:
    external_amount, external_payment_date = market_data_agent.get_latest_dividend(asset.ticker)
    if external_amount is None or external_payment_date is None:
        return

    normalized_external_amount = _quantize_dividend_amount(external_amount)
    same_date_dividend = crud.get_dividend_for_asset_on_date(db, asset.id, external_payment_date)
    if same_date_dividend is not None:
        existing_amount = _quantize_dividend_amount(Decimal(str(same_date_dividend.amount_per_share)))
        if existing_amount != normalized_external_amount:
            crud.update_dividend(
                db=db,
                db_dividend=same_date_dividend,
                dividend_in=schemas.DividendUpdate(amount_per_share=normalized_external_amount),
            )
        return

    latest_dividend = crud.get_latest_dividend_for_asset(db, asset.id)
    if latest_dividend is not None and latest_dividend.payment_date >= external_payment_date:
        return

    crud.create_asset_dividend(
        db=db,
        dividend=schemas.DividendCreate(
            asset_id=asset.id,
            amount_per_share=normalized_external_amount,
            payment_date=external_payment_date,
        ),
    )

def analyze_asset(db: Session, asset: models.Asset, refresh: bool = False) -> schemas.AssetAnalysis:
    """
    Performs a complete financial analysis for a single asset using Decimal for precision.
    """
    transactions = crud.get_transactions(db=db, asset_id=asset.id, limit=10000)
    if refresh:
        _sync_latest_dividend_for_asset(db=db, asset=asset)
    dividends = crud.get_dividends_for_asset(db=db, asset_id=asset.id, limit=10000)

    total_quantity = sum(Decimal(str(t.quantity)) for t in transactions)
    
    average_price = Decimal("0.00")
    total_invested = Decimal("0.00")

    if total_quantity > 0:
        buy_transactions = [t for t in transactions if t.quantity > 0]
        total_cost = sum(
            (Decimal(str(t.quantity)) * Decimal(str(t.price)) for t in buy_transactions),
            Decimal("0.00"),
        )
        total_shares_bought = sum(Decimal(str(t.quantity)) for t in buy_transactions)
        
        if total_shares_bought > 0:
            average_price = (total_cost / total_shares_bought).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        
        total_invested = (total_quantity * average_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Note: This is a simplification. A more complex model would consider the quantity at the time of each dividend payment.
    dividends_total = sum(
        ((Decimal(str(d.amount_per_share)) * total_quantity) for d in dividends),
        Decimal("0.00"),
    )
    total_dividends_received = dividends_total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    current_market_price, is_stale = market_data_agent.get_current_price(
        ticker=asset.ticker,
        db=db,
        force_refresh=refresh,
    )
    cached_price = crud.get_cached_price(db, asset.ticker) if current_market_price is not None else None

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
        fetched_at=cached_price.fetched_at if cached_price is not None else None,
        is_stale=is_stale,
    )
