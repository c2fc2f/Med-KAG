"""
This module defines the Neo4j class, a concrete implementation of the Database
interface that connects to a Neo4j graph database and formats query results as
readable text.
"""

import time
from .database import Database
from neo4j import Driver, GraphDatabase, Query, Result
from neo4j.graph import Graph
from typing import Any, Optional, cast


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
        excluded_properties: list[str] = list(),
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
        self._excluded_properties: list[str] = excluded_properties
        self._info = None

    def info(self) -> Optional[dict[str, Any]]:
        return self._info

    def query(self, query: str) -> str:
        def format_properties(props: dict) -> str:
            """Helper method to format properties as a string."""
            if not props:
                return ""
            prop_str = ", ".join(f"{k}: {v}" for k, v in props.items())
            return f" {{{prop_str}}}"

        start = time.perf_counter()

        self._driver.verify_connectivity()
        with self._driver.session(database=self._database) as session:
            try:
                result: Result = session.run(cast(Query, query))
            except:
                end = time.perf_counter()
                self._info = {
                    "errors": 1,
                    "nodes": 0,
                    "edges": 0,
                    "time": (end - start) * 1000,
                }
                return ""

            graph: Graph = result.graph()

            end = time.perf_counter()
            self._info = {
                "errors": 0,
                "nodes": len(graph.nodes),
                "edges": len(graph.relationships),
                "time": (end - start) * 1000,
            }

            node_labels: dict[int, str] = {}
            node_properties: dict[int, dict] = {}
            for node in graph.nodes:
                name = node.get("name") or node.get("title") or f"Node_{node.id}"
                node_labels[node.id] = name
                node_properties[node.id] = {
                    k: v
                    for k, v in dict(node).items()
                    if k not in ["name", "title"] + self._excluded_properties
                }

            textual_rels: list[str] = []
            for rel in graph.relationships:
                if rel.start_node is None:
                    start = "<empty>"
                    start_props = {}
                else:
                    start = node_labels[rel.start_node.id]
                    start_props = node_properties[rel.start_node.id]

                if rel.end_node is None:
                    end = "<empty>"
                    end_props = {}
                else:
                    end = node_labels[rel.end_node.id]
                    end_props = node_properties[rel.end_node.id]

                rel_type = rel.type
                rel_props = dict(rel)

                start_str = f"{start}:{format_properties(start_props)}"
                end_str = f"{end}:{format_properties(end_props)}"
                rel_str = f"[{rel_type}:{format_properties(rel_props)}]"

                textual_rels.append(f"{start_str} -{rel_str}-> {end_str}.")

            return "\n".join(textual_rels)

    def __del__(self) -> None:
        """
        Closes the Neo4j driver connection when the object is deleted.
        """
        self._driver.close()
