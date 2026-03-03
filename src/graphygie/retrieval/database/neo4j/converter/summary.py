"""
This module defines the Summary class, transforms Neo4j Graph query results
into a string and then summarizing it using a .
"""

from typing import Callable, override
from neo4j.graph import Graph
from graphygie.chat import Chattable, Message
from graphygie.info import Info
from util import Serializable

import time


class Summary(Info):
    """
    A converter that transforms a Neo4j Graph result into a string by chaining
        two steps:
        1. A converter turns the raw graph into an intermediate textual
           representation (e.g. triplets).
        2. A summarizer condenses that representation into a concise summary.
    """

    def __init__(
        self,
        converter: Callable[[Graph, list[str]], str],
        summarizer: Chattable,
    ) -> None:
        """
        Initializes the Summary converter.

        Parameters:
        - converter (Callable[[Graph, list[str]], str]): A callable that
            converts a Neo4j Graph and a list of excluded property keys into
            an intermediate string representation passed to the summarizer.
        - summarizer (Chattable): A chat-capable summarizer used to
            summarize the intermediate string into a concise natural language
            response.
        """

        self._converter: Callable[[Graph, list[str]], str] = converter
        self._summarizer: Chattable = summarizer
        self._info: dict[str, Serializable] | None = None

    @override
    def info(self) -> dict[str, Serializable] | None:
        return self._info

    def __call__(self, graph: Graph, excluded_properties: list[str]) -> str:
        self._info = {
            "name": self.__class__.__name__,
        }

        start: float = time.perf_counter()

        convert: str = self._converter(graph, excluded_properties)

        if isinstance(self._converter, Info):
            self._info["converter"] = self._converter.info()

        self._info["inner-result"] = convert

        res: str = self._summarizer.chat(
            chat=[
                Message(
                    role="user",
                    content=convert,
                )
            ]
        )

        self._info["summarizer"] = self._summarizer.info()

        end: float = time.perf_counter()

        self._info["time"] = (end - start) * 1000

        return res
