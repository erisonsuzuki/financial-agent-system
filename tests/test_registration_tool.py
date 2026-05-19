from decimal import Decimal

from app import crud
from app.agents.tool_context import ToolContext, set_tool_context, reset_tool_context
from app.agents.tools import register_asset_position


def test_register_asset_position_success(db_session):
    user = crud.create_user(db_session, email="tool-user@example.com", password_hash="hash")
    portfolio = crud.get_or_create_default_portfolio(db_session, user.id)
    token = set_tool_context(ToolContext(user_id=user.id, portfolio_id=portfolio.id, db_session=db_session))

    try:
        result = register_asset_position.invoke(
            {"ticker": "TEST4.SA", "quantity": 150, "average_price": Decimal("10.50")}
        )
        assert result["status"] == "success"
        assets = crud.get_assets(db_session, ticker="TEST4.SA", portfolio_id=portfolio.id)
        assert len(assets) == 1
        transactions = crud.get_transactions(db_session, asset_id=assets[0].id, portfolio_id=portfolio.id)
        assert len(transactions) == 1
    finally:
        reset_tool_context(token)
