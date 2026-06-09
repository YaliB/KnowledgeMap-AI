from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel

from apis.dependencies import get_current_user, get_chat_session_id
from agent.chat.graph import build_chat_graph

router = APIRouter()

_chat_graph = build_chat_graph()


class ChatRequest(BaseModel):
    message: str


@router.post("/chat/session/new")
async def create_chat_session(response: Response):
    chat_session_id = "chat_" + uuid4().hex
    response.set_cookie("chat_session_id", chat_session_id, httponly=True, samesite="lax", path="/")
    return {"chat_session_id": chat_session_id}


@router.post("/chat")
async def chat(
    body: ChatRequest,
    response: Response,
    user_id: str = Depends(get_current_user),
    chat_session_id: str | None = Depends(get_chat_session_id),
):
    resolved_chat_session_id = chat_session_id
    if not resolved_chat_session_id:
        resolved_chat_session_id = "chat_" + uuid4().hex
        response.set_cookie(
            "chat_session_id",
            resolved_chat_session_id,
            httponly=True,
            samesite="lax",
            path="/",
        )

    state = {
        "user_id": user_id,
        "chat_session_id": resolved_chat_session_id,
        "message": body.message,
        "message_embedding": None,
        "retrieved_concepts": [],
        "chat_history": [],
        "reply": None,
        "sources": [],
        "highlighted_node_ids": [],
        "error": None,
        "status": "",
        "messages": [],
    }
    try:
        result = await _chat_graph.ainvoke(
            state,
            config={"configurable": {"thread_id": resolved_chat_session_id}},
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Chat processing failed")

    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail="Chat processing failed")

    return {
        "chat_session_id": resolved_chat_session_id,
        "reply": result["reply"],
        "sources": result.get("sources", []),
        "highlighted_node_ids": result.get("highlighted_node_ids", []),
    }
