from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.config import settings
from infrastructure.db import mongo, neo4j


@asynccontextmanager
async def lifespan(app: FastAPI):
    mongo.init_client(settings.mongodb_uri)
    await neo4j.connect()

    yield

    await neo4j.close()
    mongo.close()
