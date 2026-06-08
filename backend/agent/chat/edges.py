from agent.chat.state import ChatState


def route_after_retrieval(state: ChatState) -> str:
    if state.get("error"):
        return "error"
    return "load_history"


def route_after_generation(state: ChatState) -> str:
    if state.get("error"):
        return "error"
    return "save_messages"
