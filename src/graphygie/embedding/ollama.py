"""
This module integrates the Ollama client to generate vector embeddings.
"""

from typing import Any, override
from ollama import Client, EmbedResponse
from util import Serializable
from .embedding import Embedding
from .embedder import Embedder

import time


class Ollama(Embedder):
    """
    Interface for Ollama embedding models.

    Args:
        model (str): The name of the Ollama model to use (e.g., 'mxbai-embed-large').
        host (Optional[str]): The URL of the Ollama server. Defaults to localhost.
        model_params (Optional[dict[str, Any]]): Additional parameters passed
            to the Ollama embedding call (e.g., temperature, num_ctx).
        **kwargs: Additional arguments used to initialize the Ollama Client.
    """

    def __init__(
        self,
        model: str,
        host: str | None = None,
        model_params: dict[str, Any] | None = None,  # pyright: ignore[reportExplicitAny]
        **kwargs: Any,  # pyright: ignore[reportAny, reportExplicitAny]
    ) -> None:
        self._client: Client = Client(host, **kwargs)  # pyright: ignore[reportAny]
        self._model: str = model
        self._model_params: dict[str, Any] | None = model_params  # pyright: ignore[reportExplicitAny]
        self._info: dict[str, Serializable] | None = None

    @override
    def info(self) -> dict[str, Serializable] | None:
        return self._info

    @override
    def embeds(self, inputs: list[str]) -> list[Embedding]:
        """
        Generates embeddings for the provided text inputs using Ollama.

        Args:
            inputs (List[str]): Strings to be vectorized.

        Returns:
            List[Embedding]: A list of results containing the vectors.
        """
        start: float = time.perf_counter()

        response: EmbedResponse = self._client.embed(
            model=self._model,
            input=inputs,
            **(self._model_params or {}),  # pyright: ignore[reportAny]
        )

        end: float = time.perf_counter()

        self._info = {
            "name": self.__class__.__name__,
            "time": (end - start) * 1000,
        }

        return [list(embeds) for embeds in response.embeddings]
