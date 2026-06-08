from abc import ABC, abstractmethod


class AbstractConceptRepo(ABC):
    @abstractmethod
    async def create_concept(self, id: str, user_id: str, document_id: str, name: str,
                              definition: str, subject: str, importance: float,
                              tags: list[str], embedding: list[float], created_at: str) -> dict: ...
