"""
This module initializes the Neo4j components, specifically exposing the
Neo4j class for graph database operations and session management.
"""

from .neo4j import Neo4j

__all__: list[str] = [
    "Neo4j",
]
