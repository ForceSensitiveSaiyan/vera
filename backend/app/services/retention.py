from __future__ import annotations

import os
import shutil
from datetime import timedelta

from sqlalchemy import delete, func, select

from app.db.session import Base, engine, get_session
from app.models.documents import AuditLog, Correction, Document, DocumentPage, Token
from app.schemas.documents import DocumentStatus
from app.utils.time import utcnow


def _archive_file(source_path: str, archive_root: str, document_id: str) -> None:
    os.makedirs(archive_root, exist_ok=True)
    destination_dir = os.path.join(archive_root, document_id)
    os.makedirs(destination_dir, exist_ok=True)
    if os.path.exists(source_path):
        shutil.move(source_path, os.path.join(destination_dir, os.path.basename(source_path)))


def cleanup_documents() -> dict[str, int | str]:
    Base.metadata.create_all(bind=engine)
    retention_days = int(os.getenv("RETENTION_DAYS", "30"))
    if retention_days <= 0:
        return {"status": "disabled", "deleted": 0}

    trigger = os.getenv("RETENTION_TRIGGER", "post_export")
    mode = os.getenv("RETENTION_MODE", "delete")
    archive_dir = os.getenv("RETENTION_ARCHIVE_DIR", "./archive")

    cutoff = utcnow() - timedelta(days=retention_days)

    with get_session() as session:
        document_query = select(Document).where(
            Document.status.not_in([DocumentStatus.processing.value, DocumentStatus.uploaded.value])
        )

        if trigger == "post_review":
            document_query = document_query.where(Document.review_complete_at.is_not(None)).where(
                Document.review_complete_at <= cutoff
            )
        else:
            export_subquery = (
                select(
                    AuditLog.document_id,
                    func.max(AuditLog.created_at).label("exported_at"),
                )
                .where(AuditLog.event_type == "exported")
                .group_by(AuditLog.document_id)
                .subquery()
            )
            document_query = document_query.join(
                export_subquery, Document.id == export_subquery.c.document_id
            ).where(export_subquery.c.exported_at <= cutoff)

        documents = session.execute(document_query).scalars().all()
        if not documents:
            return {"status": "ok", "deleted": 0}

        document_ids = [document.id for document in documents]

        page_paths = session.execute(
            select(DocumentPage.document_id, DocumentPage.image_path)
            .where(DocumentPage.document_id.in_(document_ids))
        ).all()

        for document in documents:
            if document.image_path:
                if mode == "archive":
                    _archive_file(str(document.image_path), archive_dir, document.id)
                else:
                    if os.path.exists(str(document.image_path)):
                        os.remove(str(document.image_path))

        for doc_id, path in page_paths:
            if path:
                if mode == "archive":
                    _archive_file(str(path), archive_dir, doc_id)
                else:
                    if os.path.exists(str(path)):
                        os.remove(str(path))

        session.execute(delete(Token).where(Token.document_id.in_(document_ids)))
        session.execute(delete(Correction).where(Correction.document_id.in_(document_ids)))
        session.execute(delete(AuditLog).where(AuditLog.document_id.in_(document_ids)))
        session.execute(delete(DocumentPage).where(DocumentPage.document_id.in_(document_ids)))
        session.execute(delete(Document).where(Document.id.in_(document_ids)))
        session.commit()

    return {"status": "ok", "deleted": len(document_ids)}
