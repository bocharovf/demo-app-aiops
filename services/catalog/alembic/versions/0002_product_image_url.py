"""add image_url to products

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-08
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("products", sa.Column("image_url", sa.String(), nullable=True), schema="catalog")


def downgrade() -> None:
    op.drop_column("products", "image_url", schema="catalog")
