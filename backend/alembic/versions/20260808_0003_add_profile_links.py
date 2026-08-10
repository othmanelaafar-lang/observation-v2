"""add profile links

Revision ID: 20260808_0003
Revises: 20260806_0002
Create Date: 2026-08-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260808_0003"
down_revision: Union[str, Sequence[str], None] = "20260806_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("talents", sa.Column("website_url", sa.String(length=255), nullable=True))
    op.add_column("talents", sa.Column("scholar_url", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("talents", "scholar_url")
    op.drop_column("talents", "website_url")