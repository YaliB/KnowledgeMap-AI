from langgraph.graph import StateGraph

from agent.extractor.state import ExtractorState
from agent.extractor.nodes import read_pdf_node, extract_concepts_node, save_concepts_node, error_node
from agent.extractor.edges import route_after_extract


def build_extractor_graph():
    graph = StateGraph(ExtractorState)
    graph.add_node("read_pdf_node", read_pdf_node)
    graph.add_node("extract_concepts_node", extract_concepts_node)
    graph.add_node("save_concepts_node", save_concepts_node)
    graph.add_node("error_node", error_node)

    graph.set_entry_point("read_pdf_node")
    graph.add_edge("read_pdf_node", "extract_concepts_node")
    graph.add_conditional_edges("extract_concepts_node", route_after_extract)
    graph.add_edge("save_concepts_node", "__end__")
    graph.add_edge("error_node", "__end__")

    return graph.compile()


extractor_graph = build_extractor_graph()
