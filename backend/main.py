from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.lifespan import lifespan
from apis.routers import health, auth, documents
from apis.routers.graph import router as graph_router
from apis.routers.chat import router as chat_router

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router, prefix="/auth")
app.include_router(documents.router)
app.include_router(graph_router)
app.include_router(chat_router)
