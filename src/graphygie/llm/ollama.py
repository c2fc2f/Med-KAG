"""
This module defines the Ollama class, a concrete implementation of the
Chattable interface, which uses the Ollama API to generate responses from a
chat history.
"""

from dataclasses import asdict
import logging
from typing import Any, Callable, override
from ollama import Client, ChatResponse
from graphygie.chat import Chattable, Chat, Message
from graphygie.info.info import Info
from util import Serializable
from .tools.tool import Tool

import time


class Ollama(Chattable):
    """
    An implementation of the Chattable interface using the Ollama API.

    This class manages an ongoing chat session with a specified model,
    and optionally allows post-processing of the response using a cleaner
    function.
    """

    def __init__(
        self,
        model: str,
        chat: Chat | None = None,
        host: str | None = None,
        tools: list[Tool] | None = None,
        cleaner: Callable[[str], str] | None = None,
        model_params: dict[str, Any] | None = None,  # pyright: ignore[reportExplicitAny]
        **kwargs: Any,  # pyright: ignore[reportAny, reportExplicitAny]
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

        self._client: Client = Client(host, **kwargs)  # pyright: ignore[reportAny]
        self._model: str = model
        self._chat: Chat | None = chat
        self._tools: list[Tool] | None = tools
        self._cleaner: Callable[[str], str] | None = cleaner
        self._model_params: dict[str, Any] | None = model_params  # pyright: ignore[reportExplicitAny]
        self._info: dict[str, Serializable] | None = None

    @override
    def info(self) -> dict[str, Serializable] | None:
        return self._info

    @override
    def chat(self, chat: Chat) -> str:
        logger: logging.Logger = logging.getLogger(name=__name__)

        chat = (self._chat or []) + chat

        logging.info(chat)

        start: float = time.perf_counter()

        response: ChatResponse = self._client.chat(  # pyright: ignore[reportUnknownMemberType]
            model=self._model,
            messages=chat,
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": asdict(obj=tool.parameters),
                    },
                }
                for tool in self._tools or []
            ],
            stream=False,
            **(self._model_params or {}),  # pyright: ignore[reportAny]
        )
        res: str = response.message.content or ""
        while response.message.tool_calls is not None:
            chat.append(
                Message(
                    role=response.message.role,
                    content=res,
                )
            )
            for call in response.message.tool_calls:
                func: Callable[..., object] | None = next(
                    (
                        tool
                        for tool in self._tools or []
                        if tool.name == call.function.name
                    ),
                    None,
                )
                result = func(**call.function.arguments) if func is not None else ""  # pyright: ignore[reportAny]
                chat.append(
                    Message(
                        role="tool",
                        content=str(result),
                        tool_name=call.function.name,
                    )
                )
            response = self._client.chat(  # pyright: ignore[reportUnknownMemberType]
                model=self._model,
                messages=chat,
                tools=[tool.func for tool in self._tools or []],
                stream=False,
                **(self._model_params or {}),  # pyright: ignore[reportAny]
            )
            res = response.message.content or ""

        end: float = time.perf_counter()
        self._info = {
            "name": self.__class__.__name__,
            "full-response": res,
            "time": (end - start) * 1000,
        }

        logger.info(msg=res)
        if self._cleaner is not None:
            res = self._cleaner(res)
            if isinstance(self._cleaner, Info):
                self._info["cleaner"] = self._cleaner.info()
        return res
