"""add tier and ai_purity

Revision ID: 20260811_0004
Revises: 20260808_0003
Create Date: 2026-08-11
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260811_0004"
down_revision: Union[str, Sequence[str], None] = "20260808_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("talents", sa.Column("tier", sa.String(length=20), nullable=True))
    op.add_column(
        "talents",
        sa.Column("ai_purity", sa.Float(), nullable=False, server_default="0"),
    )
    op.create_index("ix_talents_tier", "talents", ["tier"])


def downgrade() -> None:
    op.drop_index("ix_talents_tier", table_name="talents")
    op.drop_column("talents", "ai_purity")
    op.drop_column("talents", "tier")
