from agent.relationship.state import RelationshipState


def route_on_error(state: RelationshipState) -> str:
    if state.get("error"):
        return "error"
    return "find_all_pairs"
