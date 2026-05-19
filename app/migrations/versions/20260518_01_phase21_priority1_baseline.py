"""legacy baseline schema

Revision ID: 20260518_01
Revises:
Create Date: 2026-05-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260518_01"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    op.create_table(
        "assets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticker", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("asset_type", sa.Enum("STOCK", "REIT", name="assettype"), nullable=False),
        sa.Column("sector", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticker", name="uq_assets_ticker"),
    )
    op.create_index(op.f("ix_assets_id"), "assets", ["id"], unique=False)
    op.create_index(op.f("ix_assets_ticker"), "assets", ["ticker"], unique=False)

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_transactions_id"), "transactions", ["id"], unique=False)

    op.create_table(
        "dividends",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("amount_per_share", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("asset_id", "payment_date", name="uq_dividends_asset_id_payment_date"),
    )
    op.create_index(op.f("ix_dividends_id"), "dividends", ["id"], unique=False)

    op.create_table(
        "magic_link_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("purpose", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("setup_used", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_magic_link_tokens_email"), "magic_link_tokens", ["email"], unique=False)
    op.create_index(op.f("ix_magic_link_tokens_id"), "magic_link_tokens", ["id"], unique=False)
    op.create_index(op.f("ix_magic_link_tokens_token_hash"), "magic_link_tokens", ["token_hash"], unique=True)

    op.create_table(
        "agent_actions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("agent_name", sa.String(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("tool_calls", sa.JSON(), nullable=True),
        sa.Column("response", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agent_actions_id"), "agent_actions", ["id"], unique=False)

    op.create_table(
        "asset_price_cache",
        sa.Column("ticker", sa.String(), nullable=False),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("ticker"),
    )


def downgrade() -> None:
    op.drop_table("asset_price_cache")
    op.drop_index(op.f("ix_agent_actions_id"), table_name="agent_actions")
    op.drop_table("agent_actions")
    op.drop_index(op.f("ix_magic_link_tokens_token_hash"), table_name="magic_link_tokens")
    op.drop_index(op.f("ix_magic_link_tokens_id"), table_name="magic_link_tokens")
    op.drop_index(op.f("ix_magic_link_tokens_email"), table_name="magic_link_tokens")
    op.drop_table("magic_link_tokens")
    op.drop_index(op.f("ix_dividends_id"), table_name="dividends")
    op.drop_table("dividends")
    op.drop_index(op.f("ix_transactions_id"), table_name="transactions")
    op.drop_table("transactions")
    op.drop_index(op.f("ix_assets_ticker"), table_name="assets")
    op.drop_index(op.f("ix_assets_id"), table_name="assets")
    op.drop_table("assets")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS assettype")
