from typing import Optional
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorCollection

from .abstractions.user_repo import AbstractUserRepo


class MongoUserRepo(AbstractUserRepo):
    def __init__(self, col: AsyncIOMotorCollection):
        self.col = col

    async def create_user(self, user_id: str, name: str, email: str, hashed_password: str) -> dict:
        doc = {
            "_id": user_id,
            "name": name,
            "email": email,
            "hashed_password": hashed_password,
            "created_at": datetime.utcnow().isoformat(),
        }
        await self.col.insert_one(doc)
        return doc

    async def find_by_email(self, email: str) -> Optional[dict]:
        return await self.col.find_one({"email": email})
