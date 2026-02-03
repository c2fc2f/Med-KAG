"""
This module defines the Graph retriever class, which combines a language model
(LLM) and a graph database to answer chat-based queries.

The LLM generates a query from the chat history, which is then executed on the
database.
"""

import time
from typing import Any, Optional
from graphygie.llm import LLM
from graphygie.llm.chat import Chat
from util.unwrap import unwrap_or
from .database import Database
import logging


class GraphLLM(LLM):
    """
    A graph-based retriever that uses an LLM to generate a query from a chat
    history, then executes that query against a graph database.

    Attributes:
    - _llm (LLM): The language model used to generate queries.
    - _database (Database): The graph database used to retrieve information.
    """

    def __init__(self, llm: LLM, database: Database) -> None:
        """
        Initializes the Graph retriever with a language model and a database.

        Parameters:
        - llm (LLM): The language model used to interpret the chat history.
        - database (Database): The database queried with the generated output.
        """
        self._llm: LLM = llm
        self._database: Database = database
        self._info: Optional[dict[str, Any]] = None

    def info(self) -> Optional[dict[str, Any]]:
        return self._info

    def chat(self, chat: Chat = list()) -> str:
        logger: logging.Logger = logging.getLogger(__name__)
        self._info = dict()

        start: float = time.perf_counter()

        query: str = self._llm.chat(chat)
        self._info["model"] = unwrap_or(self._llm.info(), dict())
        self._info["query"] = query

        logger.info(query)

        result: str = self._database.query(query)
        self._info["database"] = unwrap_or(self._database.info(), dict())

        end: float = time.perf_counter()

        self._info["time"] = (end - start) * 1000

        return result
