"""
This module provides the abstract base class for text embedding engines. It
defines the required interface for converting natural language into vectorized
Embedding objects.
"""

from abc import ABC, abstractmethod
from typing import override
from graphygie.chat.chat import Chat
from graphygie.chat.chattable import Chattable
from .embedding import Embedding


class Embedder(Chattable, ABC):
    """
    Abstract Base Class for embedding models.

    Inherits from Info to provide metadata or versioning information about the
    underlying model. Subclasses must implement the 'embeds' method.
    """

    @abstractmethod
    def embeds(self, inputs: list[str]) -> list[Embedding]:
        """
        Transforms a list of strings into a list of Embedding objects.

        Args:
            inputs (List[str]): A list of text strings to be vectorized.
                Defaults to an empty list.

        Returns:
            List[Embedding]: A list containing the generated vector
                embeddings and their respective scores.
        """
        ...

    @override
    def chat(self, chat: Chat) -> str:
        return "\n".join(
            " ".join(str(em) for em in e)
            for e in self.embeds(
                [f"Role: {m['role']}\nMessage: {m['content']}" for m in chat]
            )
        )
