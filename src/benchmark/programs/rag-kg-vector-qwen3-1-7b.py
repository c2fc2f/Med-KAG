from dotenv import load_dotenv
from benchmark.util import benchmark, system_prompt, parse_k_argument
from graphygie.embedding.embedder import Embedder
from graphygie.embedding.ollama import Ollama as OllamaEmbdder
from graphygie.generation.basic_generator import BasicGenerator
from graphygie.llm import Ollama
from graphygie.chat import Chattable, Message
from graphygie.retrieval import Graph
from graphygie.retrieval.database import Database
from graphygie.retrieval.database.neo4j import Neo4j
from graphygie.retrieval.database.neo4j.cypher.vector import Vector2Cypher
from util import (
    read_to_string,
    unwrap,
    generator_system_prompt,
)

import json
import os

load_dotenv()

NEO4J_URI = unwrap(os.getenv("NEO4J_URI"))
NEO4J_USERNAME = unwrap(os.getenv("NEO4J_USERNAME"))
NEO4J_PASSWORD = unwrap(os.getenv("NEO4J_PASSWORD"))
NEO4J_DATABASE = unwrap(os.getenv("NEO4J_DATABASE"))

OLLAMA_URI = unwrap(os.getenv("OLLAMA_URI"))

CURRENT_DIR: str = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR: str = os.path.join(CURRENT_DIR, "../results")
BENCHMARK_FILE: str = os.path.join(CURRENT_DIR, "../benchmark.json")
PROMPT_USER: str = os.path.join(CURRENT_DIR, "../resources/prompt/user.md")
PROMPT_SYSTEM: str = os.path.join(
    CURRENT_DIR, "../resources/prompt/generator_system_rag_kg-vector.md"
)


def base_grahygie() -> tuple[Graph, Chattable]:
    database: Database = Neo4j(
        uri=NEO4J_URI,
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD,
        database=NEO4J_DATABASE,
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
            },
        },
        cleaner=lambda s: s[0] if len(s) > 0 else s,
    )

    return (retrieval, generator_llm)


def graphygie(
    retrieval: Graph, generator_llm: Chattable, choices_keys: list[str]
) -> BasicGenerator:
    return BasicGenerator(
        retriever=retrieval,
        generator=generator_llm,
        chat=[
            Message(
                role="system",
                content=system_prompt(
                    base=read_to_string(PROMPT_SYSTEM),
                    choices_keys=choices_keys,
                ),
            )
        ],
        maker=generator_system_prompt,
    )


def main() -> None:
    os.makedirs(RESULTS_DIR, exist_ok=True)

    (retrieval, generator_llm) = base_grahygie()
    benchmark(
        "rag-kg-vector-qwen3-1.7b",
        RESULTS_DIR,
        json.load(open(BENCHMARK_FILE)),
        read_to_string(PROMPT_USER),
        lambda choices: graphygie(retrieval, generator_llm, choices),
        start=parse_k_argument(1),
        end=parse_k_argument(2),
    )


if __name__ == "__main__":
    main()
