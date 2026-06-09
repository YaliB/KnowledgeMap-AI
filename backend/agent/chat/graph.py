from langgraph.graph import StateGraph, END

from agent.chat.state import ChatState
from agent.chat.nodes import (
    fetch_graph_context_node, load_history_node,
    generate_reply_node, call_tools_node, save_messages_node, error_node,
)
from agent.chat.edges import route_after_graph_fetch, route_after_generation


def build_chat_graph():
    graph = StateGraph(ChatState)  # type: ignore

    graph.add_node("fetch_graph_context", fetch_graph_context_node)  # type: ignore
    graph.add_node("load_history", load_history_node)  # type: ignore
    graph.add_node("generate_reply", generate_reply_node)  # type: ignore
    graph.add_node("call_tools", call_tools_node)  # type: ignore
    graph.add_node("save_messages", save_messages_node)  # type: ignore
    graph.add_node("error", error_node)  # type: ignore

    graph.set_entry_point("fetch_graph_context")
    graph.add_conditional_edges("fetch_graph_context", route_after_graph_fetch)
    graph.add_edge("load_history", "generate_reply")
    graph.add_conditional_edges(
        "generate_reply",
        route_after_generation,
        {"call_tools": "call_tools", "save_messages": "save_messages", "error": "error"},
    )
    graph.add_edge("call_tools", "generate_reply")
    graph.add_edge("save_messages", END)
    graph.add_edge("error", END)

    return graph.compile()
