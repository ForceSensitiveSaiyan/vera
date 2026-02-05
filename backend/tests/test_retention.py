from datetime import timedelta
from pathlib import Path

from app.db.session import Base, engine, get_session
from app.models.documents import Document, DocumentPage
from app.services.retention import cleanup_documents
from app.utils.time import utcnow


def _reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_cleanup_documents_removes_files(tmp_path, monkeypatch):
    _reset_db()
    monkeypatch.setenv("RETENTION_DAYS", "30")
    monkeypatch.setenv("RETENTION_TRIGGER", "post_review")
    monkeypatch.setenv("RETENTION_MODE", "delete")

    doc_id = "doc-retention"
    document_path = Path(tmp_path / "doc.pdf")
    page_path = Path(tmp_path / "doc-page-0.png")
    document_path.write_bytes(b"doc")
    page_path.write_bytes(b"page")

    with get_session() as session:
        session.add(
            Document(
                id=doc_id,
                image_path=str(document_path),
                image_width=100,
                image_height=200,
                status="validated",
                structured_fields="{}",
                page_count=1,
                review_complete_at=utcnow() - timedelta(days=31),
            )
        )
        session.add(
            DocumentPage(
                id="page-1",
                document_id=doc_id,
                page_index=0,
                image_path=str(page_path),
                image_width=100,
                image_height=200,
                status="validated",
                review_complete_at=utcnow() - timedelta(days=31),
            )
        )
        session.commit()

    result = cleanup_documents()

    assert result["deleted"] == 1
    assert not document_path.exists()
    assert not page_path.exists()

    with get_session() as session:
        assert session.get(Document, doc_id) is None
