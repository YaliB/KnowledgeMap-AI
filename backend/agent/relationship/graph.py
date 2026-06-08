from langgraph.graph import StateGraph, END

from agent.relationship.state import RelationshipState
from agent.relationship.nodes import (
    embed_concepts_node, find_similar_node,
    classify_relationships_node, save_relationships_node, error_node,
)
from agent.relationship.edges import should_continue_or_finish


def build_relationship_graph():
    graph = StateGraph(RelationshipState)

    graph.add_node("embed_concepts", embed_concepts_node)
    graph.add_node("find_similar", find_similar_node)
    graph.add_node("classify_relationships", classify_relationships_node)
    graph.add_node("save_relationships", save_relationships_node)
    graph.add_node("error", error_node)

    graph.set_entry_point("embed_concepts")
    graph.add_edge("embed_concepts", "find_similar")
    graph.add_edge("find_similar", "classify_relationships")
    graph.add_conditional_edges("classify_relationships", should_continue_or_finish)
    graph.add_edge("save_relationships", END)
    graph.add_edge("error", END)

    return graph.compile()
