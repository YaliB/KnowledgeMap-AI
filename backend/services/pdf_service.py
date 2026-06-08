from abc import ABC, abstractmethod
from uuid import uuid4

from fastapi import HTTPException
from pypdf import PdfReader

from core.config import settings


class AbstractPDFService(ABC):
    @abstractmethod
    def validate(self, filename: str, size_bytes: int) -> None:
        """Raises HTTPException if file is invalid."""
        ...

    @abstractmethod
    def save(self, file_bytes: bytes, original_filename: str) -> str:
        """Saves to disk, returns file_path."""
        ...

    @abstractmethod
    def count_pages(self, file_path: str) -> int: ...

    @abstractmethod
    def chunk_text(self, file_path: str) -> list[str]:
        """Returns ~500 token chunks."""
        ...


class PyPDFService(AbstractPDFService):
    def validate(self, filename: str, size_bytes: int) -> None:
        if not filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files accepted")
        if size_bytes > settings.max_file_size_mb * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large")

    def save(self, file_bytes: bytes, original_filename: str) -> str:
        file_path = f"{settings.upload_dir}/{uuid4().hex}_{original_filename}"
        with open(file_path, "wb") as f:
            f.write(file_bytes)
        return file_path

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
