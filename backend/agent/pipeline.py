import logging

from agent.extractor.nodes import read_pdf_node, extract_concepts_node
from agent.relationship.graph import build_relationship_graph
from infrastructure.db.neo4j import get_session
from infrastructure.repositories.document_repo import Neo4jDocumentRepo
from services.db_service import save_concepts_from_extractor_agent
from services.pdf_service import PyPDFService

logger = logging.getLogger(__name__)

_relationship_graph = build_relationship_graph()
_pdf_service = PyPDFService()


async def run_extraction_pipeline(document_id: str, user_id: str, file_path: str, subject: str) -> None:
    async with get_session() as session:
        doc_repo = Neo4jDocumentRepo(session)
        await doc_repo.update_document_status(user_id, document_id, "processing")

    try:
        # Call extractor nodes directly to skip the graph's built-in save step,
        # so we can capture IDs and embeddings from db_service for the relationship agent.
        state: dict = {
            "document_id": document_id,
            "user_id": user_id,
            "subject": subject,
            "filename": file_path.split("/")[-1],
            "file_path": file_path,
            "raw_chunks": [],
            "concepts": [],
            "error": None,
            "concept_repo": None,
            "document_repo": None,
            "pdf_service": _pdf_service,
        }
        state = {**state, **await read_pdf_node(state)}
        state = {**state, **await extract_concepts_node(state)}

        if state.get("error"):
            raise RuntimeError(state["error"])

        raw_concepts = [{**c.model_dump(), "subject": subject} for c in state["concepts"]]
        saved_concepts = await save_concepts_from_extractor_agent(document_id, user_id, raw_concepts)

        if saved_concepts:
            await _relationship_graph.ainvoke({
                "document_id": document_id,
                "user_id": user_id,
                "concepts": saved_concepts,
                "relationships": [],
                "candidate_pairs": [],
                "current_index": 0,
                "error": None,
                "status": "processing",
            })

        async with get_session() as session:
            doc_repo = Neo4jDocumentRepo(session)
            await doc_repo.update_document_status(user_id, document_id, "done")

    except Exception:
        logger.exception("Extraction pipeline failed for document %s", document_id)
        async with get_session() as session:
            doc_repo = Neo4jDocumentRepo(session)
            await doc_repo.update_document_status(user_id, document_id, "error")
        raise
