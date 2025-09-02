from fastapi.testclient import TestClient
from datetime import date
from decimal import Decimal
from app import crud, schemas

def test_create_transaction_success(client: TestClient, db_session):
    # Arrange: Create an asset to link to
    asset = crud.create_asset(db_session, schemas.AssetCreate(ticker="VALE3", name="VALE", asset_type="STOCK"))
    
    # Act: Create a transaction
    response = client.post(
        "/transactions/",
        json={"asset_id": asset.id, "quantity": 100, "price": "61.50", "transaction_date": str(date.today())}
    )
    data = response.json()

    # Assert
    assert response.status_code == 201
    assert data["quantity"] == 100
    assert data["price"] == "61.50"
    assert data["asset"]["ticker"] == "VALE3" # Check the nested object

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

def test_delete_transaction_success(client: TestClient, db_session):
    # Arrange: Create an asset and a transaction to delete
    asset = crud.create_asset(db_session, schemas.AssetCreate(ticker="PETR4", name="PETROBRAS", asset_type="STOCK"))
    transaction = crud.create_asset_transaction(db_session, schemas.TransactionCreate(asset_id=asset.id, quantity=50, price=Decimal("30.00"), transaction_date="2025-01-01"))

    # Act: Delete the transaction
    response = client.delete(f"/transactions/{transaction.id}")

    # Assert: Deletion was successful and returns no content
    assert response.status_code == 204

    # Assert: Verify the transaction is actually gone
    get_response = client.get(f"/transactions/{transaction.id}")
    assert get_response.status_code == 404

def test_delete_transaction_not_found(client: TestClient):
    response = client.delete("/transactions/99999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Transaction not found"}

def test_list_all_transactions(client: TestClient, db_session):
    # Arrange: Create multiple assets and transactions
    asset1 = crud.create_asset(db_session, schemas.AssetCreate(ticker="ASSET1", name="Asset One", asset_type="STOCK"))
    asset2 = crud.create_asset(db_session, schemas.AssetCreate(ticker="ASSET2", name="Asset Two", asset_type="STOCK"))
    
    crud.create_asset_transaction(db_session, schemas.TransactionCreate(asset_id=asset1.id, quantity=10, price=Decimal("10.00"), transaction_date="2025-01-01"))
    crud.create_asset_transaction(db_session, schemas.TransactionCreate(asset_id=asset2.id, quantity=20, price=Decimal("20.00"), transaction_date="2025-01-02"))

    # Act
    response = client.get("/transactions/")
    data = response.json()

    # Assert
    assert response.status_code == 200
    assert len(data) == 2
    assert data[0]["price"] == "20.00" # Sorted by date descending
    assert data[1]["price"] == "10.00"
