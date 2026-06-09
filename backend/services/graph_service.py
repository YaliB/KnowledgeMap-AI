def build_graph_response(raw_nodes: list[dict], raw_edges: list[dict],
                         subjects_data: list[dict]) -> dict:
    edges = [e for e in raw_edges if e.get("target") is not None]

    seen: set[str] = set()
    subjects: list[str] = []
    for entry in subjects_data:
        normalized = (entry.get("subject") or "").strip().title()
        if normalized and normalized not in seen:
            seen.add(normalized)
            subjects.append(normalized)

    # Normalize node subjects to match the subjects list (fixes invisible zones bug)
    nodes = []
    for n in raw_nodes:
        node = dict(n)
        if node.get("subject"):
            node["subject"] = node["subject"].strip().title()
        nodes.append(node)

    cross_subject_edges = sum(1 for e in edges if e.get("cross_subject"))

    return {
        "nodes": nodes,
        "edges": edges,
        "subjects": subjects,
        "stats": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "cross_subject_edges": cross_subject_edges,
        },
    }
