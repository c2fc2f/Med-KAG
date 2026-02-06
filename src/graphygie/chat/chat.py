"""
This module defines the Message class, which represents a single message
in a chat conversation, as well as the Chat type alias (a list of messages).
"""

from typing import Any, List


class Message:
    """
    Represents a single message in a chat, containing a role and content.

    Attributes:
    - role (str): The role of the message sender (e.g., "user", "assistant",
        "system").
    - content (str): The textual content of the message.
    - **kwargs: Additional keyword arguments
    """

    def __init__(self, role: str, content: str, **kwargs) -> None:
        """
        Initializes a Message object.

        Parameters:
        - role (str): The role of the sender.
        - content (str): The message content.
        """
        self._role: str = role
        self._content: str = content
        self._other: dict[str, Any] = kwargs

    @property
    def role(self) -> str:
        """Gets the role of the message sender."""
        return self._role

    @role.setter
    def role(self, role: str) -> None:
        """Sets the role of the message sender."""
        self._role = role

    @property
    def content(self) -> str:
        """Gets the content of the message."""
        return self._content

    @content.setter
    def content(self, content: str) -> None:
        """Sets the content of the message."""
        self._content = content

    def to_dict(self) -> dict[str, str]:
        """
        Converts the message to a dictionary format.

        Returns:
        - dict: A dictionary with 'role' and 'content' keys.
        """
        return {"role": self.role, "content": self.content} | self._other


# A chat conversation is simply a list of messages.
type Chat = List[Message]
