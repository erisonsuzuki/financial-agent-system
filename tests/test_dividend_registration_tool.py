from datetime import date
from decimal import Decimal

from app import crud, schemas
from app.agents.tool_context import ToolContext, set_tool_context, reset_tool_context
from app.agents.tools import classify_agent_request, register_dividend


def test_register_dividend_requires_share_count_with_total_amount():
    result = register_dividend.invoke({"ticker": "HGCR11", "total_amount": Decimal("200.00")})
    assert result["status"] == "error"
    assert "share_count is required" in result["message"]


def test_register_dividend_success_with_amount_per_share(db_session):
    user = crud.create_user(db_session, email="div-user@example.com", password_hash="hash")
    portfolio = crud.get_or_create_default_portfolio(db_session, user.id)
    crud.create_asset(
        db_session,
        schemas.AssetCreate(ticker="HGCR11", name="HGCR11", asset_type="REIT"),
        portfolio_id=portfolio.id,
    )
    token = set_tool_context(ToolContext(user_id=user.id, portfolio_id=portfolio.id, db_session=db_session))
    try:
        result = register_dividend.invoke(
            {"ticker": "HGCR11", "amount_per_share": Decimal("0.9000"), "payment_date": date(2026, 1, 10)}
        )
        assert result["status"] == "success"
        assert result["data"]["amount_per_share"] == "0.9000"
    finally:
        reset_tool_context(token)


def test_classify_agent_request_routes_dividend_query_to_registration():
    result = classify_agent_request.invoke({"question": "Please register a cash dividend of 50 BRL for HGCR11"})
    assert result["agent_name"] == "registration_agent"
