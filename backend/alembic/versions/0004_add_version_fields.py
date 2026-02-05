"""add version fields

Revision ID: 0004_add_version_fields
Revises: 0003_add_document_pages
Create Date: 2026-02-04
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0004_add_version_fields"
down_revision = "0003_add_document_pages"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("document_pages", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))

    op.alter_column("documents", "version", server_default=None)
    op.alter_column("document_pages", "version", server_default=None)


def downgrade() -> None:
    op.drop_column("document_pages", "version")
    op.drop_column("documents", "version")
