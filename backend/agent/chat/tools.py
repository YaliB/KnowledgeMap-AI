from langchain_core.tools import tool


@tool
def search_concepts(query: str) -> str:
    """Search the knowledge graph for concepts semantically related to a query.
    Returns concept names, definitions, subjects, and IDs.
    Use when you need broader or different context than what was initially retrieved."""
    return ""


@tool
def get_concept_neighbors(concept_id: str) -> str:
    """Get concepts directly related to a given concept ID in the knowledge graph.
    Returns related concept names, definitions, and relationship types.
    Use to explore how a specific concept connects to others."""
    return ""


@tool
def get_concepts_by_subject(subject: str) -> str:
    """Get all concepts in a specific subject area.
    Returns concept names and definitions for that subject.
    Use when the user asks about a subject area broadly."""
    return ""


GRAPH_TOOLS = [search_concepts, get_concept_neighbors, get_concepts_by_subject]
