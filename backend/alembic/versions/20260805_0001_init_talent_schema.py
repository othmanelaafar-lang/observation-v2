"""init talent schema

Revision ID: 20260805_0001
Revises: 
Create Date: 2026-08-05
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260805_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "domains",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=140), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_domains_id"), "domains", ["id"], unique=False)
    op.create_index(op.f("ix_domains_name"), "domains", ["name"], unique=True)
    op.create_index(op.f("ix_domains_slug"), "domains", ["slug"], unique=True)

    op.create_table(
        "talents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=180), nullable=False),
        sa.Column("name_ar", sa.String(length=180), nullable=True),
        sa.Column("photo_url", sa.String(length=255), nullable=True),
        sa.Column("country", sa.String(length=120), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("role", sa.String(length=180), nullable=True),
        sa.Column("organization", sa.String(length=180), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("email", sa.String(length=180), nullable=True),
        sa.Column("linkedin", sa.String(length=255), nullable=True),
        sa.Column("github_url", sa.String(length=255), nullable=True),
        sa.Column("skills_text", sa.Text(), nullable=True),
        sa.Column("interests_text", sa.Text(), nullable=True),
        sa.Column("publications", sa.Integer(), nullable=False),
        sa.Column("h_index", sa.Integer(), nullable=False),
        sa.Column("citations", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("featured", sa.Boolean(), nullable=False),
        sa.Column("source", sa.String(length=40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_talents_city"), "talents", ["city"], unique=False)
    op.create_index(op.f("ix_talents_country"), "talents", ["country"], unique=False)
    op.create_index(op.f("ix_talents_full_name"), "talents", ["full_name"], unique=False)
    op.create_index(op.f("ix_talents_id"), "talents", ["id"], unique=False)

    op.create_table(
        "universities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("country_code", sa.String(length=8), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("website", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_universities_country_code"), "universities", ["country_code"], unique=False)
    op.create_index(op.f("ix_universities_id"), "universities", ["id"], unique=False)
    op.create_index(op.f("ix_universities_name"), "universities", ["name"], unique=True)

    op.create_table(
        "talent_domains",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("talent_id", sa.Integer(), nullable=False),
        sa.Column("domain_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["domain_id"], ["domains.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["talent_id"], ["talents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("talent_id", "domain_id", name="uq_talent_domain"),
    )
    op.create_index(op.f("ix_talent_domains_domain_id"), "talent_domains", ["domain_id"], unique=False)
    op.create_index(op.f("ix_talent_domains_talent_id"), "talent_domains", ["talent_id"], unique=False)

    op.create_table(
        "talent_universities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("talent_id", sa.Integer(), nullable=False),
        sa.Column("university_id", sa.Integer(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["talent_id"], ["talents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["university_id"], ["universities.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("talent_id", "university_id", name="uq_talent_university"),
    )
    op.create_index(op.f("ix_talent_universities_talent_id"), "talent_universities", ["talent_id"], unique=False)
    op.create_index(op.f("ix_talent_universities_university_id"), "talent_universities", ["university_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_talent_universities_university_id"), table_name="talent_universities")
    op.drop_index(op.f("ix_talent_universities_talent_id"), table_name="talent_universities")
    op.drop_table("talent_universities")

    op.drop_index(op.f("ix_talent_domains_talent_id"), table_name="talent_domains")
    op.drop_index(op.f("ix_talent_domains_domain_id"), table_name="talent_domains")
    op.drop_table("talent_domains")

    op.drop_index(op.f("ix_universities_name"), table_name="universities")
    op.drop_index(op.f("ix_universities_id"), table_name="universities")
    op.drop_index(op.f("ix_universities_country_code"), table_name="universities")
    op.drop_table("universities")

    op.drop_index(op.f("ix_talents_id"), table_name="talents")
    op.drop_index(op.f("ix_talents_full_name"), table_name="talents")
    op.drop_index(op.f("ix_talents_country"), table_name="talents")
    op.drop_index(op.f("ix_talents_city"), table_name="talents")
    op.drop_table("talents")

    op.drop_index(op.f("ix_domains_slug"), table_name="domains")
    op.drop_index(op.f("ix_domains_name"), table_name="domains")
    op.drop_index(op.f("ix_domains_id"), table_name="domains")
    op.drop_table("domains")
