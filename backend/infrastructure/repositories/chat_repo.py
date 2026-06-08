from datetime import datetime, UTC

from infrastructure.db.collection import chat_history_collection


async def save_message(user_id: str, role: str, content: str,
                       sources: list, highlighted_node_ids: list) -> str:
    doc = {
        "user_id": user_id,
        "role": role,
        "content": content,
        "sources": sources,
        "highlighted_node_ids": highlighted_node_ids,
        "created_at": datetime.now(UTC),
    }
    result = await chat_history_collection().insert_one(doc)
    return str(result.inserted_id)


async def get_recent_messages(user_id: str, limit: int = 10) -> list[dict]:
    cursor = chat_history_collection().find(
        {"user_id": user_id},
        sort=[("created_at", -1)],
    ).limit(limit)
    messages = await cursor.to_list(length=limit)
    messages.reverse()
    return messages
