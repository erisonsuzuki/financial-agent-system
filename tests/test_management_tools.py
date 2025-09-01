import respx
import httpx
from decimal import Decimal
from app.agents.tools import update_transaction_by_id

@respx.mock
def test_update_transaction_by_id_success():
    # Arrange
    transaction_id = 123
    expected_payload = {"price": "99.99"}
    update_route = respx.put(f"http://app:8000/transactions/{transaction_id}").mock(
        return_value=httpx.Response(200, json={"id": transaction_id, "price": "99.99"})
    )

    # Act
    result = update_transaction_by_id.invoke({
        "transaction_id": transaction_id,
        "new_price": Decimal("99.99")
    })

    # Assert
    assert update_route.called
    assert update_route.calls[0].request.content == httpx.Request(method="PUT", url="http://app:8000", json=expected_payload).content
    assert result["price"] == "99.99"
