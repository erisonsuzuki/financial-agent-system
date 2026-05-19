from datetime import date
from decimal import Decimal

from app import crud, schemas
from app.agents.tool_context import ToolContext, set_tool_context, reset_tool_context
from app.agents.tools import list_transactions_for_ticker


def test_list_transactions_for_ticker_success(db_session):
    user = crud.create_user(db_session, email="tools-user@example.com", password_hash="hash")
    portfolio = crud.get_or_create_default_portfolio(db_session, user.id)
    asset = crud.create_asset(
        db_session,
        schemas.AssetCreate(ticker="XPML11", name="XPML11", asset_type="REIT"),
        portfolio_id=portfolio.id,
    )
    crud.create_asset_transaction(
        db_session,
        schemas.TransactionCreate(asset_id=asset.id, quantity=10, price=Decimal("100.00"), transaction_date=date.today()),
        portfolio_id=portfolio.id,
    )

    token = set_tool_context(ToolContext(user_id=user.id, portfolio_id=portfolio.id, db_session=db_session))
    try:
        result = list_transactions_for_ticker.invoke({"ticker": "XPML11"})
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["asset_id"] == asset.id
    finally:
        reset_tool_context(token)
