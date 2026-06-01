from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from app.agents.tool_context import get_tool_context


def parse_ticker_from_input(ticker_input: Any) -> str:
    if isinstance(ticker_input, dict):
        ticker_input = ticker_input.get("ticker", "")
    return str(ticker_input).strip().upper()


def quantize_dividend_amount(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def normalize_decimal_input(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, str):
        normalized = value.strip().replace(" ", "")
        if "," in normalized and "." in normalized:
            normalized = normalized.replace(".", "").replace(",", ".")
        elif "," in normalized:
            normalized = normalized.replace(",", ".")
        return Decimal(normalized)
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return Decimal(f"{value[0]}.{value[1]}")
    raise ValueError("average_price must be a number or decimal-like string")


def require_context():
    context = get_tool_context()
    if context is None:
        raise ValueError("Tool context is required for this operation")
    return context


def today() -> date:
    return date.today()
