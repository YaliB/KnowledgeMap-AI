from abc import ABC, abstractmethod
from datetime import datetime, UTC
from uuid import uuid4

from fastapi import HTTPException

from infrastructure.repositories.abstractions.document_repo import AbstractDocumentRepo
from schemas.document import DocumentResponse, UploadResponse
from services.pdf_service import AbstractPDFService


class AbstractDocumentService(ABC):
    @abstractmethod
    async def upload(self, files: list, subjects: list[str], user_id: str) -> UploadResponse: ...

    @abstractmethod
    async def get_documents(self, user_id: str) -> list[DocumentResponse]: ...

    @abstractmethod
    async def delete_document(self, doc_id: str, user_id: str) -> None: ...


class DocumentService(AbstractDocumentService):
    def __init__(
        self,
        doc_repo: AbstractDocumentRepo,
        pdf_service: AbstractPDFService,
    ):
        self.doc_repo = doc_repo
        self.pdf_service = pdf_service

    async def upload(self, files: list, subjects: list[str], user_id: str) -> UploadResponse:
        if len(files) != len(subjects):
            raise HTTPException(status_code=400, detail="Each file must have a matching subject")
        results = []
        for file, subject in zip(files, subjects):
            content = await file.read()
            self.pdf_service.validate(file.filename, len(content))
            file_path = self.pdf_service.save(content, file.filename)
            page_count = self.pdf_service.count_pages(file_path)
            doc = await self.doc_repo.create_document(
                id=str(uuid4()),
                user_id=user_id,
                filename=file.filename,
                subject=subject,
                file_path=file_path,
                page_count=page_count,
                created_at=datetime.now(UTC).isoformat(),
            )
            results.append(doc)
        return UploadResponse(documents=results)

    async def get_documents(self, user_id: str) -> list[DocumentResponse]:
        return await self.doc_repo.get_user_documents(user_id)

    async def delete_document(self, doc_id: str, user_id: str) -> None:
        await self.doc_repo.delete_document_and_concepts(user_id, doc_id)
