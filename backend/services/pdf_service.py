from abc import ABC, abstractmethod


class AbstractPDFService(ABC):
    @abstractmethod
    async def extract_text(self, file_path: str) -> str: ...

    @abstractmethod
    def count_pages(self, file_path: str) -> int: ...


class PyPDFService(AbstractPDFService):
    async def extract_text(self, file_path: str) -> str:
        raise NotImplementedError

    def count_pages(self, file_path: str) -> int:
        raise NotImplementedError
