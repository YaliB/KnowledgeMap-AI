import os
import tempfile
from abc import ABC, abstractmethod
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

import boto3
from fastapi import HTTPException
from pypdf import PdfReader

from core.config import settings

_UPLOADS_DIR = Path(__file__).parent.parent / "uploads"
_UPLOADS_DIR.mkdir(exist_ok=True)


class AbstractPDFService(ABC):
    @abstractmethod
    def validate(self, filename: str, size_bytes: int) -> None:
        """Raises HTTPException if file is invalid."""
        ...

    @abstractmethod
    def save(self, file_bytes: bytes, original_filename: str) -> str:
        """Saves file, returns a key/path for later retrieval."""
        ...

    @abstractmethod
    def count_pages(self, file_path: str) -> int: ...

    @abstractmethod
    def chunk_text(self, file_path: str) -> list[str]:
        """Returns ~500 token chunks."""
        ...


class PyPDFService(AbstractPDFService):
    """Local-disk implementation — kept for unit testing."""

    def validate(self, filename: str, size_bytes: int) -> None:
        if not filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files accepted")
        if size_bytes > settings.max_file_size_mb * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large")

    def save(self, file_bytes: bytes, original_filename: str) -> str:
        file_path = _UPLOADS_DIR / f"{uuid4().hex}_{original_filename}"
        file_path.write_bytes(file_bytes)
        return str(file_path)

    def count_pages(self, file_path: str) -> int:
        return len(PdfReader(file_path).pages)

    def chunk_text(self, file_path: str) -> list[str]:
        reader = PdfReader(file_path)
        words = []
        for page in reader.pages:
            text = page.extract_text() or ""
            words.extend(text.split())

        chunks, current = [], []
        for word in words:
            current.append(word)
            if len(current) >= 500:
                chunks.append(" ".join(current))
                current = []
        if current:
            chunks.append(" ".join(current))
        return chunks


class S3PDFService(AbstractPDFService):
    def __init__(self):
        self._client = boto3.client(
            "s3",
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
        )
        self._bucket = settings.s3_bucket

    def validate(self, filename: str, size_bytes: int) -> None:
        if not filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files accepted")
        if size_bytes > settings.max_file_size_mb * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large")

    def save(self, file_bytes: bytes, original_filename: str) -> str:
        """Uploads to S3, returns the S3 key."""
        key = f"uploads/{uuid4().hex}_{original_filename}"
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=file_bytes,
            ContentType="application/pdf",
        )
        return key

    def count_pages(self, file_path: str) -> int:
        with self._temp_pdf(file_path) as tmp:
            return len(PdfReader(tmp).pages)

    def chunk_text(self, file_path: str) -> list[str]:
        with self._temp_pdf(file_path) as tmp:
            reader = PdfReader(tmp)
            words = []
            for page in reader.pages:
                text = page.extract_text() or ""
                words.extend(text.split())

        chunks, current = [], []
        for word in words:
            current.append(word)
            if len(current) >= 500:
                chunks.append(" ".join(current))
                current = []
        if current:
            chunks.append(" ".join(current))
        return chunks

    @contextmanager
    def _temp_pdf(self, s3_key: str):
        """Downloads S3 object to a temp file, yields the path, deletes on exit."""
        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        try:
            self._client.download_fileobj(self._bucket, s3_key, tmp)
            tmp.close()
            yield tmp.name
        finally:
            os.unlink(tmp.name)
