"""
This module exposes the public interface for the LLM components,
including:

- LLMExtra: A LLM abstraction with extra information
"""

from .llmextra import LLMExtra

__all__: list[str] = ["LLMExtra"]
