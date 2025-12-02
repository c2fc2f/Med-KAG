"""
This module defines the abstract interface for a Language Model (LLM)
that can generate responses or queries based on a chat history.
"""

from abc import abstractmethod
from typing import Optional
from graphygie.llm.llm import LLM


class LLMExtra(LLM):
    """
    Abstract base class for language models that has extra information.
    """

    @abstractmethod
    def info(self) -> Optional[dict[str, int]]:
        """Returns statistics from the last query"""
        ...
