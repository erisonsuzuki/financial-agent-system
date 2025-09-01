from fastapi.testclient import TestClient
from datetime import date

def test_create_transaction_for_asset(client: TestClient):
    # First, create an asset
    client.post("/assets/", json={"ticker": "VALE3", "name": "VALE", "asset_type": "STOCK"})

    # Create a transaction for that asset
    response = client.post(
        "/assets/VALE3/transactions/",
        json={"quantity": 100, "price": 61.50, "transaction_date": str(date.today())}
    )
    data = response.json()
    assert response.status_code == 201
    assert data["quantity"] == 100
    assert data["price"] == 61.50

def test_create_transaction_for_nonexistent_asset(client: TestClient):
    response = client.post(
        "/assets/NONEXISTENT/transactions/",
        json={"quantity": 100, "price": 10.0, "transaction_date": str(date.today())}
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Asset not found"}

def test_list_transactions_for_asset(client: TestClient):
    # Create an asset and some transactions
    client.post("/assets/", json={"ticker": "BBDC4", "name": "BRADESCO", "asset_type": "STOCK"})
    client.post("/assets/BBDC4/transactions/", json={"quantity": 50, "price": 13.00, "transaction_date": "2025-01-15"})
    client.post("/assets/BBDC4/transactions/", json={"quantity": 25, "price": 13.50, "transaction_date": "2025-02-20"})

    # List the transactions
    response = client.get("/assets/BBDC4/transactions/")
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 2
    assert data[0]["quantity"] == 50
    assert data[1]["quantity"] == 25
