"""add document locale and type

Revision ID: 0005_doc_locale_type
Revises: 0004_add_version_fields
Create Date: 2026-02-04
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0005_doc_locale_type"
down_revision = "0004_add_version_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("doc_type", sa.String(), nullable=True))
    op.add_column("documents", sa.Column("locale", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("documents", "locale")
    op.drop_column("documents", "doc_type")
