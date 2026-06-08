from typing import Optional
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorCollection

from .abstractions.session_repo import AbstractSessionRepo


class MongoSessionRepo(AbstractSessionRepo):
    def __init__(self, col: AsyncIOMotorCollection):
        self.col = col

    async def create_session(self, session_id: str, user_id: str, expires_at: datetime) -> None:
        await self.col.insert_one({
            "_id": session_id,
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
        })

    async def find_session(self, session_id: str) -> Optional[dict]:
        return await self.col.find_one({"_id": session_id})

    async def delete_session(self, session_id: str) -> None:
        await self.col.delete_one({"_id": session_id})
