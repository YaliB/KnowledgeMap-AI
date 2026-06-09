import logging

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

from core.config import settings
from agent.chat.state import ChatState
from agent.chat.tools import GRAPH_TOOLS
from infrastructure.db.neo4j import get_session
from infrastructure.repositories.concept_repo import Neo4jConceptRepo
from infrastructure.repositories.chat_repo import save_message, get_recent_messages

logger = logging.getLogger(__name__)

_llm = ChatOpenAI(
    model="gpt-5.4-mini", temperature=0.3, openai_api_key=settings.openai_api_key
).bind_tools(GRAPH_TOOLS)

_embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small", openai_api_key=settings.openai_api_key
)

_SYSTEM_PROMPT = (
    "You are a study assistant for KnowledgeMap AI. "
    "You are given the user's full knowledge graph (documents, concepts, and relationships). "
    "Use this graph as your primary context when answering questions. "
    "You may also call tools to look up additional concept details when needed. "
    "For each point you make, cite the source document and subject. "
    "Format citations as: [Concept Name] (subject, document_name)."
)


_GRAPH_QUERY = """
MATCH (u:User {user_id: $user_id})
OPTIONAL MATCH (u)-[:OWNS]->(d:Document)
OPTIONAL MATCH (c:Concept {user_id: $user_id})
OPTIONAL MATCH (c)-[r:RELATED_TO]->(c2:Concept {user_id: $user_id})
RETURN collect(DISTINCT d) as documents,
       collect(DISTINCT c) as concepts,
       collect(DISTINCT {from: c.name, to: c2.name, type: r.type, weight: r.weight}) as relationships
"""


async def fetch_graph_context_node(state: ChatState) -> dict:
    async with get_session() as session:
        result = await session.run(_GRAPH_QUERY, user_id=state["user_id"])
        record = await result.single()

    if record is None:
        return {
            "graph_context": {"documents": [], "concepts": [], "relationships": []},
            "highlighted_node_ids": [],
        }

    documents = [dict(d) for d in record["documents"]]
    concepts = [dict(c) for c in record["concepts"]]
    relationships = [
        dict(r) for r in record["relationships"]
        if r.get("from") or r.get("to")
    ]

    return {
        "graph_context": {"documents": documents, "concepts": concepts, "relationships": relationships},
        "highlighted_node_ids": [c.get("id", "") for c in concepts],
    }


async def load_history_node(state: ChatState) -> dict:
    history = await get_recent_messages(
        state["user_id"],
        state["chat_session_id"],
        limit=10,
    )
    return {"chat_history": history}


async def generate_reply_node(state: ChatState) -> dict:
    if not state.get("messages"):
        context_block = _fmt_graph_context(state.get("graph_context") or {})

        messages = [SystemMessage(content=_SYSTEM_PROMPT)]
        for entry in state.get("chat_history", []):
            if entry["role"] == "user":
                messages.append(HumanMessage(content=entry["content"]))
            else:
                messages.append(AIMessage(content=entry["content"]))
        messages.append(HumanMessage(content=f"Context:\n{context_block}\n\nQuestion: {state['message']}"))
    else:
        messages = state["messages"]

    response = await _llm.ainvoke(messages)
    updated = messages + [response]

    if response.tool_calls:
        return {"messages": updated}

    return {"messages": updated, "reply": response.content}


async def call_tools_node(state: ChatState) -> dict:
    messages = state["messages"]
    ai_message = messages[-1]

    new_sources = list(state.get("sources", []))
    new_highlighted = list(state.get("highlighted_node_ids", []))
    tool_messages = []

    for tc in ai_message.tool_calls:
        try:
            result = await _execute_tool(tc["name"], tc["args"], state["user_id"])
            tool_messages.append(
                ToolMessage(content=result["text"], tool_call_id=tc["id"], name=tc["name"])
            )
            new_sources.extend(result.get("sources", []))
            new_highlighted.extend(result.get("highlighted", []))
        except Exception as exc:
            logger.exception("Tool %s failed", tc["name"])
            tool_messages.append(
                ToolMessage(content=f"Tool error: {exc}", tool_call_id=tc["id"], name=tc["name"])
            )

    return {
        "messages": messages + tool_messages,
        "sources": new_sources,
        "highlighted_node_ids": new_highlighted,
    }


