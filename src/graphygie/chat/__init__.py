"""
This module exposes the public interface for the LLM components, including:

- Chat: A list of Message instances forming a conversation.
- Chattable: Abstract base class for chattable object.
"""

from .chat import Message, Chat
from .chattable import Chattable


__all__: list[str] = [
    "Message",
    "Chat",
    "Chattable",
]
