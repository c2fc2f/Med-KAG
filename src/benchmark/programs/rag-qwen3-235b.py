from typing import Any
from dotenv import load_dotenv
from benchmark.util import benchmark, system_prompt, parse_k_argument
from graphygie.generation.basic_generator import BasicGenerator
from graphygie.llm import LLM, OpenAI, Message
from graphygie.retrieval import GraphLLM
from graphygie.retrieval.database import Database
from graphygie.retrieval.database.neo4j import Neo4j
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

OPENAI_URI = unwrap(os.getenv("OPENAI_URI"))
OPENAI_TOKEN = unwrap(os.getenv("OPENAI_TOKEN"))

CURRENT_DIR: str = os.path.dirname(os.path.abspath(__file__))


def base_grahygie() -> tuple[GraphLLM, LLM]:
    database: Database = Neo4j(
        uri=NEO4J_URI,
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD,
        database=NEO4J_DATABASE,
        excluded_properties=["embedding"],
    )

    retrieval_llm: LLM = OpenAI(
        host=OPENAI_URI,
        api_key=OPENAI_TOKEN,
        model="qwen/qwen3-235b-a22b:free",
        model_params={"temperature": 0},
        chat=[
            Message(
                role="system",
                content=read_to_string(
                    os.path.join(CURRENT_DIR, "../resources/prompt/retrieval_system.md")
                ),
            )
        ],
        cleaner=compose(strip_code_fences, strip_after_double_newline),
    )

    retrieval: GraphLLM = GraphLLM(llm=retrieval_llm, database=database)

    generator_llm: LLM = OpenAI(
        host=OPENAI_URI,
        api_key=OPENAI_TOKEN,
        model="qwen/qwen3-235b-a22b:free",
        model_params={"temperature": 0},
        cleaner=lambda s: s[0] if len(s) > 0 else s,
    )

    return (retrieval, generator_llm)


def graphygie(
    retrieval: GraphLLM, generator_llm: LLM, choices: list[str]
) -> BasicGenerator:
    return BasicGenerator(
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
        "rag-qwen3-235b",
        results_dir,
        bench,
        base,
        lambda choices: graphygie(retrieval, generator_llm, choices),
        start=parse_k_argument(1),
        end=parse_k_argument(2),
    )


if __name__ == "__main__":
    main()
