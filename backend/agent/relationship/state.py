from typing import TypedDict, List, Optional


class RelationshipState(TypedDict):
    document_id: str
    user_id: str
    concepts: List[dict]        # concept dicts with id + embedding already set
    relationships: List[dict]   # built up by nodes
    candidate_pairs: List[dict] # similar concepts found for current_index concept
    current_index: int          # which concept we're processing
    error: Optional[str]
    status: str                 # processing | done | error
