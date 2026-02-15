"""
This module defines the OpenAI class, a concrete implementation of the
Chattable interface, which uses the OpenAI API to generate responses from a
chat history.
"""

from dataclasses import asdict
import logging
from typing import Any, Optional, Callable, cast
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionFunctionToolParam,
    ChatCompletionMessageFunctionToolCall,
    ChatCompletionMessageParam,
)
from openai.types.shared_params.function_definition import FunctionDefinition
from graphygie.chat import Chattable, Chat, Message
from .tools.tool import Tool

import json
import openai
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
        chat: Chat = list(),
        host: Optional[str] = None,
        tools: list[Tool] = list(),
        cleaner: Optional[Callable[[str], str]] = None,
        model_params: Optional[dict[str, Any]] = None,
        **kwargs,
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
            base_url=host, api_key=api_key, **kwargs
        )
        self._model: str = model
        self._chat: Chat = chat
        self._tools: list[Tool] = tools
        self._cleaner: Optional[Callable[[str], str]] = cleaner
        self._model_params: Optional[dict[str, Any]] = model_params
        self._info: Optional[dict[str, Any]] = None

    def info(self) -> Optional[dict[str, Any]]:
        return self._info

    def chat(self, chat: Chat = list()) -> str:
        logger: logging.Logger = logging.getLogger(__name__)

        chat = self._chat + chat

        logging.info([message.to_dict() for message in chat])

        start: float = time.perf_counter()

        response: ChatCompletion = self._client.chat.completions.create(
            model=self._model,
            messages=[
                cast(ChatCompletionMessageParam, message.to_dict()) for message in chat
            ],
            tools=[
                ChatCompletionFunctionToolParam(
                    function=FunctionDefinition(
                        name=tool.name,
                        description=tool.description,
                        parameters=asdict(tool.parameters),
                        strict=True,
                    ),
                    type="function",
                )
                for tool in self._tools
            ],
            **(self._model_params or {}),
        )
        res: str = response.choices[0].message.content or ""
        while response.choices[0].message.tool_calls is not None:
            chat.append(Message(response.choices[0].message.role, res))
            for call in response.choices[0].message.tool_calls:
                if not isinstance(call, ChatCompletionMessageFunctionToolCall):
                    continue
                func: Callable | None = next(
                    (tool for tool in self._tools if tool.name == call.function.name),
                    None,
                )
                result = (
                    func(**json.loads(call.function.arguments))
                    if func is not None
                    else ""
                )
                chat.append(Message("tool", str(result), tool_name=call.function.name))
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    cast(ChatCompletionMessageParam, message.to_dict())
                    for message in chat
                ],
                tools=[
                    ChatCompletionFunctionToolParam(
                        function=FunctionDefinition(
                            name=tool.name,
                            description=tool.description,
                            parameters=asdict(tool.parameters),
                            strict=True,
                        ),
                        type="function",
                    )
                    for tool in self._tools
                ],
                **(self._model_params or {}),
            )
            res = response.choices[0].message.content or ""

        end: float = time.perf_counter()
        self._info = {
            "name": self.__class__.__name__,
            "full-response": res,
            "time": (end - start) * 1000,
        }

        logger.info(res)
        if self._cleaner is not None:
            return self._cleaner(res)
        return res
