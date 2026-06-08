from datetime import datetime, timezone

from infrastructure.db.collection import users_collection


async def create_user(user_id: str, name: str, email: str, hashed_password: str) -> None:
    await users_collection().insert_one({
        "_id": user_id,
        "name": name,
        "email": email,
        "hashed_password": hashed_password,
        "created_at": datetime.now(timezone.utc),
        "last_login": None,
    })


async def find_by_email(email: str) -> dict | None:
    return await users_collection().find_one({"email": email})
