"""
This module defines the Neo4j class, a concrete implementation of the Database
interface that connects to a Neo4j graph database and formats query results as
readable text.
"""

from neo4j import Driver, GraphDatabase, Result
from neo4j.graph import Graph
from typing import Any, LiteralString, cast, override
from graphygie.retrieval.database import Database

import time

from util import Serializable


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
        - excluded_properties (list[str]): List of property names to exclude
            from query results (default: empty list).
        """

        self._driver: Driver = GraphDatabase.driver(uri, auth=(username, password))
        self._database: str = database
        self._excluded_properties: list[str] | None = excluded_properties
        self._info: dict[str, Serializable] | None = None

    @override
    def info(self) -> dict[str, Serializable] | None:
        return self._info

    @override
    def query(self, query: str, **kwargs: Any) -> str:
        def format_properties(props: dict[str, str]) -> str:
            """Helper method to format properties as a string."""
            if not props:
                return ""
            prop_str = ", ".join(f"{k}: {v}" for k, v in props.items())
            return f" {{{prop_str}}}"

        startt: float = time.perf_counter()

        self._driver.verify_connectivity()
        with self._driver.session(database=self._database) as session:
            try:
                result: Result = session.run(cast(LiteralString, query), **kwargs)
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
            self._info = {
                "name": self.__class__.__name__,
                "errors": 0,
                "nodes": len(graph.nodes),
                "edges": len(graph.relationships),
                "time": (endt - startt) * 1000,
            }

            node_labels: dict[int, str] = {}
            node_properties: dict[int, dict[str, str]] = {}
            for node in graph.nodes:
                name = node.get("name") or node.get("title") or f"Node_{node.id}"
                node_labels[node.id] = name
                node_properties[node.id] = {
                    k: v
                    for k, v in dict(node).items()
                    if k not in ["name", "title"] + (self._excluded_properties or [])
                }

            textual_rels: list[str] = []
            for rel in graph.relationships:
                if rel.start_node is None:
                    start: str = "<empty>"
                    start_props: dict[str, str] = {}
                else:
                    start = node_labels[rel.start_node.id]
                    start_props = node_properties[rel.start_node.id]

                if rel.end_node is None:
                    end: str = "<empty>"
                    end_props: dict[str, str] = {}
                else:
                    end = node_labels[rel.end_node.id]
                    end_props = node_properties[rel.end_node.id]

                rel_type: str = rel.type
                rel_props: dict[str, str] = dict(rel)

                start_str = f"<{start}:{format_properties(start_props)}>"
                end_str = f"<{end}:{format_properties(end_props)}>"
                rel_str = f"[{rel_type}:{format_properties(rel_props)}]"

                textual_rels.append(f"{start_str} -{rel_str}-> {end_str}.")

            return "\n".join(textual_rels)

    def __del__(self) -> None:
        """
        Closes the Neo4j driver connection when the object is deleted.
        """
        self._driver.close()
