from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional


class AbstractSessionRepo(ABC):
    @abstractmethod
    async def create_session(self, session_id: str, user_id: str, expires_at: datetime) -> None: ...

    @abstractmethod
    async def find_session(self, session_id: str) -> Optional[dict]: ...

    @abstractmethod
    async def delete_session(self, session_id: str) -> None: ...
