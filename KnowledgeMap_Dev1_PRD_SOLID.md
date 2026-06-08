# KnowledgeMap AI — Dev 1 PRD (SOLID Edition)
**Developer:** Dev 1 (Foundation + Agent 1)
**Stack:** FastAPI · Neo4j · MongoDB · LangGraph · GPT-4o
**Last updated:** June 8, 2026

> **What changed from the original PRD:** All repositories are now classes implementing abstract interfaces. Services are classes injected via FastAPI `Depends()`. Routers never import repos directly — everything flows through dependency injection. This makes every layer independently testable and swappable.

---

## Overview

You own the entire backend foundation plus Agent 1 (the Extractor). Your output unblocks Dev 2. The moment Agent 1 produces its first real JSON output, share it with Dev 2 immediately — they cannot start agents 2 & 3 without it.

**Your finish line:** `backend/agent1` branch merged to `dev`, sample Agent 1 JSON sent to Dev 2.

---

## Phase 1 — Project Bootstrap

**Goal:** Runnable FastAPI server, correct folder structure, all secrets configured.
**Time estimate:** ~15 min

---

### Step 1 — Init uv project

```bash
uv init knowledgemap-backend
cd knowledgemap-backend
```

Add dependencies to `pyproject.toml`:

```
fastapi
uvicorn[standard]
langchain
langgraph
langchain-openai
openai
neo4j
motor
passlib[bcrypt]
python-multipart
pydantic-settings
python-dotenv
pypdf
```

Then install:

```bash
uv sync
```

---

### Step 2 — Create full folder structure

Run this in one shot:

```bash
mkdir -p \
  core \
  infrastructure/db \
  infrastructure/repositories/abstractions \
  services \
  schemas \
  agents/extractor \
  agents/relationship \
  agents/chat \
  apis/routers \
  uploads
```

Then touch all stub files:

```bash
touch main.py \
  core/config.py core/lifespan.py \
  infrastructure/db/neo4j.py infrastructure/db/mongo.py infrastructure/db/collection.py \
  infrastructure/repositories/abstractions/__init__.py \
  infrastructure/repositories/abstractions/user_repo.py \
  infrastructure/repositories/abstractions/session_repo.py \
  infrastructure/repositories/abstractions/document_repo.py \
  infrastructure/repositories/abstractions/concept_repo.py \
  infrastructure/repositories/user_repo.py \
  infrastructure/repositories/session_repo.py \
  infrastructure/repositories/document_repo.py \
  infrastructure/repositories/concept_repo.py \
  services/pdf_service.py \
  schemas/document.py schemas/concept.py schemas/user.py \
  agents/extractor/state.py agents/extractor/nodes.py agents/extractor/edges.py agents/extractor/graph.py \
  apis/dependencies.py \
  apis/routers/health.py apis/routers/auth.py apis/routers/documents.py apis/routers/graph.py apis/routers/chat.py
```

---

### Step 3 — Write `.env` and `.env.example`

Create `backend/.env`:

```env
# OpenAI
OPENAI_API_KEY=sk-...

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=knowledgemap

# MongoDB
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=knowledgemap

# Session
SESSION_SECRET=your-random-secret
SESSION_EXPIRE_DAYS=7

# File Storage
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=20

# App
ALLOWED_ORIGINS=http://localhost:3000
```

Create `.env.example` with placeholder values. Add `.env` to `.gitignore`.

> **Action:** Share real `.env` values with Dev 2 over WhatsApp now. Never push to GitHub.

---

### Step 4 — Write `core/config.py`

Use `pydantic-settings` `BaseSettings` to load every env var. Every other file in the project imports from here — never use `os.environ` directly elsewhere.

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    neo4j_database: str
    mongodb_uri: str
    mongodb_db: str
    session_secret: str
    session_expire_days: int = 7
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 20
    allowed_origins: str = "http://localhost:3000"

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## Phase 2 — Database Connections

**Goal:** Neo4j and MongoDB connected on startup, constraints and vector index created.
**Time estimate:** ~20 min

---

### Step 5 — Write `infrastructure/db/neo4j.py`

- Use `neo4j.AsyncGraphDatabase.driver()`
- Expose a `get_session()` async context manager
- Call `driver.verify_connectivity()` on startup

