"""
This module defines the abstract interface for a Database.
"""

from abc import ABC, abstractmethod
from typing import Any, override
from graphygie.chat import Chattable, Chat


class Database(Chattable, ABC):
    """
    Abstract base class for database access.
    """

    @abstractmethod
    def query(self, query: str, **kwargs: Any) -> str:
        """
        Executes a query string against the database.

        Parameters:
        - query (str): The query to execute.
        - **kwargs: Additional keyword arguments passed to the database for
            the query.

        Returns:
        - str: The result of the query.
        """
        ...

    @override
    def chat(self, chat: Chat) -> str:
        return self.query(
            query="\n\n".join(f"Role: {m.role}\nContent: {m.content}" for m in chat)
        )
