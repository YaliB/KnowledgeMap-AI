from neo4j import AsyncSession

from .abstractions.concept_repo import AbstractConceptRepo


class Neo4jConceptRepo(AbstractConceptRepo):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_concept(self, id: str, user_id: str, document_id: str, name: str,
                              definition: str, subject: str, importance: float,
                              tags: list[str], embedding: list[float], created_at: str) -> dict:
        result = await self.session.run("""
            MATCH (d:Document {id: $document_id, user_id: $user_id})
            CREATE (c:Concept {id: $id, user_id: $user_id, name: $name,
                definition: $definition, subject: $subject, importance: $importance,
                tags: $tags, embedding: $embedding, created_at: $created_at})
            CREATE (d)-[:CONTAINS]->(c)
            RETURN c
        """, id=id, user_id=user_id, document_id=document_id, name=name,
             definition=definition, subject=subject, importance=importance,
             tags=tags, embedding=embedding, created_at=created_at)
        return (await result.single())["c"]
