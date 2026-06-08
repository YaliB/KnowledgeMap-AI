import json
import logging

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage

from core.config import settings
from agent.relationship.state import RelationshipState
from services.db_service import save_relationships_from_relationship_agent, vector_search

logger = logging.getLogger(__name__)

_llm = ChatOpenAI(model="gpt-4o", temperature=0.2, openai_api_key=settings.openai_api_key)
_embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=settings.openai_api_key)


async def embed_concepts_node(state: RelationshipState) -> dict:
    updated = []
    for concept in state["concepts"]:
        if concept.get("embedding"):
            updated.append(concept)
            continue
        embedding = await _embeddings.aembed_query(concept["name"] + " " + concept["definition"])
        updated.append({**concept, "embedding": embedding})
    return {"concepts": updated, "current_index": 0}


async def find_similar_node(state: RelationshipState) -> dict:
    concept = state["concepts"][state["current_index"]]
    candidates = await vector_search(concept["embedding"], state["user_id"])
    filtered = [c for c in candidates if c["node"]["id"] != concept["id"]]
    return {"candidate_pairs": filtered}


async def classify_relationships_node(state: RelationshipState) -> dict:
    concept = state["concepts"][state["current_index"]]
    relationships = list(state.get("relationships", []))

    for candidate in state.get("candidate_pairs", []):
        neighbor = candidate["node"]
        score = candidate["score"]
        prompt = (
            f"Concept A: {concept['name']} — {concept['definition']}\n"
            f"Concept B: {neighbor['name']} — {neighbor['definition']}\n"
            f"Cosine similarity: {score}\n\n"
            "Classify their relationship as ONE of:\n"
            "related | prerequisite | contrasts | same-idea\n\n"
            "Also write a 1-sentence plain English explanation.\n\n"
            'Respond as JSON: {"rel_type": string, "explanation": string}'
        )
        try:
            response = await _llm.ainvoke([HumanMessage(content=prompt)])
            classification = json.loads(response.content)
        except Exception:
            logger.exception("classify failed for pair %s → %s", concept["id"], neighbor["id"])
            continue

        relationships.append({
            "concept_a_id": concept["id"],
            "concept_b_id": neighbor["id"],
            "weight": score,
            "rel_type": classification["rel_type"],
            "cross_subject": concept.get("subject") != neighbor.get("subject"),
            "subject_a": concept.get("subject"),
            "subject_b": neighbor.get("subject"),
            "explanation": classification["explanation"],
        })

    return {"relationships": relationships, "current_index": state["current_index"] + 1}


async def save_relationships_node(state: RelationshipState) -> dict:
    await save_relationships_from_relationship_agent(state["relationships"])
    return {"status": "done"}


async def error_node(state: RelationshipState) -> dict:
    logger.error("Relationship agent failed for document %s: %s",
                 state.get("document_id"), state.get("error"))
    return {"status": "error"}
