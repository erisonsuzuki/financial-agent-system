from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch
from datetime import datetime, timezone
from decimal import Decimal

from app import crud
from app import schemas

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


def test_get_asset_price_returns_refresh_metadata(client: TestClient, db_session):
    crud.upsert_cached_price(
        db_session,
        "AAPL",
        Decimal("170.00"),
        fetched_at=datetime.now(timezone.utc),
    )

    with patch("app.agents.market_data_agent.get_current_price") as mock_get_price:
        mock_get_price.return_value = (Decimal("170.00"), False)

        response = client.get("/assets/AAPL/price?refresh=true")

    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "AAPL"
    assert data["price"] == "170.00"
    assert data["source"] == "yfinance"
    assert data["is_stale"] is False
    assert data["fetched_at"] is not None
    mock_get_price.assert_called_once_with(ticker="AAPL", db=db_session, force_refresh=True)


def test_get_asset_analysis_passes_refresh_flag(client: TestClient, db_session):
    asset_data = {"ticker": "MSFT", "name": "MICROSOFT", "asset_type": "STOCK", "sector": "Technology"}
    response_post = client.post("/assets/", json=asset_data)
    assert response_post.status_code == 201

    with patch("app.agents.portfolio_analyzer_agent.analyze_asset") as mock_analyze:
        mock_analyze.return_value = {
            "ticker": "MSFT",
            "total_quantity": 0,
            "average_price": "0.00",
            "total_invested": "0.00",
            "current_market_price": None,
            "current_market_value": None,
            "financial_return_value": None,
            "financial_return_percent": None,
            "total_dividends_received": "0.00",
            "fetched_at": None,
            "is_stale": False,
        }

        response = client.get("/assets/MSFT/analysis?refresh=true")

    assert response.status_code == 200
    called_kwargs = mock_analyze.call_args.kwargs
    assert called_kwargs["db"] == db_session
    assert called_kwargs["refresh"] is True


def test_get_assets_summary_returns_bulk_analysis(client: TestClient):
    client.post("/assets/", json={"ticker": "AAPL", "name": "APPLE", "asset_type": "STOCK"})
    client.post("/assets/", json={"ticker": "MSFT", "name": "MICROSOFT", "asset_type": "STOCK"})

    def _mock_analysis(db, asset, refresh=False):
        if asset.ticker == "AAPL":
            raise RuntimeError("analysis failed")
        return schemas.AssetAnalysis(
            ticker=asset.ticker,
            total_quantity=10,
            average_price=Decimal("100.00"),
            total_invested=Decimal("1000.00"),
            current_market_price=Decimal("120.00"),
            current_market_value=Decimal("1200.00"),
            financial_return_value=Decimal("200.00"),
            financial_return_percent=Decimal("20.00"),
            total_dividends_received=Decimal("40.00"),
            fetched_at=None,
            is_stale=False,
        )

    with patch("app.agents.portfolio_analyzer_agent.analyze_asset", side_effect=_mock_analysis):
        response = client.get("/assets/summary?refresh=true")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    aapl = next(item for item in data if item["ticker"] == "AAPL")
    assert aapl["error"] == "analysis_unavailable"

    msft = next(item for item in data if item["ticker"] == "MSFT")
    assert msft["units"] == 10
    assert msft["average_price"] == "100.00"
    assert msft["dividends"] == "40.00"
    assert msft["total_return_value"] == "240.00"
    assert msft["total_return_percent"] == "24.00"


def test_assets_requires_authentication(no_auth_client: TestClient):
    response = no_auth_client.get("/assets/")
    assert response.status_code == 401
