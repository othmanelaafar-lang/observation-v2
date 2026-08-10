"""add contact links

Revision ID: 20260806_0002
Revises: 20260805_0001
Create Date: 2026-08-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260806_0002"
down_revision: Union[str, Sequence[str], None] = "20260805_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("talents", sa.Column("orcid_url", sa.String(length=255), nullable=True))
    op.add_column("talents", sa.Column("openalex_url", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("talents", "openalex_url")
    op.drop_column("talents", "orcid_url")
