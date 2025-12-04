"""
This module defines the Ollama class, a concrete implementation of the LLM
interface, which uses the Ollama API to generate responses from a chat
history.
"""

from typing import Any, Optional, Callable
from ollama import Client, ChatResponse
from .llm import LLM
from .chat import Chat


class Ollama(LLM):
    """
    An implementation of the LLM interface using the Ollama API.

    This class manages an ongoing chat session with a specified model,
    and optionally allows post-processing of the response using a cleaner
    function.
    """

    def __init__(
        self,
        model: str,
        chat: Chat = list(),
        host: Optional[str] = None,
        cleaner: Optional[Callable[[str], str]] = None,
        model_params: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initializes the Ollama LLM client.

        Parameters:
        - model (str): The name of the model to use (e.g., "llama3").
        - chat (Chat, optional): Initial list of messages to include in the
            chat history. Defaults to an empty list.
        - host (Optional[str]): The host URL for the Ollama server. If None,
            defaults are used.
        - cleaner (Optional[Callable[[str], str]]): A function to post-process
            the model's response.
        - model_params: (Optional[dict[str, Any]]): Extra parameters for the
            model.
        - **kwargs: Additional keyword arguments passed to the Ollama client.
        """

        self._client: Client = Client(host, **kwargs)
        self._model: str = model
        self._chat: Chat = chat
        self._cleaner: Optional[Callable[[str], str]] = cleaner
        self._model_params: Optional[dict[str, Any]] = model_params

    def chat(self, chat: Chat = list()) -> str:
        chat = self._chat + chat
        response: ChatResponse = self._client.chat(
            model=self._model,
            messages=[message.to_dict() for message in chat],
            **(self._model_params or {}),
        )
        if response.message.content is None:
            return ""
        if self._cleaner is not None:
            return self._cleaner(response.message.content)
        return response.message.content
