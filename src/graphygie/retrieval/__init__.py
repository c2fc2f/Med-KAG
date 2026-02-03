"""
This module exposes the public interface for the graph-based retriever
component.
"""

from .graph import GraphLLM

__all__: list[str] = ["GraphLLM"]
