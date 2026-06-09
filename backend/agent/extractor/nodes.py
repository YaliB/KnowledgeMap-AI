import logging
from datetime import datetime, UTC
from uuid import uuid4

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage

from core.config import settings
from agent.extractor.state import ExtractorState
from schemas.concept import ConceptList

logger = logging.getLogger(__name__)

_llm = ChatOpenAI(model="gpt-5.4-mini", temperature=0.2, openai_api_key=settings.openai_api_key)
_llm_structured = _llm.with_structured_output(ConceptList)
_embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=settings.openai_api_key)


async def read_pdf_node(state: ExtractorState) -> dict:
    chunks = state["pdf_service"].chunk_text(state["file_path"])
    return {"raw_chunks": chunks}


async def extract_concepts_node(state: ExtractorState) -> dict:
    chunks_text = "\n\n---\n\n".join(state["raw_chunks"])
    prompt = (
        f'You are a knowledge graph builder processing an educational document.\n'
        f'Upload label (context only, do NOT use as the only subject): "{state["subject"]}"\n'
        f'\n'
        f'WHAT TO DO\n'
        f'Extract concepts at EVERY level of the subject hierarchy. Classify each concept into\n'
        f'exactly one of three levels and record its position in the tree:\n'
        f'\n'
        f'EXAMPLE — grade report covering multiple courses:\n'
        f'  Mathematics                         <- level: "subject",  subject: "Mathematics", parent: null\n'
        f'    |-- Calculus                      <- level: "topic",    subject: "Mathematics", parent: "Mathematics"\n'
        f'    |    |-- Derivatives              <- level: "subtopic", subject: "Mathematics", parent: "Calculus"\n'
        f'    |-- Linear Algebra                <- level: "topic",    subject: "Mathematics", parent: "Mathematics"\n'
        f'  Computer Science                    <- level: "subject",  subject: "Computer Science", parent: null\n'
        f'    |-- Algorithms                    <- level: "topic",    subject: "Computer Science", parent: "Computer Science"\n'
        f'    |    |-- Sorting Algorithms       <- level: "subtopic", subject: "Computer Science", parent: "Algorithms"\n'
        f'  Physics                             <- level: "subject",  subject: "Physics", parent: null\n'
        f'    |-- Mechanics                     <- level: "topic",    subject: "Physics", parent: "Physics"\n'
        f'\n'
        f'ANTI-PATTERN — do NOT do this:\n'
        f'  Computer Science                    <- WRONG: lumping Calculus, Physics, Literature all under "CS"\n'
        f'    |-- Calculus                         because the upload was labeled "CS Degree"\n'
        f'    |-- Literature\n'
        f'    |-- Physics\n'
        f'  The upload label is just context. Always look at what the content actually covers.\n'
        f'\n'
        f'LEVEL DEFINITIONS\n'
        f'- "subject"  : the broadest academic domain as it would appear in a university catalog\n'
        f'               (e.g. Mathematics, Physics, History, Computer Science, Economics).\n'
        f'               Extract ONE subject node per DISTINCT academic domain present.\n'
        f'               A document covering 5 different courses should produce 5 (or fewer if some\n'
        f'               courses share the same domain) subject nodes — not one umbrella.\n'
        f'- "topic"    : a major area within a subject (e.g. Algebra, Mechanics, World War II).\n'
        f'- "subtopic" : a specific concept, method, or idea within a topic.\n'
        f'               This is where most depth lives — go as deep as the document goes.\n'
        f'\n'
        f'SUBJECT GRANULARITY RULES\n'
        f'- Too broad  : "Science", "Engineering", "School" — not useful. Split into real domains.\n'
        f'- Too narrow : "Sorting Algorithms", "Derivatives" as subjects — these are topics/subtopics.\n'
        f'- Right level: "Computer Science", "Mathematics", "Biology", "Economics", "History"\n'
        f'- When in doubt, ask: "Would a university list this as a separate department?" If yes → subject.\n'
        f'\n'
        f'FIELD RULES\n'
        f'- subject : ALWAYS the top-level domain (e.g. "Mathematics" for every math concept,\n'
        f'            regardless of nesting depth). Never use a topic or subtopic name here.\n'
        f'- parent  : the IMMEDIATE PARENT concept name (exactly as you named that concept).\n'
        f'            Null only for subject-level concepts.\n'
        f'- No duplicates: extract each idea once.\n'
        f'- Breadth: do NOT skip any domain present in the document.\n'
        f'\n'
        f'PER CONCEPT\n'
        f'- name: title case, max 60 chars\n'
        f'- definition: 1-2 plain-English sentences — what it is and why a student needs to know it\n'
        f'- level: "subject" | "topic" | "subtopic"\n'
        f'- subject: top-level domain (same value for every concept in the same domain)\n'
        f'- parent: immediate parent concept name, or null for subject-level concepts\n'
        f'- importance: 1.0-10.0 (how essential for a student learning this material)\n'
        f'- tags: 2-5 lowercase keywords\n'
        f'\n'
        f'Document text:\n'
        f'{chunks_text}\n'
    )
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
            level=concept.level,
            subject=concept.subject,
            parent=concept.parent,
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
