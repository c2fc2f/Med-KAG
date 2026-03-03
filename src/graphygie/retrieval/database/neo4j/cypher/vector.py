"""
This module maps chat history to high-dimensional vectors and builds complex
Cypher queries that perform vector searches followed by variable-depth
neighborhood traversals.
"""

from typing import override
from graphygie.chat import Chattable, Chat
from graphygie.embedding.embedder import Embedder
from graphygie.embedding.embedding import Embedding
from util import Serializable
from util.unwrap import unwrap_or

import time


class Vector2Cypher(Chattable):
    """
    Generates Cypher queries based on the vector embedding of a chat history.

    Args:
        index (str): The name of the Neo4j vector index to query.
        embedder (Embedder): The engine used to vectorize the chat context.
        top_k (int): The number of nearest neighbors to retrieve.
        distance (int): The maximum depth for expanding the graph from
            the retrieved nodes. Defaults to 0 (no expansion).
        limit (Optional[int]): The maximum number of records to return in the
            final output of a query.
    """

    def __init__(
        self,
        index: str,
        embedder: Embedder,
        top_k: int,
        distance: int = 0,
        limit: int | None = None,
    ) -> None:
        self._index: str = index
        self._embedder: Embedder = embedder
        self._info: dict[str, Serializable] | None = None
        self._top_k: int = top_k
        self._distance: int = distance
        self._limit: int | None = limit

    @override
    def info(self) -> dict[str, Serializable] | None:
        return self._info

    @override
    def chat(self, chat: Chat) -> str:
        self._info = {"name": self.__class__.__name__}

        start: float = time.perf_counter()

        embed: Embedding = self._embedder.embeds(
            inputs=[
                "\n\n".join(
                    f"Role: {m['role']}\nMessage: {m['content']}" for m in chat
                ),
            ]
        )[0]

        self._info["embedder"] = unwrap_or(
            value=self._embedder.info(),
            default=dict(),
        )

        query: str = f"""\
CALL db.index.vector.queryNodes('{self._index}', {self._top_k}, {embed})
YIELD node
MATCH p = (node)-[*0..{self._distance}]-(neighbor)
RETURN p\
"""
        if self._limit is not None:
            query += f"\nLIMIT {self._limit}"

        end: float = time.perf_counter()
        self._info["time"] = (end - start) * 1000

        return query
