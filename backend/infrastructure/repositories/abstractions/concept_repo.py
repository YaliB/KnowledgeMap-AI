from abc import ABC, abstractmethod


class AbstractConceptRepo(ABC):
    @abstractmethod
    async def create_concept(self, id: str, user_id: str, document_id: str, name: str,
                              definition: str, level: str, subject: str, parent: str | None,
                              importance: float, tags: list[str], embedding: list[float],
                              created_at: str) -> dict: ...

    @abstractmethod
    async def get_concepts_for_user(self, user_id: str) -> list[dict]: ...

    @abstractmethod
    async def get_concept_by_id(self, concept_id: str, user_id: str) -> dict | None: ...

    @abstractmethod
    async def get_concept_neighbors(self, concept_id: str, user_id: str) -> list[dict]: ...

    @abstractmethod
    async def create_related_to(self, concept_a_id: str, concept_b_id: str, props: dict) -> None: ...

    @abstractmethod
    async def vector_similarity_search(self, embedding: list[float], user_id: str,
                                       top_k: int = 10) -> list[dict]: ...

    @abstractmethod
    async def get_full_graph(self, user_id: str) -> dict: ...

    @abstractmethod
    async def get_distinct_subjects(self, user_id: str) -> list[dict]: ...
