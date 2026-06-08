# KnowledgeMap AI — Dev 1 PRD
**Developer:** Dev 1 (Foundation + Agent 1)
**Stack:** FastAPI · Neo4j · MongoDB · LangGraph · GPT-4o
**Last updated:** June 8, 2026

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
  infrastructure/repositories \
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
  infrastructure/repositories/document_repo.py infrastructure/repositories/user_repo.py infrastructure/repositories/session_repo.py infrastructure/repositories/concept_repo.py \
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

**`mongo.py`:** `AsyncIOMotorClient` singleton, returns the database handle.

**`collection.py`:** Exports three collection references used everywhere else:

```python
users_col       # infrastructure/db/collection.py
sessions_col
chat_history_col
```

---

### Step 7 — Write `core/lifespan.py`

FastAPI lifespan handler — connects both databases on startup, closes on shutdown:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup: connect neo4j, connect mongo
    yield
    # shutdown: close neo4j driver, close mongo client
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

CREATE VECTOR INDEX concept-embeddings IF NOT EXISTS
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
**Time estimate:** ~30 min

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

### Step 11 — Write `infrastructure/repositories/user_repo.py`

Two async functions:

| Function | What it does |
|---|---|
| `create_user(user_id, name, email, hashed_password)` | Inserts into `users` collection |
| `find_by_email(email)` | Returns user doc or `None` |

MongoDB document shape:

```json
{
  "_id": "user_abc123",
  "name": "John Doe",
  "email": "john@example.com",
  "hashed_password": "$2b$12$...",
  "created_at": "2026-06-08T10:00:00Z",
  "last_login": "2026-06-08T12:00:00Z"
}
```

---

### Step 12 — Write `infrastructure/repositories/session_repo.py`

Three async functions:

| Function | What it does |
|---|---|
| `create_session(session_id, user_id, expires_at)` | Inserts into `sessions` collection |
| `find_session(session_id)` | Returns session doc or `None` |
| `delete_session(session_id)` | Removes session doc on logout |

MongoDB document shape:

```json
{
  "_id": "sess_xyz789",
  "user_id": "user_abc123",
  "created_at": "2026-06-08T12:00:00Z",
  "expires_at": "2026-06-15T12:00:00Z"
}
```

Add a TTL index on `expires_at` — MongoDB auto-deletes expired sessions.

---

### Step 13 — Write `apis/routers/auth.py`

**`POST /auth/register`**
1. Check email not already in `users_col`
2. Hash password: `passlib.hash.bcrypt.hash(plain_password)`
3. Generate `user_id = "user_" + uuid4().hex[:8]`
4. Insert into MongoDB `users` collection
5. MERGE `:User` node in Neo4j (query from Section 4.1 of the architecture doc)
6. Create session, set `httpOnly` cookie
7. Return `UserResponse`

**`POST /auth/login`**
1. Find user by email
2. `bcrypt.verify(plain_password, hashed_password)` — raise 401 if fails
3. Create new session in MongoDB
4. Set `httpOnly` cookie with `session_id`
5. Return `UserResponse`

**`POST /auth/logout`**
1. Read `session_id` from cookie
2. Delete session from MongoDB
3. Clear cookie
4. Return `{"message": "logged out"}`

> **Never store or log plain text passwords anywhere.**

---

### Step 14 — Write `apis/dependencies.py`

