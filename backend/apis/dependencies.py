from fastapi import Depends, HTTPException, Request

from services.auth_service import AbstractAuthService, AuthService
from infrastructure.db.collection import users_collection, sessions_collection
from infrastructure.db.neo4j import get_session
from infrastructure.repositories.user_repo import MongoUserRepo
from infrastructure.repositories.session_repo import MongoSessionRepo
from infrastructure.repositories.document_repo import Neo4jDocumentRepo
from infrastructure.repositories.concept_repo import Neo4jConceptRepo
from infrastructure.repositories.abstractions.user_repo import AbstractUserRepo
from infrastructure.repositories.abstractions.session_repo import AbstractSessionRepo
from infrastructure.repositories.abstractions.document_repo import AbstractDocumentRepo
from infrastructure.repositories.abstractions.concept_repo import AbstractConceptRepo
from core.config import settings
from services.pdf_service import AbstractPDFService, S3PDFService, PyPDFService
from services.document_service import AbstractDocumentService, DocumentService


# --- Repo providers ---

def get_user_repo() -> AbstractUserRepo:
    return MongoUserRepo(users_collection())


def get_session_repo() -> AbstractSessionRepo:
    return MongoSessionRepo(sessions_collection())


async def get_document_repo() -> AbstractDocumentRepo:
    async with get_session() as session:
        yield Neo4jDocumentRepo(session)


async def get_concept_repo() -> AbstractConceptRepo:
    async with get_session() as session:
        yield Neo4jConceptRepo(session)


# --- Service providers ---

def get_pdf_service() -> AbstractPDFService:
    return S3PDFService() if settings.use_s3 else PyPDFService()


def get_document_service(
    doc_repo: AbstractDocumentRepo = Depends(get_document_repo),
    pdf_service: AbstractPDFService = Depends(get_pdf_service),
) -> AbstractDocumentService:
    return DocumentService(doc_repo, pdf_service)


def get_auth_service(
    user_repo: AbstractUserRepo = Depends(get_user_repo),
    session_repo: AbstractSessionRepo = Depends(get_session_repo),
    doc_repo: AbstractDocumentRepo = Depends(get_document_repo),
) -> AbstractAuthService:
    return AuthService(user_repo, session_repo, doc_repo)


# --- Auth dependency ---

async def get_current_user(
    request: Request,
    session_repo: AbstractSessionRepo = Depends(get_session_repo),
) -> str:
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await session_repo.find_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired")
    return session["user_id"]
