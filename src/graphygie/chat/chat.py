"""
This module defines the Message class, which represents a single message
in a chat conversation, as well as the Chat type alias (a list of messages).
"""

from typing import Required, TypedDict


class Message(TypedDict, total=False):
    """
    Represents a single message in a chat, containing a role and content.
    """

    role: Required[str]
    """The role of the message sender."""

    content: Required[str]
    """The textual content of the message."""

    tool_name: str
    """
    The name of the tool that produced this message. Only present for
    tool-role messages.
    """


# A chat conversation is simply a list of messages.
type Chat = list[Message]
