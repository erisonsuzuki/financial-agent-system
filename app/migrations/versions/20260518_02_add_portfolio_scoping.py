"""add portfolio scoping

Revision ID: 20260518_02
Revises: 20260518_01
Create Date: 2026-05-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


revision: str = "20260518_02"
down_revision: Union[str, Sequence[str], None] = "20260518_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    op.create_table(
        "portfolios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False, server_default="Default"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_portfolios_id"), "portfolios", ["id"], unique=False)
    op.create_index(op.f("ix_portfolios_user_id"), "portfolios", ["user_id"], unique=False)

    users_count = bind.execute(text("SELECT COUNT(*) FROM users")).scalar() or 0
    if users_count == 0:
        bind.execute(
            text(
                "INSERT INTO users (email, password_hash) VALUES (:email, :password_hash)"
            ),
            {
                "email": "legacy-owner@local",
                "password_hash": "__MAGIC_LINK_PENDING__legacy_migration_placeholder",
            },
        )

    bind.execute(
        text(
            """
            INSERT INTO portfolios (user_id, name)
            SELECT u.id, 'Default'
            FROM users u
            WHERE NOT EXISTS (
                SELECT 1 FROM portfolios p WHERE p.user_id = u.id
            )
            """
        )
    )

    default_portfolio_id = bind.execute(
        text("SELECT id FROM portfolios ORDER BY id ASC LIMIT 1")
    ).scalar()

    op.add_column("assets", sa.Column("portfolio_id", sa.Integer(), nullable=True))
    op.add_column("transactions", sa.Column("portfolio_id", sa.Integer(), nullable=True))
    op.add_column("dividends", sa.Column("portfolio_id", sa.Integer(), nullable=True))

    bind.execute(
        text("UPDATE assets SET portfolio_id = :portfolio_id WHERE portfolio_id IS NULL"),
        {"portfolio_id": default_portfolio_id},
    )
    if bind.dialect.name == "sqlite":
        bind.execute(
            text(
                """
                UPDATE transactions
                SET portfolio_id = (
                    SELECT assets.portfolio_id
                    FROM assets
                    WHERE assets.id = transactions.asset_id
                )
                WHERE portfolio_id IS NULL
                """
            )
        )
        bind.execute(
            text(
                """
                UPDATE dividends
                SET portfolio_id = (
                    SELECT assets.portfolio_id
                    FROM assets
                    WHERE assets.id = dividends.asset_id
                )
                WHERE portfolio_id IS NULL
                """
            )
        )
    else:
        bind.execute(
            text(
                """
                UPDATE transactions t
                SET portfolio_id = a.portfolio_id
                FROM assets a
                WHERE t.asset_id = a.id AND t.portfolio_id IS NULL
                """
            )
        )
        bind.execute(
            text(
                """
                UPDATE dividends d
                SET portfolio_id = a.portfolio_id
                FROM assets a
                WHERE d.asset_id = a.id AND d.portfolio_id IS NULL
                """
            )
        )

    with op.batch_alter_table("assets") as batch_op:
        batch_op.alter_column("portfolio_id", existing_type=sa.Integer(), nullable=False)
        batch_op.create_foreign_key("fk_assets_portfolio_id", "portfolios", ["portfolio_id"], ["id"])
        batch_op.drop_constraint("uq_assets_ticker", type_="unique")
        batch_op.create_unique_constraint("uq_assets_portfolio_ticker", ["portfolio_id", "ticker"])

    with op.batch_alter_table("transactions") as batch_op:
        batch_op.alter_column("portfolio_id", existing_type=sa.Integer(), nullable=False)
        batch_op.create_foreign_key("fk_transactions_portfolio_id", "portfolios", ["portfolio_id"], ["id"])

    with op.batch_alter_table("dividends") as batch_op:
        batch_op.alter_column("portfolio_id", existing_type=sa.Integer(), nullable=False)
        batch_op.create_foreign_key("fk_dividends_portfolio_id", "portfolios", ["portfolio_id"], ["id"])

    op.create_index(op.f("ix_assets_portfolio_id"), "assets", ["portfolio_id"], unique=False)
    op.create_index(op.f("ix_transactions_portfolio_id"), "transactions", ["portfolio_id"], unique=False)
    op.create_index(op.f("ix_dividends_portfolio_id"), "dividends", ["portfolio_id"], unique=False)

def downgrade() -> None:
    op.drop_index(op.f("ix_dividends_portfolio_id"), table_name="dividends")
    op.drop_index(op.f("ix_transactions_portfolio_id"), table_name="transactions")
    op.drop_index(op.f("ix_assets_portfolio_id"), table_name="assets")

    with op.batch_alter_table("dividends") as batch_op:
        batch_op.drop_constraint("fk_dividends_portfolio_id", type_="foreignkey")
        batch_op.drop_column("portfolio_id")

    with op.batch_alter_table("transactions") as batch_op:
        batch_op.drop_constraint("fk_transactions_portfolio_id", type_="foreignkey")
        batch_op.drop_column("portfolio_id")

    with op.batch_alter_table("assets") as batch_op:
        batch_op.drop_constraint("fk_assets_portfolio_id", type_="foreignkey")
        batch_op.drop_constraint("uq_assets_portfolio_ticker", type_="unique")
        batch_op.create_unique_constraint("uq_assets_ticker", ["ticker"])
        batch_op.drop_column("portfolio_id")

    op.drop_index(op.f("ix_portfolios_user_id"), table_name="portfolios")
    op.drop_index(op.f("ix_portfolios_id"), table_name="portfolios")
    op.drop_table("portfolios")
