"""initial orders schema

Revision ID: 0001
Revises:
Create Date: 2026-07-23
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

order_status = sa.Enum("created", "confirmed", "cancelled", name="order_status", schema="orders")


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS orders")
    # order_status is created implicitly by create_table() below since it's
    # only used by one column; an explicit .create() here would double-create it.

    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String, nullable=False, unique=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="orders",
    )

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("orders.users.id"), nullable=False),
        sa.Column("status", order_status, nullable=False, server_default="created"),
        sa.Column("total_amount", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="orders",
    )

    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("order_id", sa.Integer, sa.ForeignKey("orders.orders.id"), nullable=False),
        sa.Column("product_id", sa.Integer, nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False),
        sa.Column("price_at_order", sa.Numeric(10, 2), nullable=False),
        schema="orders",
    )


def downgrade() -> None:
    op.drop_table("order_items", schema="orders")
    op.drop_table("orders", schema="orders")
    op.drop_table("users", schema="orders")
    # order_status is dropped automatically along with the "orders" table above.
