import asyncio
import logging
from typing import Literal

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from core.config import settings
from agent.relationship.state import RelationshipState
from services.db_service import save_relationships_from_relationship_agent, vector_search_for_relationships, set_document_status

logger = logging.getLogger(__name__)

_llm = ChatOpenAI(model="gpt-5.4-mini", temperature=0.2, openai_api_key=settings.openai_api_key)
_embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=settings.openai_api_key)

_CLASSIFY_CONCURRENCY = 10


class RelationshipClassification(BaseModel):
    weight: float = Field(..., ge=0.0, le=1.0)
    rel_type: Literal["related", "prerequisite", "contrasts", "same-idea"]
    explanation: str


_llm_classifier = _llm.with_structured_output(RelationshipClassification)


async def embed_concepts_node(state: RelationshipState) -> dict:
    async def embed_one(concept: dict) -> dict:
        if concept.get("embedding"):
            return concept
        embedding = await _embeddings.aembed_query(concept["name"] + " " + concept["definition"])
        return {**concept, "embedding": embedding}

    concepts = await asyncio.gather(*[embed_one(c) for c in state["concepts"]])
    return {"concepts": list(concepts)}


async def find_all_pairs_node(state: RelationshipState) -> dict:
    await set_document_status(state["user_id"], state["document_id"], "finding_relationships")
    concepts = state["concepts"]

    # Fan out: search for similar concepts for all concepts in parallel
    search_results = await asyncio.gather(*[
        vector_search_for_relationships(c["embedding"], state["user_id"])
        for c in concepts
    ])

    # Deduplicate: use a sorted (id_a, id_b) tuple so A->B and B->A collapse to one pair
    seen: set[tuple] = set()
    unique_pairs: list[dict] = []

    for concept, candidates in zip(concepts, search_results):
        for cand in candidates:
            neighbor = cand["node"]
            if neighbor["id"] == concept["id"]:
                continue
            pair_key = tuple(sorted([concept["id"], neighbor["id"]]))
            if pair_key in seen:
                continue
            seen.add(pair_key)
            unique_pairs.append({
                "concept_a": concept,
                "concept_b": neighbor,
                "score": cand["score"],
            })

    logger.info("Relationship builder: %d unique pairs from %d concepts", len(unique_pairs), len(concepts))
    return {"candidate_pairs": unique_pairs}


