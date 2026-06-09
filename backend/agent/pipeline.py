import logging
from pathlib import Path

from agent.extractor.nodes import read_pdf_node, extract_concepts_node
from agent.relationship.graph import build_relationship_graph
from services.db_service import save_concepts_from_extractor_agent, set_document_status
from services.pdf_service import PyPDFService

logger = logging.getLogger(__name__)

_relationship_graph = build_relationship_graph()
_pdf_service = PyPDFService()


async def run_extraction_pipeline(document_id: str, user_id: str, file_path: str, subject: str) -> None:
    async def status(s: str) -> None:
        await set_document_status(user_id, document_id, s)

    try:
        await status("reading_pdf")
        state: dict = {
            "document_id": document_id,
            "user_id": user_id,
            "subject": subject,
            "filename": Path(file_path).name,
            "file_path": file_path,
            "raw_chunks": [],
            "concepts": [],
            "error": None,
            "concept_repo": None,
            "document_repo": None,
            "pdf_service": _pdf_service,
        }
        state = {**state, **await read_pdf_node(state)}

        await status("extracting_concepts")
        state = {**state, **await extract_concepts_node(state)}

        if state.get("error"):
            raise RuntimeError(state["error"])

        await status("saving_concepts")
        raw_concepts = [c.model_dump() for c in state["concepts"]]
        saved_concepts = await save_concepts_from_extractor_agent(document_id, user_id, raw_concepts)

        if saved_concepts:
            await _relationship_graph.ainvoke({
                "document_id": document_id,
                "user_id": user_id,
                "concepts": saved_concepts,
                "relationships": [],
                "candidate_pairs": [],
                "error": None,
                "status": "processing",
            })

        await status("done")

    except Exception:
        logger.exception("Extraction pipeline failed for document %s", document_id)
        await set_document_status(user_id, document_id, "error")
        raise
