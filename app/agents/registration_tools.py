from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Annotated, Optional, Any

from langchain.tools import tool

from app import crud, schemas
from app.agents import market_data_agent
from app.agents.toolkit_common import (
    normalize_decimal_input,
    parse_ticker_from_input,
    quantize_dividend_amount,
    require_context,
)


@tool
def register_asset_position(
    ticker: Annotated[str, "The stock ticker symbol, e.g., 'PETR4.SA'."],
    quantity: Annotated[float, "The total quantity the user holds."],
    average_price: Annotated[Any, "The user's average purchase price for this asset."],
) -> dict:
    """Register a full position for an asset in the active portfolio."""
    ticker = parse_ticker_from_input(ticker)
    try:
        parsed_average_price = normalize_decimal_input(average_price)
        context = require_context()
    except (InvalidOperation, ValueError, TypeError) as exc:
        return {"status": "error", "ticker": ticker, "message": str(exc)}

    db = context.db_session
    asset = crud.get_asset_by_ticker(db, ticker=ticker, portfolio_id=context.portfolio_id)
    if asset is None:
        asset = crud.create_asset(
            db=db,
            asset=schemas.AssetCreate(ticker=ticker, name=ticker, asset_type="STOCK"),
            portfolio_id=context.portfolio_id,
        )

    crud.create_asset_transaction(
        db=db,
        transaction=schemas.TransactionCreate(
            asset_id=asset.id,
            quantity=quantity,
            price=parsed_average_price,
            transaction_date=date.today(),
        ),
        portfolio_id=context.portfolio_id,
    )
    return {"status": "success", "ticker": ticker, "quantity": quantity, "average_price": str(parsed_average_price)}


@tool
def register_dividend(
    ticker: Annotated[str, "The stock ticker symbol, e.g., 'PETR4.SA'."],
    amount_per_share: Annotated[Optional[Decimal], "Dividend amount per share."] = None,
    total_amount: Annotated[Optional[Decimal], "Total dividend amount received."] = None,
    share_count: Annotated[Optional[Decimal], "Share count used to compute per-share amount."] = None,
    payment_date: Annotated[Optional[date], "Dividend payment date."] = None,
) -> dict:
    """Register or update a dividend by ticker in the active portfolio."""
    normalized_ticker = parse_ticker_from_input(ticker)
    if not normalized_ticker:
        return {"status": "error", "message": "Ticker is required.", "data": None}

    if amount_per_share is not None and total_amount is not None:
        return {"status": "error", "message": "Provide either amount_per_share or total_amount, not both.", "data": None}
    if amount_per_share is not None and amount_per_share <= 0:
        return {"status": "error", "message": "amount_per_share must be greater than zero.", "data": None}
    if total_amount is not None and total_amount <= 0:
        return {"status": "error", "message": "total_amount must be greater than zero.", "data": None}
    if share_count is not None and share_count <= 0:
        return {"status": "error", "message": "share_count must be greater than zero.", "data": None}

    computed_amount_per_share = amount_per_share
    fallback_payment_date = None

    if total_amount is not None:
        if share_count is None:
            return {"status": "error", "message": "share_count is required when total_amount is provided.", "data": None}
        computed_amount_per_share = total_amount / share_count

    if computed_amount_per_share is None:
        fallback_amount, fallback_date = market_data_agent.get_latest_dividend(normalized_ticker)
        if fallback_amount is None:
            return {
                "status": "error",
                "message": f"No dividend history found for ticker {normalized_ticker} and no amount was provided.",
                "data": None,
            }
        computed_amount_per_share = fallback_amount
        fallback_payment_date = fallback_date

    try:
        context = require_context()
        db = context.db_session
        asset = crud.get_asset_by_ticker(db, ticker=normalized_ticker, portfolio_id=context.portfolio_id)
        if asset is None:
            return {"status": "error", "message": f"Asset with ticker {normalized_ticker} not found.", "data": None}

        computed_amount_per_share = quantize_dividend_amount(computed_amount_per_share)
        effective_payment_date = payment_date or fallback_payment_date or date.today()
        existing = crud.get_dividends(
            db=db,
            asset_id=asset.id,
            payment_date=effective_payment_date,
            portfolio_id=context.portfolio_id,
            limit=1,
        )

        if existing:
            created_dividend = crud.update_dividend(
                db=db,
                db_dividend=existing[0],
                dividend_in=schemas.DividendUpdate(
                    amount_per_share=computed_amount_per_share,
                    payment_date=effective_payment_date,
                ),
            )
        else:
            created_dividend = crud.create_asset_dividend(
                db=db,
                dividend=schemas.DividendCreate(
                    asset_id=asset.id,
                    amount_per_share=computed_amount_per_share,
                    payment_date=effective_payment_date,
                ),
                portfolio_id=context.portfolio_id,
            )
    except ValueError as exc:
        return {"status": "error", "message": f"An error occurred: {exc}", "data": None}

    message = f"Dividend registered for {normalized_ticker}."
    if amount_per_share is None and total_amount is None:
        message = f"Dividend registered for {normalized_ticker} using latest yfinance amount_per_share."

    return {
        "status": "success",
        "message": message,
        "data": {
            "ticker": normalized_ticker,
            "asset_id": created_dividend.asset_id,
            "amount_per_share": str(created_dividend.amount_per_share),
            "payment_date": str(created_dividend.payment_date),
        },
    }
