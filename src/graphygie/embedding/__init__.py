"""
This module exposes the primary interfaces and data structures for vector
embedding operations, facilitating easier imports for end-users.
"""

from .embedding import Embedding
from .embedder import Embedder
from .ollama import Ollama

__all__: list[str] = [
    "Embedding",
    "Embedder",
    "Ollama",
]
