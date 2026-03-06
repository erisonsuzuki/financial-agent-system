from unittest.mock import patch, MagicMock
from app.agents import market_data_agent
from decimal import Decimal
from app import crud

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
    price, is_stale = market_data_agent.get_current_price("AAPL")
    
    # Assert
    assert price == Decimal("150.75")
    assert is_stale is False
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
    price, is_stale = market_data_agent.get_current_price("INVALIDTICKER")
    
    # Assert
    assert price is None
    assert is_stale is False

@patch('yfinance.Ticker')
def test_get_current_price_caching(mock_yf_ticker):
    # Arrange
    market_data_agent._cache.clear()
    mock_instance = MagicMock()
    mock_instance.history.return_value = create_mock_history(200.0)
    mock_yf_ticker.return_value = mock_instance
    
    # Act: Call the function twice
    price1, stale1 = market_data_agent.get_current_price("GOOG")
    price2, stale2 = market_data_agent.get_current_price("GOOG")
    
    # Assert
    assert price1 == Decimal("200.00")
    assert price2 == Decimal("200.00")
    assert stale1 is False
    assert stale2 is False
    # The yfinance Ticker should only have been called ONCE due to caching
    mock_yf_ticker.assert_called_once_with("GOOG")


@patch('yfinance.Ticker')
def test_get_current_price_uses_db_cache_when_fresh(mock_yf_ticker, db_session):
    market_data_agent._cache.clear()
    crud.upsert_cached_price(db_session, "AAPL", Decimal("123.45"))

    price, is_stale = market_data_agent.get_current_price("aapl", db=db_session)

    assert price == Decimal("123.45")
    assert is_stale is False
    mock_yf_ticker.assert_not_called()


@patch('yfinance.Ticker')
def test_get_current_price_force_refresh_bypasses_fresh_db_cache(mock_yf_ticker, db_session):
    market_data_agent._cache.clear()
    crud.upsert_cached_price(db_session, "AAPL", Decimal("123.45"))

    mock_instance = MagicMock()
    mock_instance.history.return_value = create_mock_history(130.0)
    mock_yf_ticker.return_value = mock_instance

    price, is_stale = market_data_agent.get_current_price("AAPL", db=db_session, force_refresh=True)
    cached = crud.get_cached_price(db_session, "AAPL")

    assert price == Decimal("130.00")
    assert is_stale is False
    assert cached is not None
    assert cached.price == Decimal("130.00")
    mock_yf_ticker.assert_called_once_with("AAPL")


@patch('yfinance.Ticker')
def test_get_current_price_returns_stale_db_cache_on_provider_failure(mock_yf_ticker, db_session):
    market_data_agent._cache.clear()
    crud.upsert_cached_price(db_session, "PETR4", Decimal("38.20"))

    with patch("app.crud.is_cached_price_fresh", return_value=False):
        mock_instance = MagicMock()
        mock_instance.history.return_value = create_mock_history(None)
        mock_yf_ticker.return_value = mock_instance

        price, is_stale = market_data_agent.get_current_price("PETR4", db=db_session)

    assert price == Decimal("38.20")
    assert is_stale is True


@patch('yfinance.Ticker')
def test_get_current_price_returns_none_when_no_db_cache_and_provider_failure(mock_yf_ticker, db_session):
    market_data_agent._cache.clear()

    mock_instance = MagicMock()
    mock_instance.history.return_value = create_mock_history(None)
    mock_yf_ticker.return_value = mock_instance

    price, is_stale = market_data_agent.get_current_price("UNKNOWN", db=db_session)

    assert price is None
    assert is_stale is False
