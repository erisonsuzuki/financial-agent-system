import time
from decimal import Decimal
from typing import Any, Dict, Iterable

import yfinance as yf

# Simple in-memory cache to avoid excessive API calls
_cache: Dict[str, Dict[str, Any]] = {}
CACHE_TTL_SECONDS = 60 * 15  # 15 minutes


def _try_fetch_price(symbol: str) -> Decimal | None:
    """Fetches the latest close price for a symbol, returning None if unavailable."""
    try:
        hist = yf.Ticker(symbol).history(period="1d")
        if hist.empty:
            return None
        price = hist["Close"].iloc[-1]
        return Decimal(str(price)).quantize(Decimal("0.01"))
    except Exception:
        return None


def _ticker_candidates(ticker: str) -> Iterable[str]:
    """
    Builds a list of symbols to try. For Brazilian tickers we also attempt the `.SA` suffix.
    """
    yield ticker
    if "." not in ticker:
        yield f"{ticker}.SA"


def get_current_price(ticker: str) -> Decimal | None:
    """
    Fetches the current price for a given ticker, using a time-based cache and fallback suffixes.
    """
    current_time = time.time()

    cached_data = _cache.get(ticker)
    if cached_data and current_time - cached_data["timestamp"] < CACHE_TTL_SECONDS:
        return cached_data["price"]

    for candidate in _ticker_candidates(ticker):
        price_decimal = _try_fetch_price(candidate)
        if price_decimal is not None:
            _cache[ticker] = {"price": price_decimal, "timestamp": current_time}
            return price_decimal

    return None
