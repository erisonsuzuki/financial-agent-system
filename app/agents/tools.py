from langchain.tools import tool
import httpx
from datetime import date
from decimal import Decimal
from typing import Annotated

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