```python
async def get_current_user(request: Request) -> str:
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

### Step 15 — Write Neo4j :User MERGE in `document_repo.py`

Called during `/register` after MongoDB insert:

```cypher
MERGE (u:User {user_id: $user_id})
ON CREATE SET u.name = $name, u.created_at = $created_at
RETURN u
```

> **Checkpoint:** `curl -X POST /auth/register` → confirm session cookie set + `:User` node visible in Neo4j Browser.

---

## Phase 4 — PDF Upload & Documents

**Goal:** Upload endpoint accepts PDFs, saves to disk, creates Neo4j `:Document` node linked to `:User`.
**Time estimate:** ~25 min

---

### Step 16 — Write `services/pdf_service.py`

Responsibilities:

| Task | Detail |
|---|---|
| Validate file type | Reject non-PDF |
| Validate size | Raise 400 if > `MAX_FILE_SIZE_MB` |
| Save to disk | `UPLOAD_DIR/{uuid}_{original_filename}` |
| Count pages | Use `pypdf.PdfReader` |
| Chunk text | Split into ~500 token chunks, return as `list[str]` |

Returns: `{"file_path": str, "page_count": int, "chunks": list[str]}`

---

### Step 17 — Write `schemas/document.py`

```python
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

### Step 18 — Complete `infrastructure/repositories/document_repo.py`

Four Cypher queries (copy from Section 4.1 of the architecture doc):

| Function | Query |
|---|---|
| `create_document(...)` | CREATE `:Document` node + `:OWNS` edge |
| `get_user_documents(user_id)` | MATCH all docs for user |
| `update_document_status(user_id, doc_id, status)` | SET `d.status` |
| `delete_document_and_concepts(user_id, doc_id)` | DETACH DELETE doc + concepts |

---

### Step 19 — Write `apis/routers/documents.py`

**`POST /upload`**
- Accept `multipart/form-data`: `files[]` (PDF list) + `subjects[]` (string list, same order)
- For each file: run `pdf_service` → create Neo4j `:Document` node with `status: "pending"`
- Return `UploadResponse`

**`GET /documents`**
- Protected by `get_current_user`
- Returns all documents for the current user from Neo4j

**`DELETE /document/{id}`**
- Protected by `get_current_user`
- Calls `delete_document_and_concepts()`

> **Checkpoint 3:** `curl POST /upload` with a real PDF. Confirm Neo4j `:Document` node exists with `:OWNS` edge. `GET /documents` returns it.

---

## Phase 5 — Agent 1: Extractor

**Goal:** LangGraph agent that reads a PDF, extracts concepts via GPT-4o, saves them to Neo4j as `:Concept` nodes.
**Time estimate:** ~45 min

> **Do step 20 first and share the schema with Dev 2 before writing any agent code.**

---

### Step 20 — Lock the handoff schema in `schemas/concept.py`

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
| `importance` | Float 1.0–10.0, from GPT-4o |
| `tags` | 2-5 strings, lowercase, stored on Concept node |

> **Action:** Push `schemas/concept.py` to `dev` branch and message Dev 2 the sample output now.

---

### Step 21 — Write `agents/extractor/state.py`

```python
from typing import TypedDict, Optional
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
```

---

### Step 22 — Write `agents/extractor/nodes.py`

Three node functions:

**`read_pdf_node(state)`**
- Call `pdf_service.chunk_pdf(state["file_path"])`
- Update `state["raw_chunks"]`

**`extract_concepts_node(state)`**
- Build GPT-4o prompt (see below)
- Parse response as `list[ConceptExtracted]` using Pydantic
- Update `state["concepts"]`

**`save_concepts_node(state)`**
- For each concept: generate UUID, call `concept_repo.create_concept()`
- Update document status to `"done"` via `document_repo.update_document_status()`

**GPT-4o prompt template:**

```
You are an expert knowledge extractor. Given the following text chunks from a document about {subject}, extract the key concepts a student needs to understand.

Return ONLY a valid JSON array. No preamble, no markdown, no explanation.

Each item must have exactly these fields:
- name: string, title case, max 60 characters
- definition: string, 1-2 plain English sentences
- importance: float between 1.0 and 10.0
- tags: array of 2-5 lowercase keyword strings

Text chunks:
{chunks}
```

---

### Step 23 — Write `agents/extractor/edges.py`

```python
def route_after_extract(state: ExtractorState) -> str:
    if state.get("error"):
        return "error_node"
    if not state.get("concepts"):
        return "error_node"
    return "save_concepts_node"
```

