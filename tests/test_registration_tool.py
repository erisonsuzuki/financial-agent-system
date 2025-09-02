import respx
import httpx
from decimal import Decimal
from app.agents.tools import register_asset_position

@respx.mock
def test_register_asset_position_success():
    # Arrange: Mock all three internal API calls that the tool will make
    ticker = "TEST4.SA"
    asset_id = 1
    
    # 1. Mock the POST to create the asset
    respx.post("http://app:8000/assets/").mock(return_value=httpx.Response(201))
    
    # 2. Mock the GET to find the asset's ID
    respx.get(f"http://app:8000/assets/?ticker={ticker}").mock(
        return_value=httpx.Response(200, json=[{"id": asset_id, "ticker": ticker}])
    )
    
    # 3. Mock the POST to create the transaction
    respx.post("http://app:8000/transactions/").mock(return_value=httpx.Response(201))

    # Act
    result = register_asset_position.invoke({
        "ticker": ticker,
        "quantity": 150,
        "average_price": Decimal("10.50")
    })

    # Assert
    assert result["status"] == "success"
    assert result["ticker"] == ticker

@respx.mock
def test_register_asset_position_handles_existing_asset():
    # Arrange: Mock the API calls, simulating that the asset already exists (400)
    ticker = "EXIST.SA"
    asset_id = 2

    # 1. Mock the POST to create the asset (simulating it already exists)
    respx.post("http://app:8000/assets/").mock(return_value=httpx.Response(400))
    
    # 2. Mock the GET to find the asset's ID
    respx.get(f"http://app:8000/assets/?ticker={ticker}").mock(
        return_value=httpx.Response(200, json=[{"id": asset_id, "ticker": ticker}])
    )

    # 3. Mock the POST to create the transaction
    respx.post("http://app:8000/transactions/").mock(return_value=httpx.Response(201))

    # Act
    result = register_asset_position.invoke({
        "ticker": ticker,
        "quantity": 50,
        "average_price": Decimal("25.00")
    })

    # Assert
    assert result["status"] == "success"
