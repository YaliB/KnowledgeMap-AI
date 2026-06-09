#!/usr/bin/env python3
"""Delete every node and relationship belonging to a given user from Neo4j."""

import os
from neo4j import GraphDatabase

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USERNAME") or os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "password")

USER_ID = os.environ.get("PURGE_USER_ID", "user_a63e7852")

def purge(driver):
    with driver.session() as session:
        session.run("MATCH (n:Concept {user_id: $uid}) DETACH DELETE n", uid=USER_ID)
        session.run("MATCH (n:Document {user_id: $uid}) DETACH DELETE n", uid=USER_ID)
        session.run("MATCH (n:User {user_id: $uid}) DETACH DELETE n", uid=USER_ID)

        remaining = session.run(
            "MATCH (n {user_id: $uid}) RETURN count(n) AS n", uid=USER_ID
        ).single()["n"]
        print(f"✓ Purged all nodes for {USER_ID} — {remaining} remaining")

if __name__ == "__main__":
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        purge(driver)
    finally:
        driver.close()
