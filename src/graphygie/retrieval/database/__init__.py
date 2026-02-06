"""
This module exposes the public interface for the database layer, including:

- Database: Abstract base class defining the database interface.
- Neo4j: Concrete implementation of the Database interface using Neo4j.
"""

from .database import Database
from .neo4j import Neo4j

__all__: list[str] = [
    "Database",
    "Neo4j",
]
