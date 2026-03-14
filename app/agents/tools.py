import os
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Annotated, Optional, List, Any

import httpx
from langchain.tools import tool
from app.agents import market_data_agent

BASE_API_URL = os.getenv("INTERNAL_API_URL", "http://app:8000")

def _parse_ticker_from_input(ticker_input: Any) -> str:
    """
    Sanitizes the ticker input, which might come as a string or a dict from the LLM.
    It also converts the ticker to uppercase for consistency.
    """
    if isinstance(ticker_input, dict):
        ticker_input = ticker_input.get("ticker", "")
    return str(ticker_input).strip().upper()


def _quantize_dividend_amount(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

@tool
def register_asset_position(
    ticker: Annotated[str, "The stock ticker symbol, e.g., 'PETR4.SA'."],
    quantity: Annotated[float, "The total quantity the user holds."],
    average_price: Annotated[Decimal, "The user's average purchase price for this asset."]
) -> dict:
    """Registers a user's complete position for a single asset."""
    ticker = _parse_ticker_from_input(ticker)
    base_url = BASE_API_URL
    
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
    base_url = BASE_API_URL
    try:
        with httpx.Client() as client:
            response = client.get(f"{base_url}/transactions/?limit={limit}", timeout=10.0)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return f"Error: {e.response.text}"


@tool
def register_dividend(
    ticker: Annotated[str, "The stock ticker symbol, e.g., 'PETR4.SA'."],
    amount_per_share: Annotated[Optional[Decimal], "Dividend amount per share."] = None,
    total_amount: Annotated[Optional[Decimal], "Total dividend amount received."] = None,
    share_count: Annotated[Optional[Decimal], "Share count used to compute per-share amount."] = None,
    payment_date: Annotated[Optional[date], "Dividend payment date."] = None,
) -> dict:
    """Registers a dividend for an existing asset by ticker."""
    normalized_ticker = _parse_ticker_from_input(ticker)
    if not normalized_ticker:
        return {"status": "error", "message": "Ticker is required.", "data": None}

    if amount_per_share is not None and total_amount is not None:
        return {
            "status": "error",
            "message": "Provide either amount_per_share or total_amount, not both.",
            "data": None,
        }

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
            return {
                "status": "error",
                "message": "share_count is required when total_amount is provided.",
                "data": None,
            }
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

    computed_amount_per_share = _quantize_dividend_amount(computed_amount_per_share)
    effective_payment_date = payment_date or fallback_payment_date or date.today()

    base_url = BASE_API_URL
    try:
        with httpx.Client() as client:
            asset_response = client.get(f"{base_url}/assets/?ticker={normalized_ticker}", timeout=10.0)
            asset_response.raise_for_status()
            assets = asset_response.json()
            if not assets:
                return {
                    "status": "error",
                    "message": f"Asset with ticker {normalized_ticker} not found.",
                    "data": None,
                }

            asset_id = assets[0]["id"]
            dividend_payload = {
                "asset_id": asset_id,
                "amount_per_share": str(computed_amount_per_share),
                "payment_date": str(effective_payment_date),
            }
            existing_response = client.get(
                f"{base_url}/dividends/?asset_id={asset_id}&payment_date={effective_payment_date}",
                timeout=10.0,
            )
            existing_response.raise_for_status()
            existing_dividends = existing_response.json()

            if existing_dividends:
                dividend_id = existing_dividends[0]["id"]
                update_payload = {
                    "amount_per_share": str(computed_amount_per_share),
                    "payment_date": str(effective_payment_date),
                }
                response = client.put(
                    f"{base_url}/dividends/{dividend_id}",
                    json=update_payload,
                    timeout=10.0,
                )
                response.raise_for_status()
            else:
                response = client.post(f"{base_url}/dividends/", json=dividend_payload, timeout=10.0)
                response.raise_for_status()
            created_dividend = response.json()
    except (httpx.HTTPStatusError, httpx.RequestError, KeyError, IndexError, ValueError) as e:
        return {"status": "error", "message": f"An error occurred: {str(e)}", "data": None}

    message = f"Dividend registered for {normalized_ticker}."
    if amount_per_share is None and total_amount is None:
        message = f"Dividend registered for {normalized_ticker} using latest yfinance amount_per_share."

    return {
        "status": "success",
        "message": message,
        "data": {
            "ticker": normalized_ticker,
            "asset_id": created_dividend.get("asset_id", asset_id),
            "amount_per_share": created_dividend.get("amount_per_share", str(computed_amount_per_share)),
            "payment_date": created_dividend.get("payment_date", str(effective_payment_date)),
        },
    }

@tool
def list_transactions_for_ticker(ticker: Annotated[str, "The ticker symbol to search for, e.g., 'PETR4.SA'."]) -> list[dict] | str:
    """
    Lists all transactions for a given asset ticker. Useful for finding a specific transaction ID before updating it.
    """
    base_url = BASE_API_URL
    ticker = _parse_ticker_from_input(ticker)
    try:
        with httpx.Client() as client:
            asset_response = client.get(f"{base_url}/assets/?ticker={ticker}", timeout=10.0)
            asset_response.raise_for_status()
            assets = asset_response.json()
            if not assets:
                return f"Error: Asset with ticker {ticker} not found."
            asset_id = assets[0]["id"]

            response = client.get(f"{base_url}/assets/{asset_id}/transactions", timeout=10.0)
            response.raise_for_status()
            return response.json()
    except (httpx.HTTPStatusError, KeyError, IndexError) as e:
        return f"Error: {str(e)}"

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
    base_url = BASE_API_URL
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
    base_url = BASE_API_URL
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

@tool
def get_full_portfolio_analysis() -> List[dict] | str:
    """
    Analyzes all assets in the portfolio and returns a list of their financial metrics.
    This should be the primary tool to get an overview of the entire portfolio before making a recommendation.
    """
    base_url = BASE_API_URL
    try:
        with httpx.Client() as client:
            # 1. Get all assets
            asset_response = client.get(f"{base_url}/assets/", timeout=10.0)
            asset_response.raise_for_status()
            assets = asset_response.json()
            if not assets:
                return "Error: No assets found in the portfolio to analyze."
            
            # 2. For each asset, get its detailed analysis
            full_analysis = []
            for asset in assets:
                ticker = asset.get("ticker")
                if not ticker:
                    continue
                
                analysis_response = client.get(f"{base_url}/assets/{ticker}/analysis", timeout=10.0)
                analysis_response.raise_for_status() # Will raise for 404s etc.
                full_analysis.append(analysis_response.json())
            
            return full_analysis
    except (httpx.HTTPStatusError, IndexError, KeyError) as e:
        return f"An unexpected error occurred during portfolio analysis: {str(e)}"

@tool
def classify_agent_request(
    question: Annotated[str, "The original natural-language request from the user."]
) -> dict:
    """
    Classifies the user request into registration, management, or analysis based on keyword heuristics.
    Acts as a backup signal for the router agent when the LLM needs structured hints.
    """
    normalized = question.lower()

    keywords = {
        "registration_agent": [
            "register",
            "add position",
            "new asset",
            "compr",
            "buy",
            "dividend",
            "dividends",
            "distribution",
            "cash distribution",
            "jcp",
        ],
        "management_agent": ["update", "correct", "sell", "delete", "adjust", "fix"],
        "analysis_agent": ["analysis", "invest", "recommendation", "where should", "analyze"],
    }

    scores = {agent: 0 for agent in keywords}
    for agent, tokens in keywords.items():
        for token in tokens:
            if token in normalized:
                scores[agent] += 1

    best_agent = max(scores, key=scores.get)
    best_score = scores[best_agent]
    total_hits = sum(scores.values()) or 1
    confidence = min(1.0, best_score / total_hits) if best_score else 0.33

    reasoning = (
        f"Matched keywords for {best_agent}: {best_score} hit(s)."
        if best_score
        else "No strong keyword matches; defaulting to analysis_agent."
    )

    return {
        "agent_name": best_agent if best_score else "analysis_agent",
        "confidence": round(confidence, 2),
        "reasoning": reasoning,
    }
