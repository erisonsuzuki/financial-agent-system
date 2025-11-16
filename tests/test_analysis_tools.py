import os
import respx
import httpx
from app.agents.tools import get_full_portfolio_analysis

BASE_URL = os.getenv("INTERNAL_API_URL", "http://app:8000")

@respx.mock
def test_get_full_portfolio_analysis_success():
    # Arrange: Mock all the API calls this tool will make
    
    # 1. Mock the call to get all assets
    respx.get(f"{BASE_URL}/assets/").mock(
        return_value=httpx.Response(200, json=[
            {"id": 1, "ticker": "PETR4.SA"},
            {"id": 2, "ticker": "VALE3.SA"}
        ])
    )
    
    # 2. Mock the analysis call for the first asset
    respx.get(f"{BASE_URL}/assets/PETR4.SA/analysis").mock(
        return_value=httpx.Response(200, json={
            "ticker": "PETR4.SA", 
            "financial_return_percent": "10.50"
        })
    )
    
    # 3. Mock the analysis call for the second asset
    respx.get(f"{BASE_URL}/assets/VALE3.SA/analysis").mock(
        return_value=httpx.Response(200, json={
            "ticker": "VALE3.SA",
            "financial_return_percent": "-5.20"
        })
    )

    # Act
    result = get_full_portfolio_analysis.invoke({})

    # Assert
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["ticker"] == "PETR4.SA"
    assert result[1]["ticker"] == "VALE3.SA"
    assert result[1]["financial_return_percent"] == "-5.20"

@respx.mock
def test_get_full_portfolio_analysis_no_assets():
    # Arrange
    respx.get(f"{BASE_URL}/assets/").mock(return_value=httpx.Response(200, json=[]))

    # Act
    result = get_full_portfolio_analysis.invoke({})

    # Assert
    assert "Error: No assets found" in result
