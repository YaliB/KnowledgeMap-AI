from abc import ABC, abstractmethod


class AbstractDocumentRepo(ABC):
    @abstractmethod
    async def create_user_node(self, user_id: str, name: str, created_at: str) -> None: ...

    @abstractmethod
    async def create_document(self, id: str, user_id: str, filename: str, subject: str,
                               file_path: str, page_count: int, created_at: str) -> dict: ...

    @abstractmethod
    async def get_user_documents(self, user_id: str) -> list[dict]: ...

    @abstractmethod
    async def update_document_status(self, user_id: str, doc_id: str, status: str) -> None: ...

    @abstractmethod
    async def delete_document_and_concepts(self, user_id: str, doc_id: str) -> None: ...

    @abstractmethod
    async def get_document_for_concept(self, concept_id: str, user_id: str) -> list[dict]: ...
