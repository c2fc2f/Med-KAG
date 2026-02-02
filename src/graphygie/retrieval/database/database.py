"""
This module defines the abstract interface for a Database.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class Database(ABC):
    """
    Abstract base class for database access.
    """

    @abstractmethod
    def query(self, query: str) -> str:
        """
        Executes a query string against the database.

        Parameters:
        - query (str): The query to execute.

        Returns:
        - str: The result of the query.
        """
        ...

    @abstractmethod
    def info(self) -> Optional[dict[str, Any]]:
        """Returns statistics from the last query"""
        ...
