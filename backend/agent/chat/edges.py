from agent.chat.state import ChatState


def route_after_graph_fetch(state: ChatState) -> str:
    if state.get("error"):
        return "error"
    return "load_history"


def route_after_generation(state: ChatState) -> str:
    if state.get("error"):
        return "error"
    messages = state.get("messages", [])
    if messages:
        last = messages[-1]
        has_tool_calls = getattr(last, "tool_calls", None)
        tool_rounds = sum(1 for m in messages if getattr(m, "tool_calls", None))
        if has_tool_calls and tool_rounds <= 3:
            return "call_tools"
    return "save_messages"
