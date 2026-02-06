"""
This module exposes the public interface for the LLM components, including:

- Ollama: Concrete implementation of LLM using the Ollama API.
- OpenAI: Concrete implementation of LLM using the OpenAI API.

"""

from .ollama import Ollama
from .openai import OpenAI


__all__: list[str] = [
    "Ollama",
    "OpenAI",
]
