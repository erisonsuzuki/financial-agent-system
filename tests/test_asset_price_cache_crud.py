from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest

from app import crud, models


def test_cached_price_roundtrip_with_normalized_ticker(db_session):
    saved = crud.upsert_cached_price(db_session, " aapl ", Decimal("150.75"), source="yfinance")

    fetched = crud.get_cached_price(db_session, "AAPL")

    assert saved.ticker == "AAPL"
    assert fetched is not None
    assert fetched.ticker == "AAPL"
    assert fetched.price == Decimal("150.75")
    assert fetched.source == "yfinance"
    assert fetched.fetched_at is not None


def test_upsert_cached_price_updates_existing_row(db_session):
    crud.upsert_cached_price(
        db_session,
        "msft",
        Decimal("100.00"),
        fetched_at=datetime.now(timezone.utc) - timedelta(hours=2),
    )
    updated = crud.upsert_cached_price(
        db_session,
        "MSFT",
        Decimal("115.30"),
        fetched_at=datetime.now(timezone.utc),
    )

    rows = db_session.query(models.AssetPriceCache).filter(models.AssetPriceCache.ticker == "MSFT").all()

    assert len(rows) == 1
    assert updated.price == Decimal("115.30")


def test_is_cached_price_fresh_uses_one_hour_ttl(db_session):
    now = datetime.now(timezone.utc)
    stale = crud.upsert_cached_price(
        db_session,
        "GOOG",
        Decimal("200.00"),
        fetched_at=now - timedelta(hours=2),
    )
    fresh = crud.upsert_cached_price(
        db_session,
        "AMZN",
        Decimal("201.00"),
        fetched_at=now - timedelta(minutes=30),
    )

    assert crud.is_cached_price_fresh(stale, now=now) is False
    assert crud.is_cached_price_fresh(fresh, now=now) is True


def test_is_cached_price_fresh_accepts_exact_ttl_boundary(db_session):
    now = datetime.now(timezone.utc)
    boundary = crud.upsert_cached_price(
        db_session,
        "NVDA",
        Decimal("300.00"),
        fetched_at=now - timedelta(seconds=3600),
    )

    assert crud.is_cached_price_fresh(boundary, now=now) is True


def test_upsert_cached_price_rejects_empty_ticker(db_session):
    with pytest.raises(ValueError, match="Ticker must not be empty"):
        crud.upsert_cached_price(db_session, "   ", Decimal("10.00"))
