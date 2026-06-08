import logging

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage

from core.config import settings
from agent.chat.state import ChatState
from services.db_service import vector_search
from infrastructure.repositories.chat_repo import save_message, get_recent_messages

logger = logging.getLogger(__name__)

_llm = ChatOpenAI(model="gpt-4o", temperature=0.3, openai_api_key=settings.openai_api_key)
_embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=settings.openai_api_key)

_SYSTEM_PROMPT = (
    "You are a study assistant for KnowledgeMap AI. Answer using ONLY the provided concept context. "
    "For each point you make, cite the source document and subject. "
    "Always format: [Concept Name] (subject, document_name)."
)


async def embed_query_node(state: ChatState) -> dict:
    embedding = await _embeddings.aembed_query(state["message"])
    return {"message_embedding": embedding}


async def retrieve_context_node(state: ChatState) -> dict:
    embedding = state["message_embedding"]
    assert embedding is not None
    results = await vector_search(embedding, state["user_id"])
    top5 = results[:5]

    sources = [
        {
            "concept_id": r["node"]["id"],
            "concept_name": r["node"]["name"],
            "document_name": r["node"].get("document_name", ""),
            "subject": r["node"].get("subject", ""),
            "relevance_score": r["score"],
        }
        for r in top5
    ]
    retrieved_concepts = [r["node"] for r in top5]
    highlighted_node_ids = [s["concept_id"] for s in sources]

    return {
        "retrieved_concepts": retrieved_concepts,
        "sources": sources,
        "highlighted_node_ids": highlighted_node_ids,
    }


async def load_history_node(state: ChatState) -> dict:
    history = await get_recent_messages(state["user_id"], limit=10)
    return {"chat_history": history}


async def generate_reply_node(state: ChatState) -> dict:
    context_lines = []
    for concept in state.get("retrieved_concepts", []):
        context_lines.append(
            f"Name: {concept.get('name', '')}\n"
            f"Subject: {concept.get('subject', '')}\n"
            f"Source: {concept.get('document_name', '')}\n"
            f"Definition: {concept.get('definition', '')}"
        )
    context_block = "\n\n".join(context_lines)

    messages: list[BaseMessage] = [SystemMessage(content=_SYSTEM_PROMPT)]
    for entry in state.get("chat_history", []):
        if entry["role"] == "user":
            messages.append(HumanMessage(content=entry["content"]))
        else:
            messages.append(AIMessage(content=entry["content"]))

    user_content = f"Context:\n{context_block}\n\nQuestion: {state['message']}"
    messages.append(HumanMessage(content=user_content))

    response = await _llm.ainvoke(messages)
    return {"reply": response.content}


async def save_messages_node(state: ChatState) -> dict:
    await save_message(state["user_id"], "user", state["message"], [], [])
    reply = state["reply"]
    assert reply is not None
    await save_message(
        state["user_id"],
        "assistant",
        reply,
        state.get("sources", []),
        state.get("highlighted_node_ids", []),
    )
    return {"status": "done"}


async def error_node(state: ChatState) -> dict:
    logger.error("Chat agent failed for user %s: %s", state.get("user_id"), state.get("error"))
    return {"status": "error"}
