import respx
import httpx
from decimal import Decimal
from app.agents.tools import register_asset_position
import pytest

@respx.mock
def test_register_asset_position_success():
    # Arrange: Mock the internal API calls that the tool will make
    asset_route = respx.post("http://app:8000/assets/").mock(return_value=httpx.Response(201))
    transaction_route = respx.post("http://app:8000/assets/TEST4.SA/transactions/").mock(return_value=httpx.Response(201))

    # Act
    result = register_asset_position.invoke({
        "ticker": "TEST4.SA",
        "quantity": 150,
        "average_price": Decimal("10.50")
    })

    # Assert
    assert asset_route.called
    assert transaction_route.called
    assert result["status"] == "success"
    assert result["ticker"] == "TEST4.SA"

@respx.mock
def test_register_asset_position_handles_existing_asset():
    # Arrange: Mock the API calls, simulating that the asset already exists (400)
    asset_route = respx.post("http://app:8000/assets/").mock(return_value=httpx.Response(400))
    transaction_route = respx.post("http://app:8000/assets/EXIST.SA/transactions/").mock(return_value=httpx.Response(201))

    # Act
    result = register_asset_position.invoke({
        "ticker": "EXIST.SA",
        "quantity": 50,
        "average_price": Decimal("25.00")
    })

    # Assert
    assert asset_route.called
    assert transaction_route.called
    assert result["status"] == "success"
