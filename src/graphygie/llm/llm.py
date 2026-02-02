"""
This module defines the abstract interface for a Language Model (LLM)
that can generate responses or queries based on a chat history.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from .chat import Chat


class LLM(ABC):
    """
    Abstract base class for language models that can handle chat interactions.
    """

    @abstractmethod
    def chat(self, chat: Chat = list()) -> str:
        """
        Handles a chat interaction by generating a query from the chat history
        and executing it on the graph database.

        Parameters:
        - chat (Chat, optional): The list of chat messages used as input.
            Defaults to an empty list.

        Returns:
        - str: The result of the query executed on the database.
        """
        ...

    @abstractmethod
    def info(self) -> Optional[dict[str, Any]]:
        """Returns statistics from the last chat"""
        ...
