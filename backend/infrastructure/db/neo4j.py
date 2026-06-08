from contextlib import asynccontextmanager
from pathlib import Path

from neo4j import AsyncGraphDatabase

from core.config import settings

_driver = None


def get_driver():
    global _driver
    if _driver is None:
        _driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_username, settings.neo4j_password),
        )
    return _driver


async def connect():
    driver = get_driver()
    await driver.verify_connectivity()


async def close():
    global _driver
    if _driver is not None:
        await _driver.close()
        _driver = None


@asynccontextmanager
async def get_session():
    driver = get_driver()
    async with driver.session(database=settings.neo4j_dbname) as session:
        yield session


def run_constraints():
    import asyncio

    cypher_file = Path(__file__).parent / "constraints.cypher"
    statements = [
        s.strip()
        for s in cypher_file.read_text().split(";")
        if s.strip()
    ]

    async def _run():
        async with get_session() as session:
            for stmt in statements:
                await session.run(stmt)

    asyncio.run(_run())
