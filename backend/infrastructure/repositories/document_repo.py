from neo4j import AsyncSession

from .abstractions.document_repo import AbstractDocumentRepo


class Neo4jDocumentRepo(AbstractDocumentRepo):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user_node(self, user_id: str, name: str, created_at: str) -> None:
        await self.session.run(
            "MERGE (u:User {user_id: $user_id}) ON CREATE SET u.name = $name, u.created_at = $created_at",
            user_id=user_id, name=name, created_at=created_at,
        )

    async def create_document(self, id: str, user_id: str, filename: str, subject: str,
                               file_path: str, page_count: int, created_at: str) -> dict:
        result = await self.session.run("""
            MATCH (u:User {user_id: $user_id})
            CREATE (d:Document {id: $id, user_id: $user_id, filename: $filename,
                subject: $subject, file_path: $file_path, status: 'pending',
                page_count: $page_count, created_at: $created_at})
            CREATE (u)-[:OWNS]->(d)
            RETURN d
        """, id=id, user_id=user_id, filename=filename, subject=subject,
             file_path=file_path, page_count=page_count, created_at=created_at)
        return (await result.single())["d"]

    async def get_user_documents(self, user_id: str) -> list[dict]:
        result = await self.session.run(
            "MATCH (u:User {user_id: $user_id})-[:OWNS]->(d:Document) RETURN d ORDER BY d.created_at DESC",
            user_id=user_id,
        )
        return [record["d"] async for record in result]

    async def update_document_status(self, user_id: str, doc_id: str, status: str) -> None:
        await self.session.run(
            "MATCH (u:User {user_id: $user_id})-[:OWNS]->(d:Document {id: $id}) SET d.status = $status",
            user_id=user_id, id=doc_id, status=status,
        )

    async def delete_document_and_concepts(self, user_id: str, doc_id: str) -> None:
        await self.session.run("""
            MATCH (u:User {user_id: $user_id})-[:OWNS]->(d:Document {id: $id})
            OPTIONAL MATCH (d)-[:CONTAINS]->(c:Concept)
            DETACH DELETE d, c
        """, user_id=user_id, id=doc_id)
