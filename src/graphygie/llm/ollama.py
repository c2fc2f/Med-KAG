"""
This module defines the Ollama class, a concrete implementation of the LLM
interface, which uses the Ollama API to generate responses from a chat
history.
"""

from dataclasses import asdict
from typing import Any, Optional, Callable
from ollama import Client, ChatResponse


from .tools.tool import Tool
from .llm import LLM
from .chat import Chat, Message


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
        tools: list[Tool] = list(),
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
        - tools (list[Tool]): List of tools that the model can use.
        - cleaner (Optional[Callable[[str], str]]): A function to post-process
            the model's response.
        - model_params: (Optional[dict[str, Any]]): Extra parameters for the
            model.
        - **kwargs: Additional keyword arguments passed to the Ollama client.
        """

        self._client: Client = Client(host, **kwargs)
        self._model: str = model
        self._chat: Chat = chat
        self._tools: list[Tool] = tools
        self._cleaner: Optional[Callable[[str], str]] = cleaner
        self._model_params: Optional[dict[str, Any]] = model_params

    def info(self) -> Optional[dict[str, Any]]:
        return None

    def chat(self, chat: Chat = list()) -> str:
        chat = self._chat + chat
        response: ChatResponse = self._client.chat(
            model=self._model,
            messages=[message.to_dict() for message in chat],
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": asdict(tool.parameters),
                    },
                }
                for tool in self._tools
            ],
            **(self._model_params or {}),
        )
        res = response.message.content or ""
        while response.message.tool_calls is not None:
            chat.append(Message(response.message.role, res))
            for call in response.message.tool_calls:
                func: Callable | None = next(
                    (tool for tool in self._tools if tool.name == call.function.name),
                    None,
                )
                result = func(**call.function.arguments) if func is not None else ""
                chat.append(Message("tool", str(result), tool_name=call.function.name))
            response: ChatResponse = self._client.chat(
                model=self._model,
                messages=[message.to_dict() for message in chat],
                tools=[tool._func for tool in self._tools],
                **(self._model_params or {}),
            )
            res = response.message.content or ""
        if self._cleaner is not None:
            return self._cleaner(res)
        return res
