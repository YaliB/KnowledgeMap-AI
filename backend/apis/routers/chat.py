from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from apis.dependencies import get_current_user
from agent.chat.graph import build_chat_graph

router = APIRouter()

_chat_graph = build_chat_graph()


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
async def chat(
    body: ChatRequest,
    user_id: str = Depends(get_current_user),
):
    state = {
        "user_id": user_id,
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
        result = await _chat_graph.ainvoke(state)
    except Exception:
        raise HTTPException(status_code=500, detail="Chat processing failed")

    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail="Chat processing failed")

    return {
        "reply": result["reply"],
        "sources": result.get("sources", []),
        "highlighted_node_ids": result.get("highlighted_node_ids", []),
    }
