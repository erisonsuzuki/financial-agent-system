from langchain.tools import tool
import httpx
from datetime import date
from decimal import Decimal
from typing import Annotated, Optional

@tool
def register_asset_position(
    ticker: Annotated[str, "The stock ticker symbol of the asset, for example, 'PETR4.SA'."],
    quantity: Annotated[float, "The total quantity of the asset the user currently holds."],
    average_price: Annotated[Decimal, "The user's average purchase price for this asset."]
) -> dict:
    """
    Registers a user's complete position for a single asset.
    It first creates the asset if it doesn't exist, then creates a single,
    synthetic initial transaction representing the user's provided average price and quantity.
    This tool should be called for each asset identified in the user's query.
    """
    base_url = "http://app:8000"
    
    # Step 1: Create the Asset
    asset_payload = {"ticker": ticker, "name": ticker, "asset_type": "STOCK"}
    try:
        with httpx.Client() as client:
            client.post(f"{base_url}/assets/", json=asset_payload, timeout=10.0)
    except httpx.HTTPStatusError as e:
        if e.response.status_code != 400: # 400 is expected for duplicates, which is ok
            return {"status": "error", "ticker": ticker, "message": f"Error creating asset: {e.response.text}"}
    
    # Step 2: Create the initial synthetic transaction
    transaction_payload = {
        "quantity": quantity,
        "price": str(average_price),
        "transaction_date": str(date.today())
    }
    try:
        with httpx.Client() as client:
            response = client.post(
                f"{base_url}/assets/{ticker}/transactions/",
                json=transaction_payload,
                timeout=10.0
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as e:
        return {"status": "error", "ticker": ticker, "message": f"Error creating transaction: {e.response.text}"}
        
    return {"status": "success", "ticker": ticker, "quantity": quantity, "average_price": str(average_price)}

@tool
def list_transactions_for_ticker(ticker: Annotated[str, "The ticker symbol to search for, e.g., 'PETR4.SA'."]) -> list[dict] | str:
    """
    Lists all transactions for a given asset ticker. Useful for finding a specific transaction ID before updating it.
    """
    base_url = "http://app:8000"
    try:
        with httpx.Client() as client:
            response = client.get(f"{base_url}/assets/{ticker}/transactions/", timeout=10.0)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return f"Error: {e.response.text}"

@tool
def update_transaction_by_id(
    transaction_id: Annotated[int, "The unique ID of the transaction to update."],
    new_quantity: Annotated[Optional[float], "The corrected quantity of the transaction."] = None,
    new_price: Annotated[Optional[Decimal], "The corrected price of the transaction."] = None,
    new_date: Annotated[Optional[str], "The corrected date of the transaction, in 'YYYY-MM-DD' format."] = None
) -> dict | str:
    """
    Updates one or more fields of a specific transaction identified by its ID.
    """
    base_url = "http://app:8000"
    update_payload = {}
    if new_quantity is not None:
        update_payload["quantity"] = new_quantity
    if new_price is not None:
        update_payload["price"] = str(new_price)
    if new_date is not None:
        update_payload["transaction_date"] = new_date

    if not update_payload:
        return "Error: At least one field (quantity, price, or date) must be provided to update."

    try:
        with httpx.Client() as client:
            response = client.put(f"{base_url}/transactions/{transaction_id}", json=update_payload, timeout=10.0)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return f"Error: {e.response.text}"

@tool
def delete_asset_by_ticker(ticker: Annotated[str, "The ticker symbol of the asset to delete, e.g., 'PETR4.SA'."]) -> str:
    """
    Deletes an asset and all its associated transactions and dividends from the portfolio.
    """
    base_url = "http://app:8000"
    # This tool is smarter: it finds the asset ID first, then calls the DELETE endpoint.
    try:
        with httpx.Client() as client:
            # Find the asset to get its ID
            get_response = client.get(f"{base_url}/assets/?ticker={ticker}", timeout=10.0) # Assuming a future query param
            get_response.raise_for_status()
            assets = get_response.json()
            if not assets:
                return f"Error: Asset with ticker {ticker} not found."
            asset_id = assets[0]["id"]
            
            # Delete the asset by its ID
            delete_response = client.delete(f"{base_url}/assets/{asset_id}", timeout=10.0)
            delete_response.raise_for_status()
            return f"Successfully deleted asset {ticker} and all its records."
    except httpx.HTTPStatusError as e:
        return f"Error: {e.response.text}"