async def _execute_tool(name: str, args: dict, user_id: str) -> dict:
    async with get_session() as session:
        repo = Neo4jConceptRepo(session)

        if name == "search_concepts":
            embedding = await _embeddings.aembed_query(args["query"])
            results = await repo.vector_similarity_search(embedding, user_id, top_k=5)
            sources = [
                {
                    "concept_id": r["node"]["id"],
                    "concept_name": r["node"]["name"],
                    "document_name": r["node"].get("document_name", ""),
                    "subject": r["node"].get("subject", ""),
                    "relevance_score": r["score"],
                }
                for r in results
            ]
            return {
                "text": _fmt_concepts([r["node"] for r in results]),
                "sources": sources,
                "highlighted": [r["node"]["id"] for r in results],
            }

        if name == "get_concept_neighbors":
            neighbors = await repo.get_concept_neighbors(args["concept_id"], user_id)
            sources = [
                {
                    "concept_id": n["id"],
                    "concept_name": n["name"],
                    "document_name": n.get("document_name", ""),
                    "subject": n.get("subject", ""),
                    "relevance_score": n.get("weight", 0),
                }
                for n in neighbors
            ]
            return {
                "text": _fmt_neighbors(neighbors),
                "sources": sources,
                "highlighted": [n["id"] for n in neighbors],
            }

        if name == "get_concepts_by_subject":
            all_concepts = await repo.get_concepts_for_user(user_id)
            subject = args["subject"].lower()
            filtered = [c for c in all_concepts if c.get("subject", "").lower() == subject]
            sources = [
                {
                    "concept_id": c["id"],
                    "concept_name": c["name"],
                    "document_name": c.get("source_document", ""),
                    "subject": c.get("subject", ""),
                    "relevance_score": 1.0,
                }
                for c in filtered
            ]
            return {
                "text": _fmt_concepts(filtered),
                "sources": sources,
                "highlighted": [c["id"] for c in filtered],
            }

    return {"text": f"Unknown tool: {name}", "sources": [], "highlighted": []}


def _fmt_graph_context(graph: dict) -> str:
    docs = graph.get("documents", [])
    concepts = graph.get("concepts", [])
    rels = graph.get("relationships", [])

    if not docs and not concepts:
        return "No graph data found for this user."

    lines = []
    if docs:
        lines.append("=== Documents ===")
        for d in docs:
            lines.append(f"- {d.get('name', d.get('title', 'Unknown'))} (id: {d.get('document_id', '')})")

    if concepts:
        lines.append("\n=== Concepts ===")
        for c in concepts:
            lines.append(
                f"- [{c.get('name', '')}] subject: {c.get('subject', '')} | "
                f"source: {c.get('document_name', '')} | def: {c.get('definition', '')}"
            )

    if rels:
        lines.append("\n=== Relationships ===")
        for r in rels:
            if r.get("from") and r.get("to"):
                lines.append(
                    f"- {r['from']} --[{r.get('type', '')}]--> {r['to']} (weight: {r.get('weight', '')})"
                )

    return "\n".join(lines)


def _fmt_concepts(concepts: list[dict]) -> str:
    if not concepts:
        return "No concepts found."
    return "\n\n".join(
        f"ID: {c.get('id', 'N/A')}\nName: {c.get('name', '')}\n"
        f"Subject: {c.get('subject', '')}\nDefinition: {c.get('definition', '')}"
        for c in concepts
    )


def _fmt_neighbors(neighbors: list[dict]) -> str:
    if not neighbors:
        return "No related concepts found."
    return "\n\n".join(
        f"ID: {n.get('id', 'N/A')}\nName: {n.get('name', '')}\n"
        f"Relationship: {n.get('rel_type', '')}\nDefinition: {n.get('definition', '')}"
        for n in neighbors
    )


async def save_messages_node(state: ChatState) -> dict:
    await save_message(
        state["user_id"],
        state["chat_session_id"],
        "user",
        state["message"],
        [],
        [],
    )
    reply = state["reply"]
    assert reply is not None
    await save_message(
        state["user_id"],
        state["chat_session_id"],
        "assistant",
        reply,
        state.get("sources", []),
        state.get("highlighted_node_ids", []),
    )
    return {"status": "done"}


async def error_node(state: ChatState) -> dict:
    logger.error("Chat agent failed for user %s: %s", state.get("user_id"), state.get("error"))
    return {"status": "error"}
