from datetime import date
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Annotated, Optional, List, Any
import unicodedata
import re

from langchain.tools import tool

from app import crud, schemas
from app.agents import market_data_agent, portfolio_analyzer_agent
from app.agents.tool_context import get_tool_context


def _parse_ticker_from_input(ticker_input: Any) -> str:
    if isinstance(ticker_input, dict):
        ticker_input = ticker_input.get("ticker", "")
    return str(ticker_input).strip().upper()


def _quantize_dividend_amount(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def _normalize_decimal_input(value: Any) -> Decimal:
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


def _require_context():
    context = get_tool_context()
    if context is None:
        raise ValueError("Tool context is required for this operation")
    return context


@tool
def register_asset_position(
    ticker: Annotated[str, "The stock ticker symbol, e.g., 'PETR4.SA'."],
    quantity: Annotated[float, "The total quantity the user holds."],
    average_price: Annotated[Any, "The user's average purchase price for this asset."],
) -> dict:
    """Register a full position for an asset in the active portfolio."""
    ticker = _parse_ticker_from_input(ticker)
    try:
        parsed_average_price = _normalize_decimal_input(average_price)
        context = _require_context()
    except (InvalidOperation, ValueError, TypeError) as exc:
        return {"status": "error", "ticker": ticker, "message": str(exc)}

    db = context.db_session
    asset = crud.get_asset_by_ticker(db, ticker=ticker, portfolio_id=context.portfolio_id)
    if asset is None:
        asset = crud.create_asset(
            db=db,
            asset=schemas.AssetCreate(ticker=ticker, name=ticker, asset_type="STOCK"),
            portfolio_id=context.portfolio_id,
        )

    crud.create_asset_transaction(
        db=db,
        transaction=schemas.TransactionCreate(
            asset_id=asset.id,
            quantity=quantity,
            price=parsed_average_price,
            transaction_date=date.today(),
        ),
        portfolio_id=context.portfolio_id,
    )
    return {"status": "success", "ticker": ticker, "quantity": quantity, "average_price": str(parsed_average_price)}


@tool
def list_all_transactions(limit: Annotated[Optional[int], "The maximum number of recent transactions to return."] = 100) -> List[dict] | str:
    """List recent transactions for the active portfolio."""
    try:
        context = _require_context()
        transactions = crud.get_transactions(context.db_session, limit=limit or 100, portfolio_id=context.portfolio_id)
        return [
            {
                "id": tx.id,
                "asset_id": tx.asset_id,
                "ticker": tx.asset.ticker if tx.asset else None,
                "quantity": tx.quantity,
                "price": str(tx.price),
                "transaction_date": str(tx.transaction_date),
            }
            for tx in transactions
        ]
    except ValueError as exc:
        return f"Error: {exc}"


@tool
def register_dividend(
    ticker: Annotated[str, "The stock ticker symbol, e.g., 'PETR4.SA'."],
    amount_per_share: Annotated[Optional[Decimal], "Dividend amount per share."] = None,
    total_amount: Annotated[Optional[Decimal], "Total dividend amount received."] = None,
    share_count: Annotated[Optional[Decimal], "Share count used to compute per-share amount."] = None,
    payment_date: Annotated[Optional[date], "Dividend payment date."] = None,
) -> dict:
    """Register or update a dividend by ticker in the active portfolio."""
    normalized_ticker = _parse_ticker_from_input(ticker)
    if not normalized_ticker:
        return {"status": "error", "message": "Ticker is required.", "data": None}

    if amount_per_share is not None and total_amount is not None:
        return {"status": "error", "message": "Provide either amount_per_share or total_amount, not both.", "data": None}
    if amount_per_share is not None and amount_per_share <= 0:
        return {"status": "error", "message": "amount_per_share must be greater than zero.", "data": None}
    if total_amount is not None and total_amount <= 0:
        return {"status": "error", "message": "total_amount must be greater than zero.", "data": None}
    if share_count is not None and share_count <= 0:
        return {"status": "error", "message": "share_count must be greater than zero.", "data": None}

    computed_amount_per_share = amount_per_share
    fallback_payment_date = None

    if total_amount is not None:
        if share_count is None:
            return {"status": "error", "message": "share_count is required when total_amount is provided.", "data": None}
        computed_amount_per_share = total_amount / share_count

    if computed_amount_per_share is None:
        fallback_amount, fallback_date = market_data_agent.get_latest_dividend(normalized_ticker)
        if fallback_amount is None:
            return {
                "status": "error",
                "message": f"No dividend history found for ticker {normalized_ticker} and no amount was provided.",
                "data": None,
            }
        computed_amount_per_share = fallback_amount
        fallback_payment_date = fallback_date

    try:
        context = _require_context()
        db = context.db_session
        asset = crud.get_asset_by_ticker(db, ticker=normalized_ticker, portfolio_id=context.portfolio_id)
        if asset is None:
            return {"status": "error", "message": f"Asset with ticker {normalized_ticker} not found.", "data": None}

        computed_amount_per_share = _quantize_dividend_amount(computed_amount_per_share)
        effective_payment_date = payment_date or fallback_payment_date or date.today()
        existing = crud.get_dividends(
            db=db,
            asset_id=asset.id,
            payment_date=effective_payment_date,
            portfolio_id=context.portfolio_id,
            limit=1,
        )

        if existing:
            created_dividend = crud.update_dividend(
                db=db,
                db_dividend=existing[0],
                dividend_in=schemas.DividendUpdate(
                    amount_per_share=computed_amount_per_share,
                    payment_date=effective_payment_date,
                ),
            )
        else:
            created_dividend = crud.create_asset_dividend(
                db=db,
                dividend=schemas.DividendCreate(
                    asset_id=asset.id,
                    amount_per_share=computed_amount_per_share,
                    payment_date=effective_payment_date,
                ),
                portfolio_id=context.portfolio_id,
            )
    except ValueError as exc:
        return {"status": "error", "message": f"An error occurred: {exc}", "data": None}

    message = f"Dividend registered for {normalized_ticker}."
    if amount_per_share is None and total_amount is None:
        message = f"Dividend registered for {normalized_ticker} using latest yfinance amount_per_share."

    return {
        "status": "success",
        "message": message,
        "data": {
            "ticker": normalized_ticker,
            "asset_id": created_dividend.asset_id,
            "amount_per_share": str(created_dividend.amount_per_share),
            "payment_date": str(created_dividend.payment_date),
        },
    }


@tool
def list_transactions_for_ticker(ticker: Annotated[str, "The ticker symbol to search for, e.g., 'PETR4.SA'."]) -> list[dict] | str:
    """List transactions for a specific ticker in the active portfolio."""
    ticker = _parse_ticker_from_input(ticker)
    try:
        context = _require_context()
        asset = crud.get_asset_by_ticker(context.db_session, ticker=ticker, portfolio_id=context.portfolio_id)
        if not asset:
            return f"Error: Asset with ticker {ticker} not found."
        transactions = crud.get_transactions_for_asset(
            context.db_session,
            asset_id=asset.id,
            portfolio_id=context.portfolio_id,
        )
        return [
            {
                "id": tx.id,
                "asset_id": tx.asset_id,
                "quantity": tx.quantity,
                "price": str(tx.price),
                "transaction_date": str(tx.transaction_date),
            }
            for tx in transactions
        ]
    except ValueError as exc:
        return f"Error: {exc}"


@tool
def update_transaction_by_id(
    transaction_id: Annotated[int, "The unique ID of the transaction to update."],
    new_quantity: Annotated[Optional[float], "The corrected quantity of the transaction."] = None,
    new_price: Annotated[Optional[Decimal], "The corrected price of the transaction."] = None,
    new_date: Annotated[Optional[str], "The corrected date of the transaction, in 'YYYY-MM-DD' format."] = None,
) -> dict | str:
    """Update transaction fields by ID in the active portfolio."""
    update_payload = {}
    if new_quantity is not None:
        update_payload["quantity"] = new_quantity
    if new_price is not None:
        update_payload["price"] = new_price
    if new_date is not None:
        update_payload["transaction_date"] = new_date
    if not update_payload:
        return "Error: At least one field (quantity, price, or date) must be provided to update."

    try:
        context = _require_context()
        db_transaction = crud.get_transaction(context.db_session, transaction_id=transaction_id, portfolio_id=context.portfolio_id)
        if db_transaction is None:
            return "Error: Transaction not found."
        updated = crud.update_transaction(
            db=context.db_session,
            db_transaction=db_transaction,
            transaction_in=schemas.TransactionUpdate(**update_payload),
        )
        return {
            "id": updated.id,
            "asset_id": updated.asset_id,
            "quantity": updated.quantity,
            "price": str(updated.price),
            "transaction_date": str(updated.transaction_date),
        }
    except ValueError as exc:
        return f"Error: {exc}"


@tool
def delete_asset_by_ticker(ticker: Annotated[str, "The ticker symbol of the asset to delete, e.g., 'PETR4.SA'."]) -> str:
    """Delete an asset by ticker in the active portfolio."""
    try:
        ticker = _parse_ticker_from_input(ticker)
        context = _require_context()
        asset = crud.get_asset_by_ticker(context.db_session, ticker=ticker, portfolio_id=context.portfolio_id)
        if asset is None:
            return f"Error: Asset with ticker {ticker} not found."
        crud.delete_asset(context.db_session, asset_id=asset.id, portfolio_id=context.portfolio_id)
        return f"Successfully deleted asset {ticker} and all its records."
    except ValueError as exc:
        return f"Error: {exc}"


@tool
def get_full_portfolio_analysis() -> List[dict] | str:
    """Return analysis for all assets in the active portfolio."""
    try:
        context = _require_context()
        assets = crud.get_assets(context.db_session, portfolio_id=context.portfolio_id)
        if not assets:
            return "Error: No assets found in the portfolio to analyze."
        return [portfolio_analyzer_agent.analyze_asset(context.db_session, asset).model_dump(mode="json") for asset in assets]
    except ValueError as exc:
        return f"An unexpected error occurred during portfolio analysis: {exc}"


@tool
def classify_agent_request(
    question: Annotated[str, "The original natural-language request from the user."],
) -> dict:
    """Classify a request into registration, management, or analysis."""
    normalized = unicodedata.normalize("NFKD", question.lower())
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    tokens = re.findall(r"[a-z0-9]+", normalized)

    root_patterns = {
        "registration_agent": [
            "registr",
            "cadast",
            "compr",
            "buy",
            "acqui",
            "purch",
            "dividend",
            "dividendo",
            "distribu",
            "jcp",
        ],
        "management_agent": [
            "updat",
            "atualiz",
            "actualiz",
            "correct",
            "corrig",
            "correg",
            "sell",
            "vend",
            "delet",
            "elimin",
            "adjust",
            "ajust",
            "fix",
            "consert",
            "edit",
        ],
        "analysis_agent": [
            "anal",
            "invest",
            "recomend",
            "recommend",
            "sugest",
            "suger",
        ],
    }

    phrase_patterns = {
        "registration_agent": ["add position", "new asset"],
        "analysis_agent": ["where should", "onde devo", "donde deber"],
    }

    scores = {agent: 0 for agent in root_patterns}
    matched_roots = {agent: [] for agent in root_patterns}
    matched_phrases = {agent: [] for agent in root_patterns}

    for agent, roots in root_patterns.items():
        for token in tokens:
            matched_root = next((root for root in roots if token.startswith(root)), None)
            if matched_root is not None:
                scores[agent] += 1
                matched_roots[agent].append(matched_root)

    for agent, phrases in phrase_patterns.items():
        for phrase in phrases:
            if phrase in normalized:
                scores[agent] += 1
                matched_phrases[agent].append(phrase)

    best_agent = max(scores, key=scores.get)
    best_score = scores[best_agent]
    total_hits = sum(scores.values()) or 1
    confidence = min(1.0, best_score / total_hits) if best_score else 0.33

    if best_score:
        roots_used = sorted(set(matched_roots[best_agent]))
        phrases_used = sorted(set(matched_phrases[best_agent]))
        evidence_parts = []
        if roots_used:
            evidence_parts.append(f"roots={roots_used}")
        if phrases_used:
            evidence_parts.append(f"phrases={phrases_used}")
        evidence = "; ".join(evidence_parts) if evidence_parts else "no explicit evidence"
        reasoning = f"Matched routing signals for {best_agent}: {best_score} hit(s); {evidence}."
    else:
        reasoning = "No strong routing signals; defaulting to analysis_agent."
    return {
        "agent_name": best_agent if best_score else "analysis_agent",
        "confidence": round(confidence, 2),
        "reasoning": reasoning,
    }
