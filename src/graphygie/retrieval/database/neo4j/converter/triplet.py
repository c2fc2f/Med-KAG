"""
This module defines the Triplet class, a concrete implementation of the
converter interface that transforms Neo4j Graph query results into a
human-readable triplet string representation, where each relationship
is rendered as a directed triplet:
    <StartNode:{props}> -[RELATION_TYPE:{props}]-> <EndNode:{props}>.
"""

from neo4j.graph import Graph


class Triplet:
    """
    A converter that transforms a Neo4j Graph result into a human-readable
    triplet string representation.

    Each relationship in the graph is rendered as a directed triplet:
        <StartNode:{prop: value}> -[RELATION_TYPE:{prop: value}]-> <EndNode:{prop: value}>.

    Example output:
        <Alice:{age: 30}> -[KNOWS:{since: 2020}]-> <Bob:{age: 25}>.
        <Bob:{age: 25}> -[WORKS_AT:{}]-> <Acme Corp:{}>.

    Nodes are identified by their "name" or "title" property (in that order
    of priority). If neither is present, the node is labeled "Node_<id>".
    The "name" and "title" properties are never included in the property block
    since they are already used as the node identifier.

    Usage:
        converter = Triplet()
        result = converter(
            graph,
            excluded_properties=["internal_id", "embedding"]
        )
    """

    def __call__(self, graph: Graph, excluded_properties: list[str]) -> str:
        def format_properties(props: dict[str, str]) -> str:
            """Helper method to format properties as a string."""
            if not props:
                return ""
            prop_str: str = ", ".join(f"{k}: {v}" for k, v in props.items())
            return f" {{{prop_str}}}"

        node_labels: dict[int, str] = {}
        node_properties: dict[int, dict[str, str]] = {}
        for node in graph.nodes:
            name = node.get("name") or node.get("title") or f"Node_{node.id}"
            node_labels[node.id] = name
            node_properties[node.id] = {
                k: v
                for k, v in dict(node).items()
                if k not in ["name", "title"] + excluded_properties
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
