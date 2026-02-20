"""
This module defines the Graph retriever class, which combines a query
generator and a graph database to answer chat-based queries.
"""

from typing import override
from util import Serializable
from util.unwrap import unwrap_or
from graphygie.chat import Chattable, Chat
from .database import Database

import logging
import time


class Graph(Chattable):
    """
    A graph-based retriever that uses an retriever to generate a query from a
    chat history, then executes that query against a graph database.

    Attributes:
    - _retriever (Chattable): The retriever used to generate queries.
    - _database (Database): The graph database used to retrieve information.
    """

    def __init__(self, query_gen: Chattable, database: Database) -> None:
        """
        Initializes the Graph retriever with a query generator and a database.

        Parameters:
        - query_gen (Chattable): The query generator used to interpret the
            chat history into a query.
        - database (Database): The database queried with the generated output.
        """
        self._query_gen: Chattable = query_gen
        self._database: Database = database
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

        query: str = self._query_gen.chat(chat)
        self._info["query-generator"] = unwrap_or(
            value=self._query_gen.info(),
            default=dict(),
        )
        self._info["query"] = query

        logger.info(msg=query)

        result: str = self._database.query(query)
        self._info["database"] = unwrap_or(
            value=self._database.info(),
            default=dict(),
        )

        end: float = time.perf_counter()

        self._info["time"] = (end - start) * 1000

        return result
