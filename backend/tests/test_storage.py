from __future__ import annotations

import io
import sys
import types
from unittest.mock import patch
from typing import Any, cast

from fastapi import UploadFile

import pytest
from PIL import Image

from app.services.storage import UploadLike, save_upload


class DummyUpload(UploadLike):
    def __init__(self, filename: str, content: bytes) -> None:
        self.filename = filename
        self.file = io.BytesIO(content)


def test_save_upload_rejects_unknown_extension(tmp_path, monkeypatch):
    monkeypatch.setenv("STRICT_MIME_VALIDATION", "0")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    upload = cast(UploadFile, DummyUpload("notes.txt", b"hello"))
    with pytest.raises(ValueError) as error:
        save_upload(upload)
    assert str(error.value) == "unsupported_file_type"


def test_save_upload_pdf_converts_pages(tmp_path, monkeypatch):
    monkeypatch.setenv("STRICT_MIME_VALIDATION", "0")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    upload = cast(UploadFile, DummyUpload("sample.pdf", b"%PDF-1.4"))
    fake_image = Image.new("RGB", (10, 10), "white")
    fake_image_two = Image.new("RGB", (10, 10), "white")

    fake_pdf2image = cast(Any, types.ModuleType("pdf2image"))
    fake_pdf2image.convert_from_path = lambda *args, **kwargs: [fake_image, fake_image_two]
    with patch.dict(sys.modules, {"pdf2image": fake_pdf2image}):
        document_id, image_path, image_url, pages = save_upload(upload)

    assert document_id
    assert image_path.endswith(".png")
    assert image_url.endswith(".png")
    assert len(pages) == 2
    assert (tmp_path / f"{document_id}-page-0.png").exists()
    assert (tmp_path / f"{document_id}-page-1.png").exists()


def test_save_upload_rejects_large_files(tmp_path, monkeypatch):
    monkeypatch.setenv("STRICT_MIME_VALIDATION", "0")
    monkeypatch.setenv("MAX_UPLOAD_MB", "0")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    upload = cast(UploadFile, DummyUpload("sample.png", b"x"))
    with pytest.raises(ValueError) as error:
        save_upload(upload)
    assert str(error.value) == "file_too_large"
