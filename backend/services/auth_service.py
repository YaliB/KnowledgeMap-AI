from abc import ABC, abstractmethod
from datetime import datetime, timedelta, UTC
from uuid import uuid4

from fastapi import HTTPException
import bcrypt

from core.config import settings
from infrastructure.repositories.abstractions.document_repo import AbstractDocumentRepo
from infrastructure.repositories.abstractions.session_repo import AbstractSessionRepo
from infrastructure.repositories.abstractions.user_repo import AbstractUserRepo
from schemas.user import LoginRequest, RegisterRequest, UserResponse


class AbstractAuthService(ABC):
    @abstractmethod
    async def register(self, body: RegisterRequest) -> tuple[UserResponse, str]: ...

    @abstractmethod
    async def login(self, body: LoginRequest) -> tuple[UserResponse, str]: ...

    @abstractmethod
    async def logout(self, session_id: str) -> None: ...


class AuthService(AbstractAuthService):
    def __init__(
        self,
        user_repo: AbstractUserRepo,
        session_repo: AbstractSessionRepo,
        doc_repo: AbstractDocumentRepo,
    ):
        self.user_repo = user_repo
        self.session_repo = session_repo
        self.doc_repo = doc_repo


    async def register(self, body: RegisterRequest) -> tuple[UserResponse, str]:
        existing = await self.user_repo.find_by_email(body.email)
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered")
        hashed = bcrypt.hashpw(body.password.encode(), bcrypt.gensalt()).decode()
        user_id = "user_" + uuid4().hex[:8]
        await self.user_repo.create_user(user_id, body.name, body.email, hashed)
        await self.doc_repo.create_user_node(user_id, body.name, datetime.now(UTC).isoformat())
        session_id = await self._create_session(user_id)
        return UserResponse(user_id=user_id, name=body.name, email=body.email), session_id


    async def login(self, body: LoginRequest) -> tuple[UserResponse, str]:
        user = await self.user_repo.find_by_email(body.email)
        if not user or not bcrypt.checkpw(body.password.encode(), user["hashed_password"].encode()):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        session_id = await self._create_session(user["_id"])
        return UserResponse(user_id=user["_id"], name=user["name"], email=user["email"]), session_id


    async def logout(self, session_id: str) -> None:
        await self.session_repo.delete_session(session_id)


    async def _create_session(self, user_id: str) -> str:
        session_id = "sess_" + uuid4().hex
        expires_at = datetime.now(UTC) + timedelta(days=settings.session_expire_days)
        await self.session_repo.create_session(session_id, user_id, expires_at)
        return session_id
