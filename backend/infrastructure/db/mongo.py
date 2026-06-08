from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from core.config import settings

_client: AsyncIOMotorClient | None = None

def init_client(uri: str) -> None:
    global _client
    if _client is not None:
        return 
    _client = AsyncIOMotorClient(uri)

def get_client() -> AsyncIOMotorClient:
    if _client is None:
        raise RuntimeError("MongoDB client not initialized. Call init_client() first.")
    return _client

def get_db() -> AsyncIOMotorDatabase:
    return get_client()[settings.mongodb_db]

def close() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None