---

### Step 6 — Write `infrastructure/db/mongo.py` and `collection.py`

**`mongo.py`:** `AsyncIOMotorClient` singleton with `init_client()` / `get_client()` / `close()`. Idempotent — safe to call twice.

**`collection.py`:** Three collection accessor functions:

```python
def users_col() -> AsyncIOMotorCollection:
    return get_db()["users"]

def sessions_col() -> AsyncIOMotorCollection:
    return get_db()["sessions"]

def chat_history_col() -> AsyncIOMotorCollection:
    return get_db()["chat_history"]
```

---

### Step 7 — Write `core/lifespan.py`

FastAPI lifespan handler — connects both databases on startup, closes on shutdown. Also creates the TTL index on sessions so MongoDB auto-deletes expired ones.

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    init_client(settings.mongodb_uri)
    await neo4j_connect()
    await sessions_col().create_index("expires_at", expireAfterSeconds=0)
    yield
    # shutdown
    await neo4j_close()
    close_mongo()
```

---

### Step 8 — Run constraints and vector index

Create `infrastructure/db/constraints.cypher`:

```cypher
CREATE CONSTRAINT user_id IF NOT EXISTS
FOR (u:User) REQUIRE u.user_id IS UNIQUE;

CREATE CONSTRAINT document_id IF NOT EXISTS
FOR (d:Document) REQUIRE d.id IS UNIQUE;

CREATE CONSTRAINT concept_id IF NOT EXISTS
FOR (c:Concept) REQUIRE c.id IS UNIQUE;

CREATE VECTOR INDEX `concept-embeddings` IF NOT EXISTS
FOR (c:Concept) ON (c.embedding)
OPTIONS { indexConfig: {
  `vector.dimensions`: 1536,
  `vector.similarity_function`: 'cosine'
}};
```

Write a helper that reads and runs this file, then run it once:

```bash
python -c "from infrastructure.db.neo4j import run_constraints; run_constraints()"
```

> **Run once only.** The `IF NOT EXISTS` clauses make it safe to re-run.

---

### Step 9 — Write `main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.lifespan import lifespan
from core.config import settings
from apis.routers import health, auth, documents

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router, prefix="/auth")
app.include_router(documents.router)
```

Write `apis/routers/health.py`:

```python
@router.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
```

Start the server:

```bash
uvicorn main:app --reload
```

> **Checkpoint 1:** `GET /health` returns `{"status": "ok"}`. Ping Dev 2 to hit it from their machine and confirm.

---

## Phase 3 — Auth System

**Goal:** Working register, login, logout. Session cookie flowing through all protected routes.
**Time estimate:** ~35 min

---

### Step 10 — Write `schemas/user.py`

```python
from pydantic import BaseModel, EmailStr

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    user_id: str
    name: str
    email: str
```

---

### Step 11 — Write abstract interfaces in `infrastructure/repositories/abstractions/`

This is the SOLID foundation. Every repo has an interface that the concrete class implements. Routers depend on the interface — never the concrete class directly.

**`abstractions/user_repo.py`:**

```python
from abc import ABC, abstractmethod
from typing import Optional

class AbstractUserRepo(ABC):
    @abstractmethod
    async def create_user(self, user_id: str, name: str, email: str, hashed_password: str) -> dict: ...

    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[dict]: ...
```

**`abstractions/session_repo.py`:**

```python
from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime

class AbstractSessionRepo(ABC):
    @abstractmethod
    async def create_session(self, session_id: str, user_id: str, expires_at: datetime) -> None: ...

    @abstractmethod
    async def find_session(self, session_id: str) -> Optional[dict]: ...

    @abstractmethod
    async def delete_session(self, session_id: str) -> None: ...
```

**`abstractions/document_repo.py`:**

```python
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
```

**`abstractions/concept_repo.py`:**

```python
from abc import ABC, abstractmethod

class AbstractConceptRepo(ABC):
    @abstractmethod
    async def create_concept(self, id: str, user_id: str, document_id: str, name: str,
                              definition: str, subject: str, importance: float,
                              tags: list[str], embedding: list[float], created_at: str) -> dict: ...
