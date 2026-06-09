from langgraph.graph import StateGraph, END

from agent.chat.state import ChatState
from agent.chat.nodes import (
    embed_query_node, retrieve_context_node, load_history_node,
    generate_reply_node, call_tools_node, save_messages_node, error_node,
)
from agent.chat.edges import route_after_retrieval, route_after_generation


def build_chat_graph():
    graph = StateGraph(ChatState)  # type: ignore

    graph.add_node("embed_query", embed_query_node)  # type: ignore
    graph.add_node("retrieve_context", retrieve_context_node)  # type: ignore
    graph.add_node("load_history", load_history_node)  # type: ignore
    graph.add_node("generate_reply", generate_reply_node)  # type: ignore
    graph.add_node("call_tools", call_tools_node)  # type: ignore
    graph.add_node("save_messages", save_messages_node)  # type: ignore
    graph.add_node("error", error_node)  # type: ignore

    graph.set_entry_point("embed_query")
    graph.add_edge("embed_query", "retrieve_context")
    graph.add_conditional_edges("retrieve_context", route_after_retrieval)
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
