from typing import TypedDict, List, Optional


class ChatState(TypedDict):
    user_id: str
    chat_session_id: str
    message: str
    graph_context: Optional[dict]
    chat_history: List[dict]
    reply: Optional[str]
    sources: List[dict]
    highlighted_node_ids: List[str]
    error: Optional[str]
    status: str
    messages: list  # working message thread for the tool-call loop
