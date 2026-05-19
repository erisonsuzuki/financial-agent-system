from app import crud, schemas
from app.agents.tool_context import ToolContext, set_tool_context, reset_tool_context
from app.agents.tools import get_full_portfolio_analysis


def test_get_full_portfolio_analysis_no_assets(db_session):
    user = crud.create_user(db_session, email="analysis-empty@example.com", password_hash="hash")
    portfolio = crud.get_or_create_default_portfolio(db_session, user.id)
    token = set_tool_context(ToolContext(user_id=user.id, portfolio_id=portfolio.id, db_session=db_session))
    try:
        result = get_full_portfolio_analysis.invoke({})
        assert "No assets found" in result
    finally:
        reset_tool_context(token)


def test_get_full_portfolio_analysis_success(db_session):
    user = crud.create_user(db_session, email="analysis-ok@example.com", password_hash="hash")
    portfolio = crud.get_or_create_default_portfolio(db_session, user.id)
    crud.create_asset(db_session, schemas.AssetCreate(ticker="PETR4", name="PETR", asset_type="STOCK"), portfolio_id=portfolio.id)
    token = set_tool_context(ToolContext(user_id=user.id, portfolio_id=portfolio.id, db_session=db_session))
    try:
        result = get_full_portfolio_analysis.invoke({})
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["ticker"] == "PETR4"
    finally:
        reset_tool_context(token)
