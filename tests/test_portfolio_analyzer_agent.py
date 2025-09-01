from sqlalchemy.orm import Session
from unittest.mock import patch
from datetime import date
from decimal import Decimal

from app.agents import portfolio_analyzer_agent
from app import crud, schemas

def test_analyze_asset_full_scenario_with_decimal(db_session: Session):
    # Arrange: Create the asset, transactions, and dividends
    asset_schema = schemas.AssetCreate(ticker="TEST4.SA", name="Test Asset", asset_type="STOCK", sector="Testing")
    asset = crud.create_asset(db=db_session, asset=asset_schema)

    trans1_schema = schemas.TransactionCreate(quantity=100, price=Decimal("10.00"), transaction_date=date(2025, 1, 15))
    crud.create_asset_transaction(db=db_session, transaction=trans1_schema, asset_id=asset.id)
    
    trans2_schema = schemas.TransactionCreate(quantity=50, price=Decimal("12.00"), transaction_date=date(2025, 2, 20))
    crud.create_asset_transaction(db=db_session, transaction=trans2_schema, asset_id=asset.id)

    div1_schema = schemas.DividendCreate(amount_per_share=Decimal("0.50"), payment_date=date(2025, 3, 10))
    crud.create_asset_dividend(db=db_session, dividend=div1_schema, asset_id=asset.id)

    # Mock the external price agent
    with patch('app.agents.market_data_agent.get_current_price') as mock_get_price:
        mock_get_price.return_value = 15.00  # Returns a float, our agent will convert to Decimal

        # Act: Run the analysis
        analysis = portfolio_analyzer_agent.analyze_asset(db=db_session, asset=asset)

        # Assert: Check all calculations using Decimal
        assert analysis.ticker == "TEST4.SA"
        assert analysis.total_quantity == 150.0
        assert analysis.average_price == Decimal("10.67")
        assert analysis.total_invested == Decimal("1600.50")
        assert analysis.total_dividends_received == Decimal("75.00")
        assert analysis.current_market_price == Decimal("15.00")
        assert analysis.current_market_value == Decimal("2250.00")
        assert analysis.financial_return_value == Decimal("649.50")
        assert analysis.financial_return_percent == Decimal("40.58")
