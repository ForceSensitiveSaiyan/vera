"""add processing task id

Revision ID: 0002_add_processing_task_id
Revises: 0001_create_tables
Create Date: 2026-02-03
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0002_add_processing_task_id"
down_revision = "0001_create_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("processing_task_id", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("documents", "processing_task_id")
