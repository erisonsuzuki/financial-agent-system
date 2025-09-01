from fastapi.testclient import TestClient
from datetime import date

def test_create_dividend_for_asset(client: TestClient):
    # First, create an asset
    client.post("/assets/", json={"ticker": "ITUB3", "name": "ITAU", "asset_type": "STOCK"})

    # Create a dividend for that asset
    response = client.post(
        "/assets/ITUB3/dividends/",
        json={"amount_per_share": 0.15, "payment_date": str(date.today())}
    )
    data = response.json()
    assert response.status_code == 201
    assert data["amount_per_share"] == 0.15

def test_create_dividend_for_nonexistent_asset(client: TestClient):
    response = client.post(
        "/assets/NONEXISTENT/dividends/",
        json={"amount_per_share": 0.50, "payment_date": str(date.today())}
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Asset not found"}

def test_list_dividends_for_asset(client: TestClient):
    # Create an asset and some dividends
    client.post("/assets/", json={"ticker": "PETR4", "name": "PETROBRAS", "asset_type": "STOCK"})
    client.post("/assets/PETR4/dividends/", json={"amount_per_share": 0.25, "payment_date": "2025-03-01"})
    client.post("/assets/PETR4/dividends/", json={"amount_per_share": 0.30, "payment_date": "2025-06-01"})

    # List the dividends
    response = client.get("/assets/PETR4/dividends/")
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 2
    assert data[0]["amount_per_share"] == 0.25
    assert data[1]["amount_per_share"] == 0.30