```

> **Note for Dev 2:** Extend `AbstractConceptRepo` with a `vector_search()` abstract method when building Agent 2. Never change the existing `create_concept` signature.

---

### Step 12 — Write concrete repo classes

**`infrastructure/repositories/user_repo.py`:**

```python
from motor.motor_asyncio import AsyncIOMotorCollection
from .abstractions.user_repo import AbstractUserRepo
from typing import Optional
from datetime import datetime

class MongoUserRepo(AbstractUserRepo):
    def __init__(self, col: AsyncIOMotorCollection):
        self.col = col

    async def create_user(self, user_id: str, name: str, email: str, hashed_password: str) -> dict:
        doc = {"_id": user_id, "name": name, "email": email,
               "hashed_password": hashed_password, "created_at": datetime.utcnow().isoformat()}
        await self.col.insert_one(doc)
        return doc

    async def find_by_email(self, email: str) -> Optional[dict]:
        return await self.col.find_one({"email": email})
```

**`infrastructure/repositories/session_repo.py`:**

```python
from motor.motor_asyncio import AsyncIOMotorCollection
from .abstractions.session_repo import AbstractSessionRepo
from typing import Optional
from datetime import datetime

class MongoSessionRepo(AbstractSessionRepo):
    def __init__(self, col: AsyncIOMotorCollection):
        self.col = col

    async def create_session(self, session_id: str, user_id: str, expires_at: datetime) -> None:
        await self.col.insert_one({"_id": session_id, "user_id": user_id,
                                    "created_at": datetime.utcnow(), "expires_at": expires_at})

    async def find_session(self, session_id: str) -> Optional[dict]:
        return await self.col.find_one({"_id": session_id})

    async def delete_session(self, session_id: str) -> None:
        await self.col.delete_one({"_id": session_id})
```

**`infrastructure/repositories/document_repo.py`:**

```python
from neo4j import AsyncSession
from .abstractions.document_repo import AbstractDocumentRepo

class Neo4jDocumentRepo(AbstractDocumentRepo):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user_node(self, user_id: str, name: str, created_at: str) -> None:
        await self.session.run(
            "MERGE (u:User {user_id: $user_id}) ON CREATE SET u.name = $name, u.created_at = $created_at",
            user_id=user_id, name=name, created_at=created_at
        )

    async def create_document(self, id, user_id, filename, subject, file_path, page_count, created_at) -> dict:
        result = await self.session.run("""
            MATCH (u:User {user_id: $user_id})
            CREATE (d:Document {id: $id, user_id: $user_id, filename: $filename,
                subject: $subject, file_path: $file_path, status: 'pending',
                page_count: $page_count, created_at: $created_at})
            CREATE (u)-[:OWNS]->(d)
            RETURN d
        """, id=id, user_id=user_id, filename=filename, subject=subject,
             file_path=file_path, page_count=page_count, created_at=created_at)
        return (await result.single())["d"]

    async def get_user_documents(self, user_id: str) -> list[dict]:
        result = await self.session.run(
            "MATCH (u:User {user_id: $user_id})-[:OWNS]->(d:Document) RETURN d ORDER BY d.created_at DESC",
            user_id=user_id
        )
        return [record["d"] async for record in result]

    async def update_document_status(self, user_id: str, doc_id: str, status: str) -> None:
        await self.session.run(
            "MATCH (u:User {user_id: $user_id})-[:OWNS]->(d:Document {id: $id}) SET d.status = $status",
            user_id=user_id, id=doc_id, status=status
        )

    async def delete_document_and_concepts(self, user_id: str, doc_id: str) -> None:
        await self.session.run("""
            MATCH (u:User {user_id: $user_id})-[:OWNS]->(d:Document {id: $id})
            OPTIONAL MATCH (d)-[:CONTAINS]->(c:Concept)
            DETACH DELETE d, c
        """, user_id=user_id, id=doc_id)
```

**`infrastructure/repositories/concept_repo.py`:**

```python
from neo4j import AsyncSession
from .abstractions.concept_repo import AbstractConceptRepo

