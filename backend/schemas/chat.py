from pydantic import BaseModel
from typing import List, Optional


class ChatSource(BaseModel):
    concept_id: str
    concept_name: str
    document_name: str
    subject: str
    relevance_score: float           # 0.0–1.0 from Neo4j vector retrieval


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    sources: List[ChatSource]        # max 5, sorted by relevance_score DESC
    highlighted_node_ids: List[str]  # concept IDs — frontend glows these nodes
