"""
This module defines the Neo4j class, a concrete implementation of the Database
interface that connects to a Neo4j graph database and formats query results as
readable text.
"""

from neo4j import Driver, GraphDatabase, Result
from neo4j.graph import Graph
from typing import Callable, LiteralString, cast, override
from graphygie.info import Info
from graphygie.retrieval.database import Database
from util import Serializable

import time


class Neo4j(Database):
    """
    A Neo4j database implementation of the Database interface.

    Connects to a Neo4j instance and runs Cypher queries,
    returning the results in a human-readable format.
    """

    def __init__(
        self,
        uri: str,
        username: str,
        password: str,
        database: str,
        converter: Callable[[Graph, list[str]], str],
        excluded_properties: list[str] | None = None,
    ) -> None:
        """
        Initializes the Neo4j driver.

        Parameters:
        - uri (str): The URI of the Neo4j server
            (e.g., "bolt://localhost:7687").
        - username (str): Username for authentication.
        - password (str): Password for authentication.
        - database (str): The name of the Neo4j database to connect to.
        - converter (Callable[[Graph, list[str]], str]): A callable that
            converts a Neo4j Graph resultinto a string.
        - excluded_properties (list[str]): List of property names to exclude
            from query results (default: empty list).
        """

        self._driver: Driver = GraphDatabase.driver(  # pyright: ignore[reportUnknownMemberType]
            uri,
            auth=(
                username,
                password,
            ),
        )
        self._database: str = database
        self._excluded_properties: list[str] | None = excluded_properties
        self._info: dict[str, Serializable] | None = None
        self._converter: Callable[[Graph, list[str]], str] = converter

    @override
    def info(self) -> dict[str, Serializable] | None:
        return self._info

    @override
    def query(
        self,
        query: str,
        parameters: dict[str, object] | None = None,
        **kwargs: object,
    ) -> str:
        startt: float = time.perf_counter()

        self._driver.verify_connectivity()  # pyright: ignore[reportUnknownMemberType]
        with self._driver.session(  # pyright: ignore[reportUnknownMemberType]
            database=self._database,
        ) as session:
            try:
                result: Result = session.run(
                    query=cast(LiteralString, query),
                    parameters=parameters,
                    **kwargs,
                )
            except:
                endt: float = time.perf_counter()
                self._info = {
                    "name": self.__class__.__name__,
                    "errors": 1,
                    "nodes": 0,
                    "edges": 0,
                    "time": (endt - startt) * 1000,
                }
                return ""

            graph: Graph = result.graph()
            endt = time.perf_counter()

            res: str = self._converter(graph, self._excluded_properties or [])

            self._info = {
                "name": self.__class__.__name__,
                "errors": 0,
                "nodes": len(graph.nodes),
                "edges": len(graph.relationships),
                "time": (endt - startt) * 1000,
            }

            if isinstance(self._converter, Info):
                self._info["converter"] = self._converter.info()

            return res

    def __del__(self) -> None:
        """
        Closes the Neo4j driver connection when the object is deleted.
        """
        self._driver.close()
