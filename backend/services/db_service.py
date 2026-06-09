import asyncio
from datetime import datetime, UTC
from uuid import uuid4

from langchain_openai import OpenAIEmbeddings

from core.config import settings
from infrastructure.db.neo4j import get_session
from infrastructure.repositories.concept_repo import Neo4jConceptRepo

_embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=settings.openai_api_key)


async def save_concepts_from_extractor_agent(document_id: str, user_id: str,
                                             concepts: list[dict]) -> list[dict]:
    # Embed all concepts in parallel — one API call per concept but all in-flight at once
    embeddings = await asyncio.gather(*[
        _embeddings.aembed_query(c["name"] + " " + c["definition"])
        for c in concepts
    ])

    created = []
    async with get_session() as session:
        repo = Neo4jConceptRepo(session)
        for concept, embedding in zip(concepts, embeddings):
            concept_id = str(uuid4())
            await repo.create_concept(
                id=concept_id,
                user_id=user_id,
                document_id=document_id,
                name=concept["name"],
                definition=concept["definition"],
                level=concept.get("level", "subtopic"),
                subject=concept["subject"],
                parent=concept.get("parent"),
                importance=concept["importance"],
                tags=concept["tags"],
                embedding=embedding,
                created_at=datetime.now(UTC).isoformat(),
            )
            created.append({**concept, "id": concept_id, "embedding": embedding})
    return created


async def save_relationships_from_relationship_agent(relationships: list[dict]) -> None:
    async with get_session() as session:
        repo = Neo4jConceptRepo(session)
        for rel in relationships:
            await repo.create_related_to(
                concept_a_id=rel["concept_a_id"],
                concept_b_id=rel["concept_b_id"],
                props={
                    "weight": rel["weight"],
                    "rel_type": rel["rel_type"],
                    "cross_subject": rel["cross_subject"],
                    "explanation": rel["explanation"],
                    "created_at": datetime.now(UTC).isoformat(),
                },
            )


async def set_document_status(user_id: str, document_id: str, status: str) -> None:
    async with get_session() as session:
        from infrastructure.repositories.document_repo import Neo4jDocumentRepo
        repo = Neo4jDocumentRepo(session)
        await repo.update_document_status(user_id, document_id, status)


async def get_graph_for_user(user_id: str) -> dict:
    from services.graph_service import build_graph_response
    async with get_session() as session:
        repo = Neo4jConceptRepo(session)
        graph_data = await repo.get_full_graph(user_id)
        subjects_data = await repo.get_distinct_subjects(user_id)
    return build_graph_response(graph_data["nodes"], graph_data["edges"], subjects_data)


async def vector_search(embedding: list[float], user_id: str) -> list[dict]:
    async with get_session() as session:
        repo = Neo4jConceptRepo(session)
        return await repo.vector_similarity_search(embedding, user_id)


async def vector_search_for_relationships(embedding: list[float], user_id: str) -> list[dict]:
    """Wider search for relationship discovery — lower threshold to catch cross-subject connections."""
    async with get_session() as session:
        repo = Neo4jConceptRepo(session)
        return await repo.vector_similarity_search(embedding, user_id, top_k=20, min_score=0.60)
