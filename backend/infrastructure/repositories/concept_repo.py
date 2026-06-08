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
        return dict((await result.single())["c"])

    async def get_concepts_for_user(self, user_id: str) -> list[dict]:
        result = await self.session.run("""
            MATCH (u:User {user_id: $user_id})-[:OWNS]->(d:Document)-[:CONTAINS]->(c:Concept)
            RETURN c, d.filename AS source_document
            ORDER BY c.created_at DESC
        """, user_id=user_id)
        return [
            {**dict(record["c"]), "source_document": record["source_document"]}
            async for record in result
        ]

    async def get_concept_by_id(self, concept_id: str, user_id: str) -> dict | None:
        result = await self.session.run("""
            MATCH (c:Concept {id: $concept_id})
            WHERE c.user_id = $user_id
            RETURN c
        """, concept_id=concept_id, user_id=user_id)
        record = await result.single()
        return dict(record["c"]) if record else None

    async def get_concept_neighbors(self, concept_id: str, user_id: str) -> list[dict]:
        result = await self.session.run("""
            MATCH (c:Concept {id: $concept_id})-[r:RELATED_TO]-(neighbor:Concept)
            WHERE c.user_id = $user_id
            RETURN neighbor, r.weight AS weight, r.rel_type AS rel_type
            ORDER BY r.weight DESC
            LIMIT 10
        """, concept_id=concept_id, user_id=user_id)
        return [
            {**dict(record["neighbor"]), "weight": record["weight"], "rel_type": record["rel_type"]}
            async for record in result
        ]

    async def create_related_to(self, concept_a_id: str, concept_b_id: str, props: dict) -> None:
        await self.session.run("""
            MATCH (a:Concept {id: $concept_a_id})
            MATCH (b:Concept {id: $concept_b_id})
            CREATE (a)-[:RELATED_TO {
                weight: $weight,
                rel_type: $rel_type,
                cross_subject: $cross_subject,
                explanation: $explanation,
                created_at: $created_at
            }]->(b)
        """, concept_a_id=concept_a_id, concept_b_id=concept_b_id, **props)

    async def vector_similarity_search(self, embedding: list[float], user_id: str,
                                       top_k: int = 10) -> list[dict]:
        result = await self.session.run("""
            CALL db.index.vector.queryNodes('concept-embeddings', $top_k, $embedding)
            YIELD node, score
            WHERE node.user_id = $user_id
              AND score > 0.75
            MATCH (d:Document)-[:CONTAINS]->(node)
            RETURN node, score, d.filename AS document_name
            ORDER BY score DESC
        """, embedding=embedding, user_id=user_id, top_k=top_k)
        return [
            {"node": {**dict(record["node"]), "document_name": record["document_name"]}, "score": record["score"]}
            async for record in result
        ]

    async def get_full_graph(self, user_id: str) -> dict:
        result = await self.session.run("""
            MATCH (u:User {user_id: $user_id})-[:OWNS]->(d:Document)-[:CONTAINS]->(c:Concept)
            OPTIONAL MATCH (c)-[r:RELATED_TO]->(c2:Concept {user_id: $user_id})
            RETURN
              collect(DISTINCT {
                id: c.id,
                name: c.name,
                subject: c.subject,
                importance: c.importance,
                definition: c.definition,
                source_document: d.filename,
                connection_count: size([(c)-[:RELATED_TO]-() | 1])
              }) AS nodes,
              collect(DISTINCT {
                source: c.id,
                target: c2.id,
                weight: r.weight,
                rel_type: r.rel_type,
                cross_subject: r.cross_subject
              }) AS edges
        """, user_id=user_id)
        record = await result.single()
        if record is None:
            return {"nodes": [], "edges": []}
        return {"nodes": list(record["nodes"]), "edges": list(record["edges"])}

    async def get_distinct_subjects(self, user_id: str) -> list[dict]:
        result = await self.session.run("""
            MATCH (u:User {user_id: $user_id})-[:OWNS]->(:Document)-[:CONTAINS]->(c:Concept)
            RETURN DISTINCT c.subject AS subject, count(c) AS concept_count
            ORDER BY concept_count DESC
        """, user_id=user_id)
        return [
            {"subject": record["subject"], "concept_count": record["concept_count"]}
            async for record in result
        ]
