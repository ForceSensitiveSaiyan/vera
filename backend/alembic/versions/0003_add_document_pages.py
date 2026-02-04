"""add document pages

Revision ID: 0003_add_document_pages
Revises: 0002_add_processing_task_id
Create Date: 2026-02-04
"""

from __future__ import annotations

import uuid

from alembic import op
import sqlalchemy as sa

revision = "0003_add_document_pages"
down_revision = "0002_add_processing_task_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("page_count", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("documents", sa.Column("review_complete_at", sa.DateTime(), nullable=True))

    op.create_table(
        "document_pages",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("document_id", sa.String(), sa.ForeignKey("documents.id"), nullable=False, index=True),
        sa.Column("page_index", sa.Integer(), nullable=False),
        sa.Column("image_path", sa.String(), nullable=False),
        sa.Column("image_width", sa.Integer(), nullable=False),
        sa.Column("image_height", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("validated_text", sa.Text(), nullable=True),
        sa.Column("structured_fields", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("review_complete_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.add_column("tokens", sa.Column("page_id", sa.String(), nullable=True))
    op.add_column("corrections", sa.Column("page_id", sa.String(), nullable=True))
    op.add_column("audit_logs", sa.Column("page_id", sa.String(), nullable=True))

    bind = op.get_bind()
    documents = bind.execute(sa.text("SELECT id, image_path, image_width, image_height, status FROM documents")).fetchall()
    for doc in documents:
        page_id = uuid.uuid4().hex
        bind.execute(
            sa.text(
                """
                INSERT INTO document_pages (
                    id, document_id, page_index, image_path, image_width, image_height, status,
                    structured_fields, created_at, updated_at
                ) VALUES (
                    :id, :document_id, :page_index, :image_path, :image_width, :image_height, :status,
                    :structured_fields, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
                """
            ),
            {
                "id": page_id,
                "document_id": doc.id,
                "page_index": 0,
                "image_path": doc.image_path,
                "image_width": doc.image_width,
                "image_height": doc.image_height,
                "status": doc.status,
                "structured_fields": "{}",
            },
        )
        bind.execute(
            sa.text("UPDATE tokens SET page_id = :page_id WHERE document_id = :document_id"),
            {"page_id": page_id, "document_id": doc.id},
        )
        bind.execute(
            sa.text("UPDATE corrections SET page_id = :page_id WHERE document_id = :document_id"),
            {"page_id": page_id, "document_id": doc.id},
        )

    with op.batch_alter_table("tokens") as batch:
        batch.alter_column("page_id", existing_type=sa.String(), nullable=False)
    with op.batch_alter_table("corrections") as batch:
        batch.alter_column("page_id", existing_type=sa.String(), nullable=False)

    op.alter_column("documents", "page_count", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("corrections") as batch:
        batch.drop_column("page_id")
    with op.batch_alter_table("tokens") as batch:
        batch.drop_column("page_id")
    with op.batch_alter_table("audit_logs") as batch:
        batch.drop_column("page_id")

    op.drop_table("document_pages")
    op.drop_column("documents", "review_complete_at")
    op.drop_column("documents", "page_count")
