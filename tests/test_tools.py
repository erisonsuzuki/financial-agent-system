import os
import respx
import httpx
from app.agents.tools import list_transactions_for_ticker

BASE_URL = os.getenv("INTERNAL_API_URL", "http://app:8000")

@respx.mock
def test_list_transactions_for_ticker_success():
    # Arrange
    ticker = "XPML11"
    asset_id = 1
    asset_response = {
        "json": [
            {"id": asset_id, "ticker": ticker}
        ]
    }
    transactions_response = {
        "json": [
            {"id": 101, "asset_id": asset_id, "quantity": 10, "price": "100.00"},
            {"id": 102, "asset_id": asset_id, "quantity": 5, "price": "105.00"}
        ]
    }

    respx.get(f"{BASE_URL}/assets/?ticker={ticker}").mock(return_value=httpx.Response(200, json=asset_response["json"]))
    respx.get(f"{BASE_URL}/assets/{asset_id}/transactions").mock(return_value=httpx.Response(200, json=transactions_response["json"]))

    # Act
    result = list_transactions_for_ticker.invoke({"ticker": ticker})

    # Assert
    assert isinstance(result, list)
    assert len(result) == 2
    assert all(item["asset_id"] == asset_id for item in result)