async def classify_all_pairs_node(state: RelationshipState) -> dict:
    await set_document_status(state["user_id"], state["document_id"], "classifying_relationships")
    pairs = state["candidate_pairs"]
    semaphore = asyncio.Semaphore(_CLASSIFY_CONCURRENCY)

    async def classify_one(pair: dict) -> dict | None:
        concept = pair["concept_a"]
        neighbor = pair["concept_b"]
        score = pair["score"]
        cross = concept.get("subject") != neighbor.get("subject")

        subject_line = (
            f"DIFFERENT ({concept.get('subject')} vs {neighbor.get('subject')})"
            if cross else
            f"same ({concept.get('subject')})"
        )
        prompt = (
            f"Concept A: {concept['name']} | subject: {concept.get('subject', 'unknown')} | level: {concept.get('level', 'unknown')}\n"
            f"Definition A: {concept['definition']}\n\n"
            f"Concept B: {neighbor['name']} | subject: {neighbor.get('subject', 'unknown')} | level: {neighbor.get('level', 'unknown')}\n"
            f"Definition B: {neighbor['definition']}\n\n"
            f"Subjects: {subject_line}\n"
            f"Embedding similarity: {score:.2f}\n\n"
            "──────────────────────────────────────────\n"
            "RELATIONSHIP QUALITY GUIDELINES\n"
            "──────────────────────────────────────────\n"
            "Quality over quantity. Every relationship you create appears as an edge on a visual\n"
            "graph a student will study from. Bad edges pollute the graph.\n\n"
            "THE CORE QUESTION: Before creating any relationship, ask:\n"
            "'If a student is studying A and sees B connected to it, will they say\n"
            " YES, that makes sense — or WHY is that there?'\n"
            "If the answer is 'why is that there' — do NOT create the relationship.\n\n"
            "STRONG SIGNALS — CREATE THESE:\n"
            "  • One concept is used to define or explain the other\n"
            "      GOOD: 'Eigenvalues' → 'PCA'  (PCA is defined using eigenvalue decomposition)\n"
            "  • One is a specific instance or type of the other\n"
            "      GOOD: 'SVD' → 'Matrix Decomposition'  (SVD is a specific matrix decomposition)\n"
            "  • Without A you cannot solve or understand B\n"
            "      GOOD: 'Derivatives' → 'Gradient Descent'  (GD computes derivatives at every step)\n"
            "  • They appear together in the same theorem, proof, or formula\n"
            "      GOOD: 'Chain Rule' → 'Backpropagation'  (backprop IS chain rule applied to networks)\n"
            "  • A was historically developed to solve a problem posed by B (or vice versa)\n"
            "      GOOD: 'Germ Theory' → 'Antibiotics'\n"
            "  • They are commonly contrasted in academic literature\n"
            "      GOOD: 'Supervised Learning' contrasts 'Unsupervised Learning'\n\n"
            "WEAK SIGNALS — AVOID THESE:\n"
            "  ✗ They are in the same general field  →  BAD: 'Photosynthesis' → 'Cell Division'\n"
            "  ✗ They share a keyword in their definition  →  BAD: 'DNA Replication' → 'RNA Transcription' just because both mention nucleotides\n"
            "  ✗ They were mentioned on the same page/chapter  →  BAD: 'WW1' → 'French Revolution'\n"
            "  ✗ The connection requires multiple inferential steps  →  BAD: 'Inflation' → 'Newton\\'s Laws'\n"
            "  ✗ The relationship is obvious category membership  →  BAD: 'Addition' → 'Mathematics'\n\n"
            "REL_TYPE ASSIGNMENT — BE STRICT:\n\n"
            "  prerequisite:\n"
            "    Test: 'Can a student understand B without knowing A?'\n"
            "    If NO → prerequisite. If YES → it is NOT a prerequisite.\n"
            "    CORRECT: 'Derivatives' prerequisite 'Gradient Descent'\n"
            "    WRONG:   'Statistics' prerequisite 'Economics'  ← a student can study economics\n"
            "              without statistics, they just do it worse\n\n"
            "  same-idea:\n"
            "    Test: 'Would a textbook say \"X is also known as Y\" or \"X is essentially Y\"?'\n"
            "    CORRECT: 'Natural Selection' same-idea 'Survival of the Fittest'\n"
            "    CORRECT: 'Entropy' same-idea 'Information Entropy'\n"
            "    WRONG:   'Supervised Learning' same-idea 'Neural Networks'  ← NN is one type of SL\n\n"
            "  related:\n"
            "    A and B clearly belong together but neither is a prerequisite and they are not\n"
            "    the same thing. When in doubt between related and prerequisite, run the\n"
            "    prerequisite test. Default to related only if the test is ambiguous.\n"
            "    CORRECT: 'Inflation' related 'Unemployment'\n"
            "    CORRECT: 'DNA' related 'Protein Synthesis'\n\n"
            "  contrasts:\n"
            "    Test: 'Are these defined in opposition, where understanding one requires knowing\n"
            "           the other exists?'\n"
            "    CORRECT: 'Keynesian Economics' contrasts 'Monetarism'\n"
            "    CORRECT: 'Mitosis' contrasts 'Meiosis'\n"
            "    WRONG:   'Photosynthesis' contrasts 'Respiration'  ← opposite reactions but not\n"
            "              defined in opposition academically\n\n"
            + (
            "CROSS-SUBJECT RULES (stricter standard — these are different subjects):\n"
            "  REQUIRE at least one of:\n"
            "    A) A is used as a tool/method inside B's domain\n"
            "       Example: 'Linear Algebra' → 'Machine Learning'\n"
            "    B) A was the historical/scientific prerequisite for B\n"
            "       Example: 'Germ Theory' (Medicine) → 'Vaccines' (Biology)\n"
            "    C) A and B are formally equivalent or isomorphic\n"
            "       Example: 'Entropy' (Physics) same-idea 'Information Entropy' (CS)\n"
            "    D) B directly applies A to a new domain\n"
            "       Example: 'Probability' (Math) applied as 'Risk' (Economics)\n"
            "  REJECT if: connection requires more than one inferential step, relationship is\n"
            "  cultural/thematic rather than structural, or concepts are at totally different\n"
            "  abstraction levels.\n\n"
            if cross else ""
            ) +
            "WEIGHT CALIBRATION:\n"
            "  0.95+      Used in the formal definition of each other\n"
            "             'Eigenvalues' → 'Characteristic Polynomial' | 'Derivative' → 'Gradient'\n"
            "  0.85-0.94  Core dependency, appears in every explanation of B\n"
            "             'Chain Rule' → 'Backpropagation' | 'Supply & Demand' → 'Market Equilibrium'\n"
            "  0.75-0.84  Important connection, regularly co-studied\n"
            "             'Probability' → 'Bayesian Inference' | 'Newton\\'s Laws' → 'Biomechanics'\n"
            "  0.60-0.74  Real but loose connection, tangential co-occurrence\n"
            "             'Inflation' → 'Game Theory'\n"
            "  below 0.60 Do NOT create. Too weak to add value.\n\n"
            "CALIBRATION CHECK: If you assign weight > 0.85, be sure a professor would agree\n"
            "with that strength. Most relationships should fall in 0.60-0.84.\n\n"
            "EXPLANATION RULES (shown to students on the graph):\n"
            "  - Exactly 1 sentence, specific, written for a student\n"
            "  - Mention WHAT A does to B or HOW they connect mechanically\n"
            "  - Never vague filler like 'these two concepts are related in the field of X'\n"
            "  BAD:  'PCA and eigenvalues are both important in linear algebra'\n"
            "  GOOD: 'PCA identifies principal components by computing the eigenvectors of the data\\'s covariance matrix'\n"
            "  BAD:  'Inflation and interest rates are related economic concepts'\n"
            "  GOOD: 'Central banks raise interest rates to cool inflation by making borrowing more expensive'\n\n"
            "FINAL SELF-CHECK before responding:\n"
            "  1. Does this weight honestly reflect strength? Would a professor agree?\n"
            "  2. Does the rel_type pass the strict test above?\n"
            "  3. Is the explanation specific and exactly one sentence?\n"
            "  4. If cross-subject, does it pass the stricter standard?\n"
            "  If any check fails → set weight < 0.60 (will be discarded).\n\n"
            'Respond as JSON: {"weight": float, "rel_type": string, "explanation": string}'
        )
        try:
            async with semaphore:
                classification = await _llm_classifier.ainvoke(
                    [HumanMessage(content=prompt)]
                )
        except Exception:
            logger.exception("classify failed for pair %s -> %s", concept["id"], neighbor["id"])
            return None

        if classification.weight < 0.60:
            return None

        return {
            "concept_a_id": concept["id"],
            "concept_b_id": neighbor["id"],
            "weight": classification.weight,
            "rel_type": classification.rel_type,
            "cross_subject": cross,
            "subject_a": concept.get("subject"),
            "subject_b": neighbor.get("subject"),
            "explanation": classification.explanation,
        }

    results = await asyncio.gather(*[classify_one(p) for p in pairs])
    relationships = [r for r in results if r is not None]
    logger.info("Relationship builder: %d relationships from %d pairs", len(relationships), len(pairs))
    return {"relationships": relationships}


async def save_relationships_node(state: RelationshipState) -> dict:
    await save_relationships_from_relationship_agent(state["relationships"])
    return {"status": "done"}


async def error_node(state: RelationshipState) -> dict:
    logger.error("Relationship agent failed for document %s: %s",
                 state.get("document_id"), state.get("error"))
    return {"status": "error"}
