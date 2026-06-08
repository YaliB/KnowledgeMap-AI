from agent.extractor.state import ExtractorState


def route_after_extract(state: ExtractorState) -> str:
    if state.get("error"):
        return "error_node"
    if not state.get("concepts"):
        return "error_node"
    return "save_concepts_node"
