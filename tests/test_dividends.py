from fastapi.testclient import TestClient
from datetime import date

def test_create_dividend_success(client: TestClient):
    # First, create an asset
    asset_data = {"ticker": "ITUB4", "name": "ITAÚ UNIBANCO", "asset_type": "STOCK", "sector": "Financial"}
    response_asset = client.post("/assets/", json=asset_data)
    asset_id = response_asset.json()["id"]

    # Create a dividend for that asset
    dividend_data = {"asset_id": asset_id, "amount_per_share": "0.5120", "payment_date": str(date.today())}
    response = client.post("/dividends/", json=dividend_data)
    data = response.json()
    assert response.status_code == 201
    assert data["amount_per_share"] == "0.5120"
    assert data["asset_id"] == asset_id
    assert "id" in data

def test_create_dividend_for_nonexistent_asset(client: TestClient):
    dividend_data = {"asset_id": 99999, "amount_per_share": "1.00", "payment_date": str(date.today())}
    response = client.post("/dividends/", json=dividend_data)
    assert response.status_code == 404
    assert response.json() == {"detail": "Asset not found"}

def test_read_dividend_success(client: TestClient):
    # First, create an asset
    asset_data = {"ticker": "BBDC4", "name": "BRADESCO", "asset_type": "STOCK", "sector": "Financial"}
    response_asset = client.post("/assets/", json=asset_data)
    asset_id = response_asset.json()["id"]

    # Create a dividend
    dividend_data = {"asset_id": asset_id, "amount_per_share": "0.10", "payment_date": "2023-01-01"}
    response_post = client.post("/dividends/", json=dividend_data)
    dividend_id = response_post.json()["id"]

    # Read the dividend
    response_get = client.get(f"/dividends/{dividend_id}")
    data = response_get.json()
    assert response_get.status_code == 200
    assert data["id"] == dividend_id
    assert data["amount_per_share"] == "0.1000"

def test_read_dividend_not_found(client: TestClient):
    response = client.get("/dividends/99999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Dividend not found"}

def test_update_dividend_success(client: TestClient):
    # First, create an asset
    asset_data = {"ticker": "ABEV3", "name": "AMBEV", "asset_type": "STOCK", "sector": "Beverages"}
    response_asset = client.post("/assets/", json=asset_data)
    asset_id = response_asset.json()["id"]

    # Create a dividend
    dividend_data = {"asset_id": asset_id, "amount_per_share": "0.15", "payment_date": "2023-01-01"}
    response_post = client.post("/dividends/", json=dividend_data)
    dividend_id = response_post.json()["id"]

    # Update the dividend
    update_data = {"amount_per_share": "0.20", "payment_date": "2023-01-02"}
    response_put = client.put(f"/dividends/{dividend_id}", json=update_data)
    data = response_put.json()
    assert response_put.status_code == 200
    assert data["id"] == dividend_id
    assert data["amount_per_share"] == "0.2000"
    assert data["payment_date"] == "2023-01-02"

def test_update_dividend_not_found(client: TestClient):
    update_data = {"amount_per_share": "0.10"}
    response = client.put("/dividends/99999", json=update_data)
    assert response.status_code == 404
    assert response.json() == {"detail": "Dividend not found"}

def test_delete_dividend_success(client: TestClient):
    # First, create an asset
    asset_data = {"ticker": "FLRY3", "name": "FLEURY", "asset_type": "STOCK", "sector": "Healthcare"}
    response_asset = client.post("/assets/", json=asset_data)
    asset_id = response_asset.json()["id"]

    # Create a dividend
    dividend_data = {"asset_id": asset_id, "amount_per_share": "0.05", "payment_date": "2023-01-01"}
    response_post = client.post("/dividends/", json=dividend_data)
    dividend_id = response_post.json()["id"]

    # Delete the dividend
    response_delete = client.delete(f"/dividends/{dividend_id}")
    data = response_delete.json()
    assert response_delete.status_code == 200
    assert data["id"] == dividend_id

    # Verify it's deleted
    response_get = client.get(f"/dividends/{dividend_id}")
    assert response_get.status_code == 404

def test_delete_dividend_not_found(client: TestClient):
    response = client.delete("/dividends/99999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Dividend not found"}
