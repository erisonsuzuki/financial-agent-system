from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

def test_create_asset_success(client: TestClient):
    response = client.post(
        "/assets/",
        json={"ticker": "ITSA4", "name": "ITAU SA", "asset_type": "STOCK", "sector": "Financial"},
    )
    data = response.json()
    assert response.status_code == 201
    assert data["ticker"] == "ITSA4"
    assert data["name"] == "ITAU SA"
    assert "id" in data

def test_create_asset_duplicate_ticker(client: TestClient):
    # First, create an initial asset
    asset_data = {"ticker": "WEGE3", "name": "WEG SA", "asset_type": "STOCK", "sector": "Industrial"}
    response_1 = client.post("/assets/", json=asset_data)
    assert response_1.status_code == 201

    # Now, try to create it again
    response_2 = client.post("/assets/", json=asset_data)
    assert response_2.status_code == 400
    assert response_2.json() == {"detail": "Asset with this ticker already exists"}

def test_read_asset_success(client: TestClient):
    # First, create an asset to read
    asset_data = {"ticker": "MGLU3", "name": "MAGAZINE LUIZA", "asset_type": "STOCK"}
    response_post = client.post("/assets/", json=asset_data)
    asset_id = response_post.json()["id"]

    # Now, read it
    response = client.get(f"/assets/{asset_id}")
    data = response.json()
    assert response.status_code == 200
    assert data["ticker"] == "MGLU3"
    assert data["name"] == "MAGAZINE LUIZA"
    assert data["id"] == asset_id

def test_read_asset_not_found(client: TestClient):
    response = client.get("/assets/99999") # Assuming 99999 is a non-existent ID
    assert response.status_code == 404
    assert response.json() == {"detail": "Asset not found"}

def test_update_asset_success(client: TestClient):
    # First, create an asset
    asset_data = {"ticker": "PETR4", "name": "PETROBRAS", "asset_type": "STOCK", "sector": "Oil & Gas"}
    response_post = client.post("/assets/", json=asset_data)
    asset_id = response_post.json()["id"]

    # Now, update it
    update_data = {"name": "PETROBRAS S.A.", "sector": "Energy"}
    response_put = client.put(f"/assets/{asset_id}", json=update_data)
    data = response_put.json()
    assert response_put.status_code == 200
    assert data["name"] == "PETROBRAS S.A."
    assert data["sector"] == "Energy"
    assert data["id"] == asset_id

def test_update_asset_not_found(client: TestClient):
    update_data = {"name": "Non Existent Asset"}
    response = client.put("/assets/99999", json=update_data)
    assert response.status_code == 404
    assert response.json() == {"detail": "Asset not found"}

def test_delete_asset_success(client: TestClient):
    # First, create an asset
    asset_data = {"ticker": "VALE3", "name": "VALE", "asset_type": "STOCK", "sector": "Mining"}
    response_post = client.post("/assets/", json=asset_data)
    asset_id = response_post.json()["id"]

    # Now, delete it
    response_delete = client.delete(f"/assets/{asset_id}")
    data = response_delete.json()
    assert response_delete.status_code == 200
    assert data["id"] == asset_id

    # Verify it's deleted
    response_get = client.get(f"/assets/{asset_id}")
    assert response_get.status_code == 404

def test_delete_asset_not_found(client: TestClient):
    response = client.delete("/assets/99999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Asset not found"}
