import logging
from datetime import datetime, UTC
from uuid import uuid4

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage

from core.config import settings
from agent.extractor.state import ExtractorState
from schemas.concept import ConceptList

logger = logging.getLogger(__name__)

_llm = ChatOpenAI(model="gpt-4o", temperature=0.2, openai_api_key=settings.openai_api_key)
_llm_structured = _llm.with_structured_output(ConceptList)
_embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=settings.openai_api_key)


async def read_pdf_node(state: ExtractorState) -> dict:
    chunks = state["pdf_service"].chunk_text(state["file_path"])
    return {"raw_chunks": chunks}


async def extract_concepts_node(state: ExtractorState) -> dict:
    prompt = f"""You are an expert knowledge extractor. Given the following text chunks from a document about {state['subject']}, extract the key concepts a student needs to understand.

For each concept provide: name (title case, max 60 chars), definition (1-2 plain English sentences), importance (float 1.0-10.0), tags (2-5 lowercase keywords).

Text chunks:
{state['raw_chunks']}
"""
    try:
        result: ConceptList = await _llm_structured.ainvoke([HumanMessage(content=prompt)])
        return {"concepts": result.concepts}
    except Exception as e:
        logger.exception("extract_concepts_node failed")
        return {"error": str(e), "concepts": []}


async def save_concepts_node(state: ExtractorState) -> dict:
    for concept in state["concepts"]:
        embedding = await _embeddings.aembed_query(concept.name + " " + concept.definition)
        await state["concept_repo"].create_concept(
            id=str(uuid4()),
            user_id=state["user_id"],
            document_id=state["document_id"],
            name=concept.name,
            definition=concept.definition,
            subject=state["subject"],
            importance=concept.importance,
            tags=concept.tags,
            embedding=embedding,
            created_at=datetime.now(UTC).isoformat(),
        )
    await state["document_repo"].update_document_status(
        state["user_id"], state["document_id"], "done"
    )
    return {}


async def error_node(state: ExtractorState) -> dict:
    logger.error("Extractor failed for document %s: %s", state["document_id"], state.get("error"))
    await state["document_repo"].update_document_status(
        state["user_id"], state["document_id"], "error"
    )
    return {}
