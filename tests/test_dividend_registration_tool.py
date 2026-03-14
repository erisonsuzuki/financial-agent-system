import os
import json
from datetime import date
from decimal import Decimal

import httpx
import respx

from app.agents.tools import classify_agent_request, register_dividend

BASE_URL = os.getenv("INTERNAL_API_URL", "http://app:8000")


@respx.mock
def test_register_dividend_success_with_amount_per_share():
    ticker = "HGCR11"
    asset_id = 7

    respx.get(f"{BASE_URL}/assets/?ticker={ticker}").mock(
        return_value=httpx.Response(200, json=[{"id": asset_id, "ticker": ticker}])
    )
    respx.get(f"{BASE_URL}/dividends/?asset_id={asset_id}&payment_date=2026-01-10").mock(
        return_value=httpx.Response(200, json=[])
    )
    respx.post(f"{BASE_URL}/dividends/").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": 100,
                "asset_id": asset_id,
                "amount_per_share": "0.9000",
                "payment_date": "2026-01-10",
            },
        )
    )

    result = register_dividend.invoke(
        {
            "ticker": ticker,
            "amount_per_share": Decimal("0.90"),
            "payment_date": date(2026, 1, 10),
        }
    )

    assert result["status"] == "success"
    assert result["data"]["asset_id"] == asset_id
    assert result["data"]["amount_per_share"] == "0.9000"


def test_register_dividend_requires_share_count_with_total_amount():
    result = register_dividend.invoke(
        {
            "ticker": "HGCR11",
            "total_amount": Decimal("200.00"),
        }
    )

    assert result["status"] == "error"
    assert "share_count is required" in result["message"]


@respx.mock
def test_register_dividend_computes_amount_per_share_with_precision():
    ticker = "HGCR11"
    asset_id = 7

    assets_route = respx.get(f"{BASE_URL}/assets/?ticker={ticker}").mock(
        return_value=httpx.Response(200, json=[{"id": asset_id, "ticker": ticker}])
    )
    respx.get(f"{BASE_URL}/dividends/?asset_id={asset_id}&payment_date=2026-02-15").mock(
        return_value=httpx.Response(200, json=[])
    )
    dividends_route = respx.post(f"{BASE_URL}/dividends/").mock(return_value=httpx.Response(201, json={}))

    result = register_dividend.invoke(
        {
            "ticker": ticker,
            "total_amount": Decimal("100.00"),
            "share_count": Decimal("3"),
            "payment_date": date(2026, 2, 15),
        }
    )

    assert result["status"] == "success"
    assert assets_route.called
    assert dividends_route.called
    request_body = json.loads(dividends_route.calls.last.request.content.decode())
    assert request_body["amount_per_share"] == "33.3333"


@respx.mock
def test_register_dividend_uses_yfinance_fallback(monkeypatch):
    ticker = "HGCR11"
    asset_id = 7

    monkeypatch.setattr(
        "app.agents.tools.market_data_agent.get_latest_dividend",
        lambda _ticker: (Decimal("0.3219"), date(2026, 3, 10)),
    )

    respx.get(f"{BASE_URL}/assets/?ticker={ticker}").mock(
        return_value=httpx.Response(200, json=[{"id": asset_id, "ticker": ticker}])
    )
    respx.get(f"{BASE_URL}/dividends/?asset_id={asset_id}&payment_date=2026-03-10").mock(
        return_value=httpx.Response(200, json=[])
    )
    dividends_route = respx.post(f"{BASE_URL}/dividends/").mock(return_value=httpx.Response(201, json={}))

    result = register_dividend.invoke({"ticker": ticker})

    assert result["status"] == "success"
    assert "yfinance" in result["message"].lower()
    request_body = json.loads(dividends_route.calls.last.request.content.decode())
    assert request_body["amount_per_share"] == "0.3219"
    assert request_body["payment_date"] == "2026-03-10"


def test_register_dividend_fails_when_amount_missing_and_no_fallback(monkeypatch):
    monkeypatch.setattr(
        "app.agents.tools.market_data_agent.get_latest_dividend",
        lambda _ticker: (None, None),
    )

    result = register_dividend.invoke({"ticker": "HGCR11"})

    assert result["status"] == "error"
    assert "No dividend history found" in result["message"]


@respx.mock
def test_register_dividend_updates_existing_same_date_entry():
    ticker = "HGCR11"
    asset_id = 7

    respx.get(f"{BASE_URL}/assets/?ticker={ticker}").mock(
        return_value=httpx.Response(200, json=[{"id": asset_id, "ticker": ticker}])
    )
    respx.get(f"{BASE_URL}/dividends/?asset_id={asset_id}&payment_date=2026-04-01").mock(
        return_value=httpx.Response(200, json=[{"id": 11, "asset_id": asset_id}])
    )
    update_route = respx.put(f"{BASE_URL}/dividends/11").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": 11,
                "asset_id": asset_id,
                "amount_per_share": "0.4567",
                "payment_date": "2026-04-01",
            },
        )
    )

    result = register_dividend.invoke(
        {
            "ticker": ticker,
            "amount_per_share": Decimal("0.4567"),
            "payment_date": date(2026, 4, 1),
        }
    )

    assert result["status"] == "success"
    assert update_route.called


def test_classify_agent_request_routes_dividend_query_to_registration():
    result = classify_agent_request.invoke(
        {"question": "Please register a cash dividend of 50 BRL for HGCR11"}
    )

    assert result["agent_name"] == "registration_agent"


def test_classify_agent_request_keeps_analysis_query_in_analysis_agent():
    result = classify_agent_request.invoke(
        {"question": "Can you analyze my portfolio and suggest where I should invest next?"}
    )

    assert result["agent_name"] == "analysis_agent"
