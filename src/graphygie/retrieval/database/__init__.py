"""
This module exposes the public interface for the database layer, including:

- Database: Abstract base class defining the database interface.
- Neo4j: Concrete implementation of the Database interface using Neo4j.
"""

from .database import Database

__all__: list[str] = [
    "Database",
]
