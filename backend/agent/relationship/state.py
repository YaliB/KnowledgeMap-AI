from typing import TypedDict, List, Optional


class RelationshipState(TypedDict):
    document_id: str
    user_id: str
    concepts: List[dict]        # concept dicts with id + embedding already set
    relationships: List[dict]   # built up by classify_all_pairs_node
    candidate_pairs: List[dict] # {concept_a, concept_b, score} — deduped unique pairs
    error: Optional[str]
    status: str
