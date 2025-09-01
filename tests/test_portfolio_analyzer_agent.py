from sqlalchemy.orm import Session
from unittest.mock import patch
from datetime import date

from app.agents import portfolio_analyzer_agent
from app import crud, schemas

def test_analyze_asset_full_scenario(db_session: Session):
    # Arrange: Create the asset, transactions, and dividends in the test DB
    asset_schema = schemas.AssetCreate(ticker="TEST4.SA", name="Test Asset", asset_type="STOCK", sector="Testing")
    asset = crud.create_asset(db=db_session, asset=asset_schema)

    # Two buy transactions
    trans1_schema = schemas.TransactionCreate(quantity=100, price=10.00, transaction_date=date(2025, 1, 15))
    crud.create_asset_transaction(db=db_session, transaction=trans1_schema, asset_id=asset.id)
    
    trans2_schema = schemas.TransactionCreate(quantity=50, price=12.00, transaction_date=date(2025, 2, 20))
    crud.create_asset_transaction(db=db_session, transaction=trans2_schema, asset_id=asset.id)

    # One dividend payment
    div1_schema = schemas.DividendCreate(amount_per_share=0.50, payment_date=date(2025, 3, 10))
    crud.create_asset_dividend(db=db_session, dividend=div1_schema, asset_id=asset.id)

    # Mock the external price agent
    with patch('app.agents.market_data_agent.get_current_price') as mock_get_price:
        mock_get_price.return_value = 15.00  # Set a mock current market price

        # Act: Run the analysis
        analysis = portfolio_analyzer_agent.analyze_asset(db=db_session, asset=asset)

        # Assert: Check all calculations
        assert analysis.ticker == "TEST4.SA"
        assert analysis.total_quantity == 150.0 # 100 + 50
        
        # total_cost = (100 * 10) + (50 * 12) = 1000 + 600 = 1600
        # total_shares_bought = 100 + 50 = 150
        # average_price = 1600 / 150 = 10.666...
        assert round(analysis.average_price, 2) == 10.67
        
        # total_invested = total_quantity * average_price = 150 * 10.666... = 1600
        assert round(analysis.total_invested, 2) == 1600.00

        # total_dividends = amount_per_share * total_quantity = 0.50 * 150 = 75
        assert analysis.total_dividends_received == 75.0

        assert analysis.current_market_price == 15.00
        
        # current_market_value = total_quantity * current_price = 150 * 15 = 2250
        assert analysis.current_market_value == 2250.0
        
        # financial_return = market_value - total_invested = 2250 - 1600 = 650
        assert analysis.financial_return_value == 650.0
        
        # return_percent = (return_value / total_invested) * 100 = (650 / 1600) * 100 = 40.625
        assert round(analysis.financial_return_percent, 2) == 40.63