class Neo4jConceptRepo(AbstractConceptRepo):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_concept(self, id, user_id, document_id, name, definition,
                              subject, importance, tags, embedding, created_at) -> dict:
        result = await self.session.run("""
            MATCH (d:Document {id: $document_id, user_id: $user_id})
            CREATE (c:Concept {id: $id, user_id: $user_id, name: $name,
                definition: $definition, subject: $subject, importance: $importance,
                tags: $tags, embedding: $embedding, created_at: $created_at})
            CREATE (d)-[:CONTAINS]->(c)
            RETURN c
        """, id=id, user_id=user_id, document_id=document_id, name=name,
             definition=definition, subject=subject, importance=importance,
             tags=tags, embedding=embedding, created_at=created_at)
        return (await result.single())["c"]
```

---

### Step 13 — Write `apis/dependencies.py`

This is the single place where abstract interfaces are wired to concrete classes. Routers only ever import from here — never from repo files directly.

```python
from fastapi import Depends, HTTPException, Request
from infrastructure.db.collection import users_col, sessions_col
from infrastructure.db.neo4j import get_neo4j_session
from infrastructure.repositories.user_repo import MongoUserRepo
from infrastructure.repositories.session_repo import MongoSessionRepo
from infrastructure.repositories.document_repo import Neo4jDocumentRepo
from infrastructure.repositories.concept_repo import Neo4jConceptRepo
from infrastructure.repositories.abstractions.user_repo import AbstractUserRepo
from infrastructure.repositories.abstractions.session_repo import AbstractSessionRepo
from infrastructure.repositories.abstractions.document_repo import AbstractDocumentRepo
from infrastructure.repositories.abstractions.concept_repo import AbstractConceptRepo
from services.pdf_service import AbstractPDFService, PyPDFService

# --- Repo providers ---

def get_user_repo() -> AbstractUserRepo:
    return MongoUserRepo(users_col())

def get_session_repo() -> AbstractSessionRepo:
    return MongoSessionRepo(sessions_col())

async def get_document_repo() -> AbstractDocumentRepo:
    async with get_neo4j_session() as session:
        yield Neo4jDocumentRepo(session)

async def get_concept_repo() -> AbstractConceptRepo:
    async with get_neo4j_session() as session:
        yield Neo4jConceptRepo(session)

# --- Service providers ---

def get_pdf_service() -> AbstractPDFService:
    return PyPDFService()

# --- Auth dependency ---

async def get_current_user(
    request: Request,
    session_repo: AbstractSessionRepo = Depends(get_session_repo)
) -> str:
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await session_repo.find_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired")
    return session["user_id"]
```

Every protected route uses `user_id: str = Depends(get_current_user)`.

---

### Step 14 — Write `services/auth_service.py` and `apis/routers/auth.py`

#### Part A — Write `services/auth_service.py`

All business logic lives here. The router just delegates.

```python
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from uuid import uuid4
from passlib.hash import bcrypt
from fastapi import HTTPException
from schemas.user import RegisterRequest, LoginRequest, UserResponse
from infrastructure.repositories.abstractions.user_repo import AbstractUserRepo
from infrastructure.repositories.abstractions.session_repo import AbstractSessionRepo
from infrastructure.repositories.abstractions.document_repo import AbstractDocumentRepo
from core.config import settings

