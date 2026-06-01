from decimal import Decimal
from typing import Annotated, Optional, List

from langchain.tools import tool

from app import crud, schemas
from app.agents.toolkit_common import parse_ticker_from_input, require_context


@tool
def list_all_transactions(limit: Annotated[Optional[int], "The maximum number of recent transactions to return."] = 100) -> List[dict] | str:
    """List recent transactions for the active portfolio."""
    try:
        context = require_context()
        transactions = crud.get_transactions(context.db_session, limit=limit or 100, portfolio_id=context.portfolio_id)
        return [
            {
                "id": tx.id,
                "asset_id": tx.asset_id,
                "ticker": tx.asset.ticker if tx.asset else None,
                "quantity": tx.quantity,
                "price": str(tx.price),
                "transaction_date": str(tx.transaction_date),
            }
            for tx in transactions
        ]
    except ValueError as exc:
        return f"Error: {exc}"


@tool
def list_transactions_for_ticker(ticker: Annotated[str, "The ticker symbol to search for, e.g., 'PETR4.SA'."]) -> list[dict] | str:
    """List transactions for a specific ticker in the active portfolio."""
    ticker = parse_ticker_from_input(ticker)
    try:
        context = require_context()
        asset = crud.get_asset_by_ticker(context.db_session, ticker=ticker, portfolio_id=context.portfolio_id)
        if not asset:
            return f"Error: Asset with ticker {ticker} not found."
        transactions = crud.get_transactions_for_asset(
            context.db_session,
            asset_id=asset.id,
            portfolio_id=context.portfolio_id,
        )
        return [
            {
                "id": tx.id,
                "asset_id": tx.asset_id,
                "quantity": tx.quantity,
                "price": str(tx.price),
                "transaction_date": str(tx.transaction_date),
            }
            for tx in transactions
        ]
    except ValueError as exc:
        return f"Error: {exc}"


@tool
def update_transaction_by_id(
    transaction_id: Annotated[int, "The unique ID of the transaction to update."],
    new_quantity: Annotated[Optional[float], "The corrected quantity of the transaction."] = None,
    new_price: Annotated[Optional[Decimal], "The corrected price of the transaction."] = None,
    new_date: Annotated[Optional[str], "The corrected date of the transaction, in 'YYYY-MM-DD' format."] = None,
) -> dict | str:
    """Update transaction fields by ID in the active portfolio."""
    update_payload = {}
    if new_quantity is not None:
        update_payload["quantity"] = new_quantity
    if new_price is not None:
        update_payload["price"] = new_price
    if new_date is not None:
        update_payload["transaction_date"] = new_date
    if not update_payload:
        return "Error: At least one field (quantity, price, or date) must be provided to update."

    try:
        context = require_context()
        db_transaction = crud.get_transaction(context.db_session, transaction_id=transaction_id, portfolio_id=context.portfolio_id)
        if db_transaction is None:
            return "Error: Transaction not found."
        updated = crud.update_transaction(
            db=context.db_session,
            db_transaction=db_transaction,
            transaction_in=schemas.TransactionUpdate(**update_payload),
        )
        return {
            "id": updated.id,
            "asset_id": updated.asset_id,
            "quantity": updated.quantity,
            "price": str(updated.price),
            "transaction_date": str(updated.transaction_date),
        }
    except ValueError as exc:
        return f"Error: {exc}"


@tool
def delete_asset_by_ticker(ticker: Annotated[str, "The ticker symbol of the asset to delete, e.g., 'PETR4.SA'."]) -> str:
    """Delete an asset by ticker in the active portfolio."""
    try:
        ticker = parse_ticker_from_input(ticker)
        context = require_context()
        asset = crud.get_asset_by_ticker(context.db_session, ticker=ticker, portfolio_id=context.portfolio_id)
        if asset is None:
            return f"Error: Asset with ticker {ticker} not found."
        crud.delete_asset(context.db_session, asset_id=asset.id, portfolio_id=context.portfolio_id)
        return f"Successfully deleted asset {ticker} and all its records."
    except ValueError as exc:
        return f"Error: {exc}"