---

### Step 24 — Write `agents/extractor/graph.py`

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

---

### Step 25 — Write `concept_repo.py` (your portion)

Your responsibility is `create_concept()`. Dev 2 adds vector search later.

Cypher (from Section 4.2):

```cypher
MATCH (d:Document {id: $document_id, user_id: $user_id})
CREATE (c:Concept {
  id: $id,
  user_id: $user_id,
  name: $name,
  definition: $definition,
  subject: $subject,
  importance: $importance,
  tags: $tags,
  embedding: $embedding,
  created_at: $created_at
})
CREATE (d)-[:CONTAINS]->(c)
RETURN c
```

> **Note:** Generate the OpenAI embedding for each concept in `save_concepts_node` before calling this — `text-embedding-ada-002`, 1536 dimensions.

---

## Phase 6 — Git & Dev 2 Handoff

**Goal:** All your branches clean and merged to `dev`. Dev 2 has everything they need to start.
**Time estimate:** ~10 min

---

### Step 26 — Push branches in order

```bash
# Branch 1: foundation
git checkout -b backend/setup
git add .
git commit -m "feat(setup): FastAPI project structure, config, DB connections, constraints"
git push origin backend/setup

# Branch 2: upload
git checkout -b backend/upload
git commit -m "feat(upload): PDF upload, document CRUD, auth system"
git push origin backend/upload

# Branch 3: agent 1
git checkout -b backend/agent1
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

### Step 27 — Share Agent 1 sample output with Dev 2

Run the extractor on a real PDF and save the output:

```bash
python -c "
from agents.extractor.graph import extractor_graph
result = extractor_graph.invoke({
  'document_id': 'test_001',
  'user_id': 'user_test',
  'subject': 'Linear Algebra',
  'filename': 'test.pdf',
  'file_path': './uploads/test.pdf',
  'raw_chunks': [],
  'concepts': [],
  'error': None
})
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
| `core/lifespan.py` | DB startup/shutdown |
| `infrastructure/db/neo4j.py` | Neo4j driver |
| `infrastructure/db/mongo.py` | MongoDB client |
| `infrastructure/db/collection.py` | Collection refs |
| `infrastructure/db/constraints.cypher` | Constraints + vector index |
| `infrastructure/repositories/document_repo.py` | Document Cypher queries |
| `infrastructure/repositories/user_repo.py` | User MongoDB queries |
| `infrastructure/repositories/session_repo.py` | Session MongoDB queries |
| `infrastructure/repositories/concept_repo.py` | `create_concept()` only (Dev 2 adds rest) |
| `services/pdf_service.py` | PDF read, validate, chunk, save |
| `schemas/document.py` | Document Pydantic models |
| `schemas/concept.py` | **Handoff schema — lock with Dev 2 first** |
| `schemas/user.py` | User Pydantic models |
| `agents/extractor/state.py` | ExtractorState TypedDict |
| `agents/extractor/nodes.py` | read_pdf, extract_concepts, save_concepts |
| `agents/extractor/edges.py` | Routing logic |
| `agents/extractor/graph.py` | Compiled LangGraph graph |
| `apis/dependencies.py` | `get_current_user` dependency |
| `apis/routers/health.py` | GET /health |
| `apis/routers/auth.py` | POST /register, /login, /logout |
| `apis/routers/documents.py` | POST /upload, GET /documents, DELETE /document/{id} |

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
- Vector search queries in `concept_repo.py`

---

## Rules

- Never commit `.env` — only `.env.example`
- Never store plain text passwords
- Never use `os.environ` directly — always import from `core/config.py`
- Run `constraints.cypher` once only
- Don't change `schemas/concept.py` after Dev 2 has confirmed it — breaking the handoff schema breaks their entire pipeline
- Push to feature branch first, then merge to `dev`, never commit directly to `main`
