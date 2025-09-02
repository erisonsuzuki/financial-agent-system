from langchain.tools import tool
import httpx
from datetime import date
from decimal import Decimal
from typing import Annotated, Optional, List, Any

def _parse_ticker_from_input(ticker_input: Any) -> str:
    """
    Sanitizes the ticker input, which might come as a string or a dict from the LLM.
    It also converts the ticker to uppercase for consistency.
    """
    if isinstance(ticker_input, dict):
        ticker_input = ticker_input.get("ticker", "")
    return str(ticker_input).strip().upper()

@tool
def register_asset_position(
    ticker: Annotated[str, "The stock ticker symbol, e.g., 'PETR4.SA'."],
    quantity: Annotated[float, "The total quantity the user holds."],
    average_price: Annotated[Decimal, "The user's average purchase price for this asset."]
) -> dict:
    """Registers a user's complete position for a single asset."""
    ticker = _parse_ticker_from_input(ticker)
    base_url = "http://app:8000"
    
    asset_payload = {"ticker": ticker, "name": ticker, "asset_type": "STOCK"}
    transaction_payload = {
        "quantity": quantity,
        "price": str(average_price),
        "transaction_date": str(date.today())
    }

    try:
        with httpx.Client() as client:
            # Step 1: Attempt to create the asset
            try:
                client.post(f"{base_url}/assets/", json=asset_payload, timeout=10.0)
            except httpx.HTTPStatusError as e:
                if e.response.status_code != 400: # 400 is expected for duplicates
                    raise e # Re-raise the error to be caught by the main block

            # Step 2: Fetch the Asset ID (newly created or already existing)
            asset_response = client.get(f"{base_url}/assets/?ticker={ticker}", timeout=10.0)
            asset_response.raise_for_status()
            assets = asset_response.json()
            if not assets:
                return {"status": "error", "ticker": ticker, "message": f"Asset with ticker {ticker} not found after creation attempt."}
            asset_id = assets[0]['id']

            # Step 3: Create the initial synthetic transaction with the Asset ID
            transaction_payload['asset_id'] = asset_id
            response = client.post(f"{base_url}/transactions/", json=transaction_payload, timeout=10.0)
            response.raise_for_status()

    except (httpx.HTTPStatusError, IndexError, KeyError) as e:
        return {"status": "error", "ticker": ticker, "message": f"An error occurred: {str(e)}"}
        
    return {"status": "success", "ticker": ticker, "quantity": quantity, "average_price": str(average_price)}

@tool
def list_all_transactions(limit: Annotated[Optional[int], "The maximum number of recent transactions to return."] = 100) -> List[dict] | str:
    """
    Lists recent transactions across all assets in the portfolio.
    Useful for general questions like 'what was my last transaction?'.
    """
    base_url = "http://app:8000"
    try:
        with httpx.Client() as client:
            response = client.get(f"{base_url}/transactions/?limit={limit}", timeout=10.0)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return f"Error: {e.response.text}"

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