class AbstractAuthService(ABC):
    @abstractmethod
    async def register(self, body: RegisterRequest) -> tuple[UserResponse, str]: ...

    @abstractmethod
    async def login(self, body: LoginRequest) -> tuple[UserResponse, str]:
        """Returns UserResponse + session_id to set as cookie."""
        ...

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
        hashed = bcrypt.hash(body.password)
        user_id = "user_" + uuid4().hex[:8]
        await self.user_repo.create_user(user_id, body.name, body.email, hashed)
        await self.doc_repo.create_user_node(user_id, body.name, datetime.utcnow().isoformat())
        session_id = await self._create_session(user_id)
        return UserResponse(user_id=user_id, name=body.name, email=body.email), session_id

    async def login(self, body: LoginRequest) -> tuple[UserResponse, str]:
        user = await self.user_repo.find_by_email(body.email)
        if not user or not bcrypt.verify(body.password, user["hashed_password"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        session_id = await self._create_session(user["_id"])
        return UserResponse(user_id=user["_id"], name=user["name"], email=user["email"]), session_id

    async def logout(self, session_id: str) -> None:
        await self.session_repo.delete_session(session_id)

    async def _create_session(self, user_id: str) -> str:
        session_id = "sess_" + uuid4().hex
        expires_at = datetime.utcnow() + timedelta(days=settings.session_expire_days)
        await self.session_repo.create_session(session_id, user_id, expires_at)
        return session_id
```

Add to `apis/dependencies.py`:

```python
from services.auth_service import AbstractAuthService, AuthService

def get_auth_service(
    user_repo: AbstractUserRepo = Depends(get_user_repo),
    session_repo: AbstractSessionRepo = Depends(get_session_repo),
    doc_repo: AbstractDocumentRepo = Depends(get_document_repo),
) -> AbstractAuthService:
    return AuthService(user_repo, session_repo, doc_repo)
```

---

#### Part B — Write `apis/routers/auth.py`

Router is now thin — HTTP concerns only. No business logic here.

```python
@router.post("/register")
async def register(
    response: Response,
    body: RegisterRequest,
    auth_service: AbstractAuthService = Depends(get_auth_service),
):
    user, session_id = await auth_service.register(body)
    response.set_cookie("session_id", session_id, httponly=True)
    return user


@router.post("/login")
async def login(
    response: Response,
    body: LoginRequest,
    auth_service: AbstractAuthService = Depends(get_auth_service),
):
    user, session_id = await auth_service.login(body)
    response.set_cookie("session_id", session_id, httponly=True)
    return user


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    auth_service: AbstractAuthService = Depends(get_auth_service),
):
    session_id = request.cookies.get("session_id")
    if session_id:
        await auth_service.logout(session_id)
    response.delete_cookie("session_id")
    return {"message": "logged out"}
```

> **Never store or log plain text passwords anywhere.**

> **Checkpoint:** `curl -X POST /auth/register` -> confirm session cookie set + `:User` node visible in Neo4j Browser.
---

## Phase 4 — PDF Upload & Documents

**Goal:** Upload endpoint accepts PDFs, saves to disk, creates Neo4j `:Document` node linked to `:User`.
**Time estimate:** ~30 min

---

### Step 15 — Write `services/pdf_service.py`

Services follow the same SOLID pattern as repos: abstract interface + concrete class.

```python
from abc import ABC, abstractmethod

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
        # Read all pages, split into ~500 token chunks
        ...
```

---

### Step 16 — Write `schemas/document.py`

```python
from pydantic import BaseModel

class DocumentResponse(BaseModel):
    id: str
    filename: str
    subject: str
    status: str
    page_count: int
    created_at: str

class UploadResponse(BaseModel):
    documents: list[DocumentResponse]
```

---

### Step 17 — Write `apis/routers/documents.py`

All repos and services injected via `Depends()`.

**`POST /upload`**

```python
@router.post("/upload")
async def upload(
    files: list[UploadFile] = File(...),
    subjects: list[str] = Form(...),
    user_id: str = Depends(get_current_user),
    doc_repo: AbstractDocumentRepo = Depends(get_document_repo),
    pdf_service: AbstractPDFService = Depends(get_pdf_service),
):
    results = []
    for file, subject in zip(files, subjects):
        content = await file.read()
        pdf_service.validate(file.filename, len(content))
        file_path = pdf_service.save(content, file.filename)
        page_count = pdf_service.count_pages(file_path)
        doc = await doc_repo.create_document(
            id=str(uuid4()), user_id=user_id, filename=file.filename,
            subject=subject, file_path=file_path,
            page_count=page_count, created_at=datetime.utcnow().isoformat()
        )
        results.append(doc)
    return UploadResponse(documents=results)
```

**`GET /documents`**

```python
@router.get("/documents")
async def get_documents(
    user_id: str = Depends(get_current_user),
    doc_repo: AbstractDocumentRepo = Depends(get_document_repo),
):
    docs = await doc_repo.get_user_documents(user_id)
    return {"documents": docs}
```

**`DELETE /document/{id}`**

```python
@router.delete("/document/{doc_id}")
async def delete_document(
    doc_id: str,
    user_id: str = Depends(get_current_user),
    doc_repo: AbstractDocumentRepo = Depends(get_document_repo),
):
    await doc_repo.delete_document_and_concepts(user_id, doc_id)
    return {"message": "deleted"}
```

> **Checkpoint 3:** `curl POST /upload` with a real PDF. Confirm Neo4j `:Document` node exists with `:OWNS` edge. `GET /documents` returns it.

---

## Phase 5 — Agent 1: Extractor

**Goal:** LangGraph agent that reads a PDF, extracts concepts via GPT-4o, saves them to Neo4j as `:Concept` nodes.
**Time estimate:** ~50 min

> **Do step 18 first and share the schema with Dev 2 before writing any agent code.**

---

### Step 18 — Lock the handoff schema in `schemas/concept.py`

This is the most critical step. Dev 2 cannot start without this.

```python
from pydantic import BaseModel, Field
from typing import List

class ConceptExtracted(BaseModel):
    name: str = Field(..., max_length=60, description="Title case, max 60 chars")
    definition: str = Field(..., description="1-2 sentences, plain English")
    importance: float = Field(..., ge=1.0, le=10.0, description="GPT-4o scoring 1-10")
    tags: List[str] = Field(..., min_length=2, max_length=5, description="2-5 lowercase keywords")

class Agent1Output(BaseModel):
    document_id: str
    user_id: str
    subject: str
    filename: str
    concepts: List[ConceptExtracted]
```

**Field rules (non-negotiable):**

| Field | Rule |
|---|---|
| `name` | String, max 60 chars, title case |
| `definition` | 1-2 sentences, plain English |
| `importance` | Float 1.0-10.0, from GPT-4o |
| `tags` | 2-5 strings, lowercase, stored on Concept node |

> **Action:** Push `schemas/concept.py` to `dev` branch and message Dev 2 the sample output now.

---

### Step 19 — Write `agents/extractor/state.py`

The agent state carries repos as fields so nodes never import infrastructure directly — keeping the agent layer fully decoupled.

```python
from typing import TypedDict, Optional, Any
from schemas.concept import ConceptExtracted

class ExtractorState(TypedDict):
    document_id: str
    user_id: str
    subject: str
    filename: str
    file_path: str
    raw_chunks: list[str]
    concepts: list[ConceptExtracted]
    error: Optional[str]
    # injected dependencies — passed in at graph.invoke() time
    concept_repo: Any   # AbstractConceptRepo
    document_repo: Any  # AbstractDocumentRepo
    pdf_service: Any    # AbstractPDFService
```

---

### Step 20 — Write `agents/extractor/nodes.py`

Nodes read repos and services from state — no direct imports of infrastructure anywhere in this file.

**`read_pdf_node(state)`**

```python
async def read_pdf_node(state: ExtractorState) -> dict:
    chunks = state["pdf_service"].chunk_text(state["file_path"])
    return {"raw_chunks": chunks}
```

**`extract_concepts_node(state)`**

```python
async def extract_concepts_node(state: ExtractorState) -> dict:
    prompt = f"""
You are an expert knowledge extractor. Given the following text chunks from a document about {state['subject']}, extract the key concepts a student needs to understand.

Return ONLY a valid JSON array. No preamble, no markdown, no explanation.

Each item must have exactly these fields:
- name: string, title case, max 60 characters
- definition: string, 1-2 plain English sentences
- importance: float between 1.0 and 10.0
- tags: array of 2-5 lowercase keyword strings

Text chunks:
{state['raw_chunks']}
"""
    # call GPT-4o, parse JSON, validate with ConceptExtracted
    ...
    return {"concepts": parsed_concepts}
```

**`save_concepts_node(state)`**

```python
async def save_concepts_node(state: ExtractorState) -> dict:
    for concept in state["concepts"]:
        embedding = await generate_embedding(concept.name + " " + concept.definition)
        await state["concept_repo"].create_concept(
            id=str(uuid4()), user_id=state["user_id"],
            document_id=state["document_id"], name=concept.name,
            definition=concept.definition, subject=state["subject"],
            importance=concept.importance, tags=concept.tags,
            embedding=embedding, created_at=datetime.utcnow().isoformat()
        )
    await state["document_repo"].update_document_status(
        state["user_id"], state["document_id"], "done"
    )
    return {}
```

> **Note:** Generate the OpenAI embedding in `save_concepts_node` before calling `create_concept` — `text-embedding-3-small`, 1536 dimensions.

---

### Step 21 — Write `agents/extractor/edges.py`

```python
def route_after_extract(state: ExtractorState) -> str:
    if state.get("error"):
        return "error_node"
    if not state.get("concepts"):
        return "error_node"
    return "save_concepts_node"
```

---

### Step 22 — Write `agents/extractor/graph.py`

```python
from langgraph.graph import StateGraph
from .state import ExtractorState
from .nodes import read_pdf_node, extract_concepts_node, save_concepts_node, error_node
from .edges import route_after_extract

def build_extractor_graph():
    graph = StateGraph(ExtractorState)
    graph.add_node("read_pdf_node", read_pdf_node)
    graph.add_node("extract_concepts_node", extract_concepts_node)
    graph.add_node("save_concepts_node", save_concepts_node)
    graph.add_node("error_node", error_node)

    graph.set_entry_point("read_pdf_node")
    graph.add_edge("read_pdf_node", "extract_concepts_node")
    graph.add_conditional_edges("extract_concepts_node", route_after_extract)
    graph.add_edge("save_concepts_node", "__end__")
    graph.add_edge("error_node", "__end__")

    return graph.compile()

extractor_graph = build_extractor_graph()
```

The graph is invoked from the `/extract` router (Dev 2's file), with repos passed into state:

```python
# How Dev 2 calls it from apis/routers/graph.py:
await extractor_graph.ainvoke({
    "document_id": doc_id,
    "user_id": user_id,
    "subject": subject,
    "filename": filename,
    "file_path": file_path,
    "raw_chunks": [],
    "concepts": [],
    "error": None,
    "concept_repo": concept_repo,    # injected via Depends()
    "document_repo": document_repo,  # injected via Depends()
    "pdf_service": pdf_service,      # injected via Depends()
})
```

---

## Phase 6 — Git & Dev 2 Handoff

**Goal:** All your branches clean and merged to `dev`. Dev 2 has everything they need to start.
**Time estimate:** ~10 min

---

### Step 23 — Push branches in order

```bash
# Branch 1: foundation
git checkout -b backend/setup
git add pyproject.toml uv.lock .env.example .gitignore core/ infrastructure/db/ main.py apis/routers/health.py
git commit -m "feat(setup): FastAPI project structure, config, DB connections, constraints"
git push origin backend/setup

# Branch 2: upload + auth
git checkout -b backend/upload
git add infrastructure/repositories/ services/ schemas/user.py schemas/document.py apis/
git commit -m "feat(upload): SOLID repo interfaces, DI wiring, auth system, PDF upload endpoints"
git push origin backend/upload

# Branch 3: agent 1
git checkout -b backend/agent1
git add schemas/concept.py agents/extractor/
git commit -m "feat(agent1): Extractor agent, concept schema, Neo4j concept nodes"
git push origin backend/agent1

# Merge all to dev
git checkout dev
git merge backend/setup
git merge backend/upload
git merge backend/agent1
git push origin dev
```

---

### Step 24 — Share Agent 1 sample output with Dev 2

Run the extractor on a real PDF and save the output:

```bash
python -c "
import asyncio
from agents.extractor.graph import extractor_graph
from infrastructure.repositories.concept_repo import Neo4jConceptRepo
from infrastructure.repositories.document_repo import Neo4jDocumentRepo
from services.pdf_service import PyPDFService

result = asyncio.run(extractor_graph.ainvoke({
  'document_id': 'test_001',
  'user_id': 'user_test',
  'subject': 'Linear Algebra',
  'filename': 'test.pdf',
  'file_path': './uploads/test.pdf',
  'raw_chunks': [],
  'concepts': [],
  'error': None,
  'concept_repo': Neo4jConceptRepo(...),
  'document_repo': Neo4jDocumentRepo(...),
  'pdf_service': PyPDFService(),
}))
import json; print(json.dumps([c.dict() for c in result['concepts']], indent=2))
"
```

Send the printed JSON to Dev 2 over WhatsApp. This is checkpoint 2.

---

## Checkpoints Summary

| # | What | How to verify |
|---|---|---|
| 1 | `/health` returns OK | Start server, Dev 2 hits it from their machine |
| 2 | Agent 1 schema agreed | Share `schemas/concept.py` + sample JSON with Dev 2 |
| 3 | `/upload` saves document | curl POST with real PDF, check Neo4j Browser |
| 4 | Agent 1 runs end-to-end | Run extractor, confirm `:Concept` nodes in Neo4j |

---

## Files You Own (Complete List)

| File | Purpose |
|---|---|
| `main.py` | FastAPI entry point |
| `core/config.py` | All env vars via pydantic-settings |
| `core/lifespan.py` | DB startup/shutdown + TTL index creation |
| `infrastructure/db/neo4j.py` | Neo4j driver |
| `infrastructure/db/mongo.py` | MongoDB client singleton |
| `infrastructure/db/collection.py` | Collection accessor functions |
| `infrastructure/db/constraints.cypher` | Constraints + vector index |
| `infrastructure/repositories/abstractions/user_repo.py` | AbstractUserRepo interface |
| `infrastructure/repositories/abstractions/session_repo.py` | AbstractSessionRepo interface |
| `infrastructure/repositories/abstractions/document_repo.py` | AbstractDocumentRepo interface |
| `infrastructure/repositories/abstractions/concept_repo.py` | AbstractConceptRepo interface (Dev 2 extends with vector search) |
| `infrastructure/repositories/user_repo.py` | MongoUserRepo concrete class |
| `infrastructure/repositories/session_repo.py` | MongoSessionRepo concrete class |
| `infrastructure/repositories/document_repo.py` | Neo4jDocumentRepo concrete class |
| `infrastructure/repositories/concept_repo.py` | Neo4jConceptRepo — `create_concept()` only |
| `services/pdf_service.py` | AbstractPDFService + PyPDFService |
| `schemas/document.py` | Document Pydantic models |
| `schemas/concept.py` | **Handoff schema — lock with Dev 2 first** |
| `schemas/user.py` | User Pydantic models |
| `agents/extractor/state.py` | ExtractorState TypedDict (includes injected repos) |
| `agents/extractor/nodes.py` | read_pdf, extract_concepts, save_concepts — read repos from state |
| `agents/extractor/edges.py` | Routing logic |
| `agents/extractor/graph.py` | Compiled LangGraph graph |
| `apis/dependencies.py` | **All DI wiring lives here** — repo providers + get_current_user |
| `apis/routers/health.py` | GET /health |
| `apis/routers/auth.py` | POST /register, /login, /logout — repos via Depends() |
| `apis/routers/documents.py` | POST /upload, GET /documents, DELETE /document/{id} — repos via Depends() |

---

## What Dev 2 Owns (Do Not Touch)

- `agents/relationship/` — Agent 2
- `agents/chat/` — Agent 3
- `agents/pipeline.py` — LangGraph orchestrator
- `services/graph_service.py` — Graph structure builder
- `services/db_service.py` — High-level DB ops for agents
- `apis/routers/graph.py` — /extract, /graph, /concept endpoints
- `apis/routers/chat.py` — /chat endpoint
- `schemas/chat.py` — ChatMessage, ChatResponse
- Vector search methods added to `AbstractConceptRepo` + `Neo4jConceptRepo`

> **Note for Dev 2:** To add vector search, extend `AbstractConceptRepo` with a `vector_search()` abstract method and implement it in `Neo4jConceptRepo`. Add `get_concept_repo()` to `dependencies.py`. Never import `Neo4jConceptRepo` directly in routers.

---

## Rules

- Never commit `.env` — only `.env.example`
- Never store plain text passwords
- Never use `os.environ` directly — always import from `core/config.py`
- Run `constraints.cypher` once only
- Don't change `schemas/concept.py` after Dev 2 has confirmed it — breaking the handoff schema breaks their entire pipeline
- Push to feature branch first, then merge to `dev`, never commit directly to `main`
- **Routers never import concrete repo classes** — only abstract interfaces and providers from `dependencies.py`
- **Agents never import repos directly** — repos travel through `ExtractorState`
