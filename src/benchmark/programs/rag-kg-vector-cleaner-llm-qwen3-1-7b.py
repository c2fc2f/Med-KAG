from typing import override
from dotenv import load_dotenv
from benchmark.util import benchmark, system_prompt, parse_k_argument
from graphygie.embedding.embedder import Embedder
from graphygie.embedding.ollama import Ollama as OllamaEmbdder
from graphygie.generation.basic_generator import BasicGenerator
from graphygie.info.info import Info
from graphygie.llm import Ollama
from graphygie.chat import Chattable, Message
from graphygie.retrieval import Graph
from graphygie.retrieval.database import Database
from graphygie.retrieval.database.neo4j import Neo4j
from graphygie.retrieval.database.neo4j.converter import Triplet
from graphygie.retrieval.database.neo4j.cypher.vector import Vector2Cypher
from util import (
    Serializable,
    read_to_string,
    unwrap,
    generator_system_prompt,
)

import json
import os

_ = load_dotenv()

NEO4J_URI: str = unwrap(value=os.getenv("NEO4J_URI"))
NEO4J_USERNAME: str = unwrap(value=os.getenv("NEO4J_USERNAME"))
NEO4J_PASSWORD: str = unwrap(value=os.getenv("NEO4J_PASSWORD"))
NEO4J_DATABASE: str = unwrap(value=os.getenv("NEO4J_DATABASE"))

OLLAMA_URI: str = unwrap(value=os.getenv("OLLAMA_URI"))

CURRENT_DIR: str = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR: str = os.path.join(CURRENT_DIR, "../results")
BENCHMARK_FILE: str = os.path.join(CURRENT_DIR, "../benchmark.json")
PROMPT_USER: str = os.path.join(CURRENT_DIR, "../resources/prompt/user.md")
PROMPT_SYSTEM: str = os.path.join(
    CURRENT_DIR,
    "../resources/prompt/generator_system_rag_kg-vector-cleaner-llm.md",
)
PROMPT_CLEANER: str = os.path.join(
    CURRENT_DIR,
    "../resources/prompt/cleaner-llm.md",
)


class CleanerLLM(Info):
    def __init__(self, choices_keys: list[str]) -> None:
        self._cleaner: Chattable = Ollama(
            host=OLLAMA_URI,
            model="qwen3:1.7b",
            chat=[
                Message(
                    role="system",
                    content=system_prompt(
                        base=read_to_string(path=PROMPT_CLEANER),
                        choices_keys=choices_keys,
                    ),
                )
            ],
            model_params={
                "options": {
                    "temperature": 0.0,
                },
            },
        )
        self._info: dict[str, Serializable] | None = None

    @override
    def info(self) -> dict[str, Serializable] | None:
        return self._info

    def __call__(self, s: str) -> str:
        if len(s) == 0:
            return s
        res: str = self._cleaner.chat(
            chat=[
                Message(
                    role="user",
                    content=s,
                ),
            ]
        )

        self._info = self._cleaner.info()

        return res


def base_grahygie(choices_keys: list[str]) -> tuple[Graph, Chattable]:
    database: Database = Neo4j(
        uri=NEO4J_URI,
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD,
        database=NEO4J_DATABASE,
        converter=Triplet(),
        excluded_properties=[
            "embedding",
        ],
    )

    embedder: Embedder = OllamaEmbdder(
        host=OLLAMA_URI,
        model="embeddinggemma:latest",
    )

    retrieval_vector: Chattable = Vector2Cypher(
        index="CUI_EMBEDDINGS",
        embedder=embedder,
        top_k=2,
        distance=1,
    )

    retrieval: Graph = Graph(query_gen=retrieval_vector, database=database)

    generator_llm: Chattable = Ollama(
        host=OLLAMA_URI,
        model="qwen3:1.7b",
        model_params={
            "options": {
                "temperature": 0.0,
                "num_ctx": 8192,
            },
        },
        cleaner=CleanerLLM(
            choices_keys=choices_keys,
        ),
    )

    return (retrieval, generator_llm)


def graphygie(choices_keys: list[str]) -> BasicGenerator:
    (retrieval, generator_llm) = base_grahygie(
        choices_keys=choices_keys,
    )

    return BasicGenerator(
        retriever=retrieval,
        generator=generator_llm,
        chat=[
            Message(
                role="system",
                content=read_to_string(path=PROMPT_SYSTEM),
            )
        ],
        maker=generator_system_prompt,
    )


def main() -> None:
    os.makedirs(name=RESULTS_DIR, exist_ok=True)

    benchmark(
        name="rag-kg-vector-cleaner-llm-qwen3-1.7b",
        results_dir=RESULTS_DIR,
        bench=json.load(
            fp=open(
                file=BENCHMARK_FILE,
            ),
        ),  # pyright: ignore[reportAny]
        base=read_to_string(path=PROMPT_USER),
        model=lambda choices: graphygie(
            choices_keys=choices,
        ),
        start=parse_k_argument(k=1),
        end=parse_k_argument(k=2),
    )


if __name__ == "__main__":
    main()
