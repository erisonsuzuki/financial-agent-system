from datetime import date
from decimal import Decimal

from app import crud, schemas
from app.agents.tool_context import ToolContext, set_tool_context, reset_tool_context
from app.agents.tools import update_transaction_by_id


def test_update_transaction_by_id_success(db_session):
    user = crud.create_user(db_session, email="mgmt-user@example.com", password_hash="hash")
    portfolio = crud.get_or_create_default_portfolio(db_session, user.id)
    asset = crud.create_asset(
        db_session,
        schemas.AssetCreate(ticker="MGT4", name="MGT", asset_type="STOCK"),
        portfolio_id=portfolio.id,
    )
    tx = crud.create_asset_transaction(
        db_session,
        schemas.TransactionCreate(asset_id=asset.id, quantity=1, price=Decimal("10.00"), transaction_date=date.today()),
        portfolio_id=portfolio.id,
    )

    token = set_tool_context(ToolContext(user_id=user.id, portfolio_id=portfolio.id, db_session=db_session))
    try:
        result = update_transaction_by_id.invoke({"transaction_id": tx.id, "new_price": Decimal("99.99")})
        assert result["price"] == "99.99"
    finally:
        reset_tool_context(token)
