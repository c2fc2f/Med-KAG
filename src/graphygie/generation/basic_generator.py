"""
This module defines the BasicGenerator class, which combines a retriever and a
generator LLM to process a chat sequence and produce responses in a structured
pipeline.
"""

import logging
import time
from graphygie.llm import LLM
from graphygie.llm.chat import Chat
from typing import Any, Callable, Optional


class BasicGenerator(LLM):
    """
    A pipeline-based generator that uses two LLMs:
    - A retriever LLM to fetch or infer relevant context.
    - A generator LLM to produce the final response.
    """

    def __init__(
        self,
        retriever: LLM,
        generator: LLM,
        chat: Chat,
        maker: Callable[[Chat, str], Chat],
    ) -> None:
        """
        Initializes the BasicGenerator pipeline.

        Parameters:
        - retriever (LLM): The LLM used to retrieve context or information.
        - generator (LLM): The LLM used to generate the final response.
        - chat (Chat): The initial chat history.
        - maker (Callable[[Chat, str], Chat]): A function that merges the
            existing chat
          with the retrieved result to build the input for the generator.
        """
        self._retriever: LLM = retriever
        self._generator: LLM = generator
        self._chat: Chat = chat
        self._maker: Callable[[Chat, str], Chat] = maker
        self._info: Optional[dict[str, Any]] = None

    def info(self) -> Optional[dict[str, Any]]:
        return self._info

    def chat(self, chat: Chat = list()) -> str:
        logger: logging.Logger = logging.getLogger(__name__)
        self._info = dict()

        start: float = time.perf_counter()

        info: str = self._retriever.chat(chat)
        self._info["retriever"] = self._retriever.info()

        logger.info(info)

        chat = self._maker(self._chat, info) + chat

        result: str = self._generator.chat(chat)
        self._info["generator"] = self._generator.info()

        end: float = time.perf_counter()
        self._info["time"] = (end - start) * 1000

        return result
