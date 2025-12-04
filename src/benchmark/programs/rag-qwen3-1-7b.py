from typing import Any
from dotenv import load_dotenv
from benchmark.generation.basic_generator import BasicGeneratorExtra
from benchmark.util import benchmark, system_prompt, parse_first_argument
from benchmark.retrieval import GraphExtra
from benchmark.retrieval.database import Neo4jExtra
from graphygie.llm import LLM, Ollama, Message
from graphygie.retrieval.database import Database
from util import (
    read_to_string,
    unwrap,
    strip_code_fences,
    strip_after_double_newline,
    generator_system_prompt,
    compose,
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


def base_grahygie() -> tuple[GraphExtra, LLM]:
    database: Database = Neo4jExtra(
        uri=NEO4J_URI,
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD,
        database=NEO4J_DATABASE,
    )

    retrieval_llm: LLM = Ollama(
        host=OLLAMA_URI,
        model="qwen3:1.7b",
        chat=[
            Message(
                role="system",
                content=read_to_string(
                    os.path.join(CURRENT_DIR, "../resources/prompt/retrieval_system.md")
                ),
            )
        ],
        cleaner=compose(strip_code_fences, strip_after_double_newline),
        timeout=None,
    )

    retrieval: GraphExtra = GraphExtra(llm=retrieval_llm, database=database)

    generator_llm: LLM = Ollama(
        host=OLLAMA_URI,
        model="qwen3:1.7b",
        cleaner=lambda s: s[0],
    )

    return (retrieval, generator_llm)


def graphygie(
    retrieval: GraphExtra, generator_llm: LLM, choices: list[str]
) -> BasicGeneratorExtra:
    return BasicGeneratorExtra(
        retriever=retrieval,
        generator=generator_llm,
        chat=[
            Message(
                role="system",
                content=system_prompt(
                    base=read_to_string(
                        os.path.join(
                            CURRENT_DIR,
                            "../resources/prompt/generator_system_native.md",
                        )
                    ),
                    choices=choices,
                ),
            )
        ],
        maker=generator_system_prompt,
    )


def main() -> None:
    bench: Any = json.load(open(os.path.join(CURRENT_DIR, "../benchmark.json")))
    base: str = read_to_string(os.path.join(CURRENT_DIR, "../resources/prompt/user.md"))
    results_dir = os.path.join(CURRENT_DIR, "../results")

    os.makedirs(results_dir, exist_ok=True)

    (retrieval, generator_llm) = base_grahygie()
    benchmark(
        "rag-qwen3-1-7b",
        results_dir,
        bench,
        base,
        lambda choices: graphygie(retrieval, generator_llm, choices),
        start=parse_first_argument(),
    )


if __name__ == "__main__":
    main()
