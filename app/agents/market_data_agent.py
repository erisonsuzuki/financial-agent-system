import time
from decimal import Decimal
from typing import Any, Dict, Iterable

import yfinance as yf
from sqlalchemy.orm import Session

from app import crud

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


def get_current_price(
    ticker: str,
    db: Session | None = None,
    force_refresh: bool = False,
) -> tuple[Decimal | None, bool]:
    """
    Fetches the current price for a given ticker.

    Returns a tuple of (price, is_stale).
    """
    normalized_ticker = crud.normalize_ticker(ticker)

    if db is not None:
        cached_price = crud.get_cached_price(db, normalized_ticker)

        if not force_refresh and crud.is_cached_price_fresh(cached_price):
            return cached_price.price, False

        for candidate in _ticker_candidates(normalized_ticker):
            price_decimal = _try_fetch_price(candidate)
            if price_decimal is not None:
                crud.upsert_cached_price(db, normalized_ticker, price_decimal, source="yfinance")
                return price_decimal, False

        if cached_price is not None:
            return cached_price.price, True

        return None, False

    current_time = time.time()

    cached_data = _cache.get(normalized_ticker)
    if cached_data and current_time - cached_data["timestamp"] < CACHE_TTL_SECONDS:
        return cached_data["price"], False

    for candidate in _ticker_candidates(normalized_ticker):
        price_decimal = _try_fetch_price(candidate)
        if price_decimal is not None:
            _cache[normalized_ticker] = {"price": price_decimal, "timestamp": current_time}
            return price_decimal, False

    return None, False
