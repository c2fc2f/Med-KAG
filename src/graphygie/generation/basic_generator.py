"""
This module defines the BasicGenerator class, which combines a retriever and a
generator to process a chat sequence and produce responses in a structured
pipeline.
"""

from graphygie.chat import Chattable, Chat
from typing import Callable, override

import logging
import time

from util import Serializable


class BasicGenerator(Chattable):
    """
    A pipeline-based generator that uses two LLMs:
    - A retriever to fetch or infer relevant context.
    - A generator to produce the final response.
    """

    def __init__(
        self,
        retriever: Chattable,
        generator: Chattable,
        chat: Chat,
        maker: Callable[[Chat, str], Chat],
    ) -> None:
        """
        Initializes the BasicGenerator pipeline.

        Parameters:
        - retriever (Chattable): The LLM used to retrieve context or
            information.
        - generator (Chattable): The LLM used to generate the final response.
        - chat (Chat): The initial chat history.
        - maker (Callable[[Chat, str], Chat]): A function that merges the
            existing chat
          with the retrieved result to build the input for the generator.
        """
        self._retriever: Chattable = retriever
        self._generator: Chattable = generator
        self._chat: Chat = chat
        self._maker: Callable[[Chat, str], Chat] = maker
        self._info: dict[str, Serializable] | None = None

    @override
    def info(self) -> dict[str, Serializable] | None:
        return self._info

    @override
    def chat(self, chat: Chat) -> str:
        logger: logging.Logger = logging.getLogger(name=__name__)
        self._info = {
            "name": self.__class__.__name__,
        }

        start: float = time.perf_counter()

        info: str = self._retriever.chat(chat)
        self._info["retriever"] = self._retriever.info()

        logger.info(msg=info)

        chat = self._maker(self._chat, info) + chat

        result: str = self._generator.chat(chat)
        self._info["generator"] = self._generator.info()

        end: float = time.perf_counter()
        self._info["time"] = (end - start) * 1000

        return result
