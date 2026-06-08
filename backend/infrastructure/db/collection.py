from motor.motor_asyncio import AsyncIOMotorCollection

from infrastructure.db.mongo import get_db


def _col(name: str) -> AsyncIOMotorCollection:
    return get_db()[name]


def users_collection() -> AsyncIOMotorCollection:
    return _col("users")


def sessions_collection() -> AsyncIOMotorCollection:
    return _col("sessions")


def chat_history_collection() -> AsyncIOMotorCollection:
    return _col("chat_history")
