"""
This module defines the abstract interface for a chattable object that can
generate responses based on a chat history.
"""

from abc import ABC, abstractmethod
from graphygie.info import Info
from .chat import Chat


class Chattable(Info, ABC):
    """
    Abstract base class for chattable object that can handle chat
    interactions.
    """

    @abstractmethod
    def chat(self, chat: Chat) -> str:
        """
        Handles a chat interaction by generating a query from the chat history
        and executing it.

        Parameters:
        - chat (Chat, optional): The list of chat messages used as input.
            Defaults to an empty list.

        Returns:
        - str: The result of the query executed on the database.
        """
        ...
