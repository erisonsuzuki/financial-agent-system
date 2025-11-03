from unittest.mock import patch, MagicMock
from app.agents import market_data_agent
from decimal import Decimal

# Helper to create a mock yfinance history object
def create_mock_history(price: float | None):
    import pandas as pd
    if price is None:
        return pd.DataFrame({'Close': []})
    return pd.DataFrame({'Close': [price]})

@patch('yfinance.Ticker')
def test_get_current_price_success(mock_yf_ticker):
    # Arrange
    market_data_agent._cache.clear()
    mock_instance = MagicMock()
    mock_instance.history.return_value = create_mock_history(150.75)
    mock_yf_ticker.return_value = mock_instance
    
    # Act
    price = market_data_agent.get_current_price("AAPL")
    
    # Assert
    assert price == Decimal("150.75")
    mock_yf_ticker.assert_called_with("AAPL")
    mock_instance.history.assert_called_with(period="1d")

@patch('yfinance.Ticker')
def test_get_current_price_not_found(mock_yf_ticker):
    # Arrange
    market_data_agent._cache.clear()
    mock_instance = MagicMock()
    mock_instance.history.return_value = create_mock_history(None) # Empty DataFrame
    mock_yf_ticker.return_value = mock_instance
    
    # Act
    price = market_data_agent.get_current_price("INVALIDTICKER")
    
    # Assert
    assert price is None

@patch('yfinance.Ticker')
def test_get_current_price_caching(mock_yf_ticker):
    # Arrange
    market_data_agent._cache.clear()
    mock_instance = MagicMock()
    mock_instance.history.return_value = create_mock_history(200.0)
    mock_yf_ticker.return_value = mock_instance
    
    # Act: Call the function twice
    price1 = market_data_agent.get_current_price("GOOG")
    price2 = market_data_agent.get_current_price("GOOG")
    
    # Assert
    assert price1 == Decimal("200.00")
    assert price2 == Decimal("200.00")
    # The yfinance Ticker should only have been called ONCE due to caching
    mock_yf_ticker.assert_called_once_with("GOOG")
