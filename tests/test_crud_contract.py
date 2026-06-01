import inspect

from app import crud


def test_crud_public_contract_contains_expected_functions():
    expected = {
        "get_user",
        "get_user_by_email",
        "create_user",
        "create_user_without_password",
        "set_user_password",
        "create_magic_link_token",
        "count_recent_magic_link_requests",
        "get_magic_link_token_by_hash",
        "consume_magic_link_token",
        "mark_magic_link_setup_used",
        "get_asset",
        "get_asset_by_ticker",
        "get_assets",
        "create_asset",
        "update_asset",
        "delete_asset",
        "get_transaction",
        "get_transactions",
        "create_asset_transaction",
        "update_transaction",
        "delete_transaction",
        "get_dividend",
        "get_dividends",
        "create_asset_dividend",
        "update_dividend",
        "delete_dividend",
        "get_cached_price",
        "upsert_cached_price",
        "is_cached_price_fresh",
        "create_agent_action",
        "get_agent_actions",
    }
    available = {name for name, value in vars(crud).items() if inspect.isfunction(value)}
    assert expected.issubset(available)


def test_scoped_asset_query_keeps_portfolio_id_parameter():
    signature = inspect.signature(crud.get_asset)
    assert "portfolio_id" in signature.parameters
