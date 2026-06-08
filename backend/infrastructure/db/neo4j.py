import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from neo4j import AsyncGraphDatabase, AsyncDriver
from core.config import settings
from typing import cast, LiteralString

_driver: AsyncDriver | None = None
_lock = asyncio.Lock()


async def get_driver() -> AsyncDriver:
    global _driver
    async with _lock:
        if _driver is None:
            _driver = AsyncGraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_username, settings.neo4j_password),
            )
    return _driver #type: ignore


async def connect():
    driver = await get_driver()
    await driver.verify_connectivity()


async def close():
    global _driver
    async with _lock:
        if _driver is not None:
            await _driver.close()
            _driver = None


@asynccontextmanager
async def get_session():
    driver = await get_driver()
    async with driver.session(database=settings.neo4j_dbname) as session:
        yield session


async def run_constraints():
    cypher_file = Path(__file__).parent / "constraints.cypher"
    statements = [
        s.strip()
        for s in cypher_file.read_text().split(";")
        if s.strip()
    ]
    async with get_session() as session:
        for stmt in statements:
            await session.run(cast(LiteralString, stmt))