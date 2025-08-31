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
    client.post("/assets/", json=asset_data)

    # Now, read it
    response = client.get("/assets/MGLU3")
    data = response.json()
    assert response.status_code == 200
    assert data["ticker"] == "MGLU3"
    assert data["name"] == "MAGAZINE LUIZA"
    assert "id" in data

def test_read_asset_not_found(client: TestClient):
    response = client.get("/assets/NONEXISTENT")
    assert response.status_code == 404
    assert response.json() == {"detail": "Asset not found"}
