from fastapi.testclient import TestClient
from datetime import date

def test_create_transaction_success(client: TestClient):
    # First, create an asset
    asset_data = {"ticker": "VALE3", "name": "VALE", "asset_type": "STOCK", "sector": "Mining"}
    response_asset = client.post("/assets/", json=asset_data)
    asset_id = response_asset.json()["id"]

    # Create a transaction for that asset
    transaction_data = {"asset_id": asset_id, "quantity": 100, "price": "61.50", "transaction_date": str(date.today())}
    response = client.post("/transactions/", json=transaction_data)
    data = response.json()
    assert response.status_code == 201
    assert data["quantity"] == 100
    assert data["price"] == "61.50"
    assert data["asset_id"] == asset_id
    assert "id" in data

def test_create_transaction_for_nonexistent_asset(client: TestClient):
    transaction_data = {"asset_id": 99999, "quantity": 100, "price": "10.00", "transaction_date": str(date.today())}
    response = client.post("/transactions/", json=transaction_data)
    assert response.status_code == 404
    assert response.json() == {"detail": "Asset not found"}

def test_read_transaction_success(client: TestClient):
    # First, create an asset
    asset_data = {"ticker": "PETR4", "name": "PETROBRAS", "asset_type": "STOCK", "sector": "Oil & Gas"}
    response_asset = client.post("/assets/", json=asset_data)
    asset_id = response_asset.json()["id"]

    # Create a transaction
    transaction_data = {"asset_id": asset_id, "quantity": 50, "price": "30.00", "transaction_date": "2023-01-01"}
    response_post = client.post("/transactions/", json=transaction_data)
    transaction_id = response_post.json()["id"]

    # Read the transaction
    response_get = client.get(f"/transactions/{transaction_id}")
    data = response_get.json()
    assert response_get.status_code == 200
    assert data["id"] == transaction_id
    assert data["quantity"] == 50
    assert data["price"] == "30.00"

def test_read_transaction_not_found(client: TestClient):
    response = client.get("/transactions/99999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Transaction not found"}

def test_update_transaction_success(client: TestClient):
    # First, create an asset
    asset_data = {"ticker": "ITSA4", "name": "ITAU SA", "asset_type": "STOCK", "sector": "Financial"}
    response_asset = client.post("/assets/", json=asset_data)
    asset_id = response_asset.json()["id"]

    # Create a transaction
    transaction_data = {"asset_id": asset_id, "quantity": 100, "price": "10.00", "transaction_date": "2023-01-01"}
    response_post = client.post("/transactions/", json=transaction_data)
    transaction_id = response_post.json()["id"]

    # Update the transaction
    update_data = {"quantity": 120, "price": "10.50", "transaction_date": "2023-01-02"}
    response_put = client.put(f"/transactions/{transaction_id}", json=update_data)
    data = response_put.json()
    assert response_put.status_code == 200
    assert data["id"] == transaction_id
    assert data["quantity"] == 120
    assert data["price"] == "10.50"
    assert data["transaction_date"] == "2023-01-02"

def test_update_transaction_not_found(client: TestClient):
    update_data = {"quantity": 10}
    response = client.put("/transactions/99999", json=update_data)
    assert response.status_code == 404
    assert response.json() == {"detail": "Transaction not found"}

def test_delete_transaction_success(client: TestClient):
    # First, create an asset
    asset_data = {"ticker": "BBDC4", "name": "BRADESCO", "asset_type": "STOCK", "sector": "Financial"}
    response_asset = client.post("/assets/", json=asset_data)
    asset_id = response_asset.json()["id"]

    # Create a transaction
    transaction_data = {"asset_id": asset_id, "quantity": 50, "price": "15.00", "transaction_date": "2023-01-01"}
    response_post = client.post("/transactions/", json=transaction_data)
    transaction_id = response_post.json()["id"]

    # Delete the transaction
    response_delete = client.delete(f"/transactions/{transaction_id}")
    data = response_delete.json()
    assert response_delete.status_code == 200
    assert data["id"] == transaction_id

    # Verify it's deleted
    response_get = client.get(f"/transactions/{transaction_id}")
    assert response_get.status_code == 404

def test_delete_transaction_not_found(client: TestClient):
    response = client.delete("/transactions/99999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Transaction not found"}
