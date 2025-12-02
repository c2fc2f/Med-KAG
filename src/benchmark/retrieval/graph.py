"""
This module defines the Graph retriever class, which combines a language model
(LLM) and a graph database to answer chat-based queries.

The LLM generates a query from the chat history, which is then executed on the
database.
"""

from typing import Optional
from benchmark.retrieval.database.neo4j import Neo4jExtra
from benchmark.llm import LLMExtra
from graphygie.llm import LLM
from graphygie.llm.chat import Chat
import logging


class GraphExtra(LLMExtra):
    """
    A graph-based retriever that uses an LLM to generate a query from a chat
    history, then executes that query against a graph database.

    Attributes:
    - _llm (LLM): The language model used to generate queries.
    - _database (Database): The graph database used to retrieve information.
    """

    def __init__(self, llm: LLM, database: Neo4jExtra) -> None:
        """
        Initializes the Graph retriever with a language model and a database.

        Parameters:
        - llm (LLM): The language model used to interpret the chat history.
        - database (Database): The database queried with the generated output.
        """
        self._llm: LLM = llm
        self._database: Neo4jExtra = database
        self._info = None

    def info(self) -> Optional[dict[str, int]]:
        return self._info

    def chat(self, chat: Chat = list()) -> str:
        logger: logging.Logger = logging.getLogger(__name__)

        query: str = self._llm.chat(chat)

        logger.info(query)

        result: str = self._database.query(query)
        self._info = self._database.info

        return result
