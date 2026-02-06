"""
This module integrates the Ollama client to generate vector embeddings.
"""

from typing import Any, List, Optional
from ollama import Client, EmbedResponse
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
        host: Optional[str] = None,
        model_params: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        self._client: Client = Client(host, **kwargs)
        self._model: str = model
        self._model_params: Optional[dict[str, Any]] = model_params
        self._info: Optional[dict[str, Any]] = None

    def info(self) -> Optional[dict[str, Any]]:
        return self._info

    def embeds(self, inputs: List[str] = list()) -> List[Embedding]:
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
            **(self._model_params or {}),
        )

        end: float = time.perf_counter()

        self._info = {
            "name": self.__class__.__name__,
            "time": (end - start) * 1000,
        }

        return [list(embeds) for embeds in response.embeddings]
