import yfinance as yf
import time
from typing import Dict, Any

# Simple in-memory cache to avoid excessive API calls
# In a production system, this would be replaced by Redis, Memcached, etc.
_cache: Dict[str, Dict[str, Any]] = {}
CACHE_TTL_SECONDS = 60 * 15  # 15 minutes

def get_current_price(ticker: str) -> float | None:
    """
    Fetches the current price for a given ticker, using a time-based cache.
    """
    current_time = time.time()
    
    # Check cache first
    if ticker in _cache:
        cached_data = _cache[ticker]
        if current_time - cached_data["timestamp"] < CACHE_TTL_SECONDS:
            return cached_data["price"]

    # If not in cache or expired, fetch from yfinance
    try:
        stock = yf.Ticker(ticker)
        # Fetch the most recent price data
        hist = stock.history(period="1d")
        if hist.empty:
            return None
            
        price = hist['Close'].iloc[-1]
        
        # Update cache
        _cache[ticker] = {"price": price, "timestamp": current_time}
        
        return price
    except Exception:
        # Could be a network error or invalid ticker
        return None
