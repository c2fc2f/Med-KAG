"""
This module defines the `generator_system_prompt` helper, which takes the
initial (system) message of a chat and injects the retrieved content into the
`{{RETRIEVAL}}` placeholder, returning a new one-message Chat to be fed to a
generator LLM.
"""

from graphygie.chat import Chat, Message


def generator_system_prompt(chat: Chat, content: str) -> Chat:
    """
    Builds a new system prompt by taking the first message of the given chat
    and replacing the `{{RETRIEVAL}}` placeholder with the provided content.

    Parameters:
    - chat (Chat): The chat history; the first message is expected to be the
        system prompt.
    - content (str): The retrieved text that will replace `{{RETRIEVAL}}` in
        the system message.
      If empty, the placeholder is replaced with "<empty>".

    Returns:
    - Chat: A single-message chat containing the updated system prompt.

    Raises:
    - ValueError: If the provided chat is empty.
    """
    if not chat:
        raise ValueError("expected a non-empty chat.")

    message: Message = chat[0]

    if "{{RETRIEVAL}}" not in message["content"]:
        raise ValueError("expected a chat which contains {{RETRIEVAL}}")

    if not content:
        content = "<empty>"

    return [
        Message(
            role=message["role"],
            content=message["content"].replace("{{RETRIEVAL}}", content),
        )
    ]
