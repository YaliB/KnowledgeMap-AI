from abc import ABC, abstractmethod
from typing import Optional


class AbstractUserRepo(ABC):
    @abstractmethod
    async def create_user(self, user_id: str, name: str, email: str, hashed_password: str) -> dict: ...

    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[dict]: ...
