"""
This module defines the OpenAI class, a concrete implementation of the
Chattable interface, which uses the OpenAI API to generate responses from a
chat history.
"""

from dataclasses import asdict
import logging
from typing import Any, Callable, cast, override
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionFunctionToolParam,
    ChatCompletionMessageFunctionToolCall,
    ChatCompletionMessageParam,
)
from openai.types.shared_params.function_definition import FunctionDefinition
from graphygie.chat import Chattable, Chat, Message
from graphygie.info.info import Info
from util import Serializable
from .tools.tool import Tool

import openai
import json
import time


class OpenAI(Chattable):
    """
    An implementation of the Chattable interface using the OpenAI API.

    This class manages an ongoing chat session with a specified model,
    and optionally allows post-processing of the response using a cleaner
    function.
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        chat: Chat | None = None,
        host: str | None = None,
        tools: list[Tool] | None = None,
        cleaner: Callable[[str], str] | None = None,
        model_params: dict[str, Any] | None = None,  # pyright: ignore[reportExplicitAny]
        **kwargs: Any,  # pyright: ignore[reportAny, reportExplicitAny]
    ) -> None:
        """
        Initializes the OpenAI LLM client.

        Parameters:
        - api_key (str): The API key used to authenticate requests to the
            OpenAI server.
        - model (str): The name of the model to use (e.g., "llama3").
        - chat (Chat, optional): Initial list of messages to include in the
            chat history. Defaults to an empty list.
        - host (Optional[str]): The host URL for the OpenAI server. If None,
            defaults are used.
        - tools (list[Tool]): List of tools that the model can use.
        - cleaner (Optional[Callable[[str], str]]): A function to post-process
            the model's response.
        - model_params: (Optional[dict[str, Any]]): Extra parameters for the
            model.
        """

        self._client: openai.OpenAI = openai.OpenAI(
            base_url=host,
            api_key=api_key,
            **kwargs,  # pyright: ignore[reportAny]
        )
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

        logging.info(msg=chat)

        start: float = time.perf_counter()

        response: ChatCompletion = self._client.chat.completions.create(
            model=self._model,
            messages=[
                cast(
                    ChatCompletionMessageParam,
                    message,
                )  # pyright: ignore[reportInvalidCast]
                for message in chat
            ],
            tools=[
                ChatCompletionFunctionToolParam(
                    function=FunctionDefinition(
                        name=tool.name,
                        description=tool.description,
                        parameters=asdict(obj=tool.parameters),
                        strict=True,
                    ),
                    type="function",
                )
                for tool in self._tools or []
            ],
            stream=False,
            **(self._model_params or {}),  # pyright: ignore[reportAny]
        )
        res: str = response.choices[0].message.content or ""
        while response.choices[0].message.tool_calls is not None:
            chat.append(
                Message(
                    role=response.choices[0].message.role,
                    content=res,
                )
            )
            for call in response.choices[0].message.tool_calls:
                if not isinstance(call, ChatCompletionMessageFunctionToolCall):
                    continue
                func: Callable[..., object] | None = next(
                    (
                        tool
                        for tool in self._tools or []
                        if tool.name == call.function.name
                    ),
                    None,
                )
                result = (
                    func(**json.loads(call.function.arguments))
                    if func is not None
                    else ""
                )
                chat.append(
                    Message(
                        role="tool",
                        content=str(result),
                        tool_name=call.function.name,
                    )
                )
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    cast(
                        ChatCompletionMessageParam,
                        message,
                    )  # pyright: ignore[reportInvalidCast]
                    for message in chat
                ],
                tools=[
                    ChatCompletionFunctionToolParam(
                        function=FunctionDefinition(
                            name=tool.name,
                            description=tool.description,
                            parameters=asdict(obj=tool.parameters),
                            strict=True,
                        ),
                        type="function",
                    )
                    for tool in self._tools or []
                ],
                stream=False,
                **(self._model_params or {}),  # pyright: ignore[reportAny]
            )
            res = response.choices[0].message.content or ""

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
