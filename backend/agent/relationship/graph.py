from langgraph.graph import StateGraph, END

from agent.relationship.state import RelationshipState
from agent.relationship.nodes import (
    embed_concepts_node, find_all_pairs_node,
    classify_all_pairs_node, save_relationships_node, error_node,
)
from agent.relationship.edges import route_on_error


def build_relationship_graph():
    graph = StateGraph(RelationshipState)

    graph.add_node("embed_concepts", embed_concepts_node)
    graph.add_node("find_all_pairs", find_all_pairs_node)
    graph.add_node("classify_all_pairs", classify_all_pairs_node)
    graph.add_node("save_relationships", save_relationships_node)
    graph.add_node("error", error_node)

    graph.set_entry_point("embed_concepts")
    graph.add_conditional_edges("embed_concepts", route_on_error)
    graph.add_edge("find_all_pairs", "classify_all_pairs")
    graph.add_edge("classify_all_pairs", "save_relationships")
    graph.add_edge("save_relationships", END)
    graph.add_edge("error", END)

    return graph.compile()
