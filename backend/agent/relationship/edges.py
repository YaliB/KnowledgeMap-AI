from agent.relationship.state import RelationshipState


def should_continue_or_finish(state: RelationshipState) -> str:
    if state["current_index"] < len(state["concepts"]):
        return "find_similar"
    return "save_relationships"


def route_on_error(state: RelationshipState) -> str:
    if state.get("error"):
        return "error"
    return "embed_concepts"
