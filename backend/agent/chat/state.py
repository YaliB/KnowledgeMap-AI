from typing import TypedDict, List, Optional


class ChatState(TypedDict):
    user_id: str
    message: str
    message_embedding: Optional[list]
    retrieved_concepts: List[dict]
    chat_history: List[dict]
    reply: Optional[str]
    sources: List[dict]
    highlighted_node_ids: List[str]
    error: Optional[str]
    status: str
    messages: list  # working message thread for the tool-call loop
