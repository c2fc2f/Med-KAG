import time
from typing import Any, Tuple, cast
from dotenv import load_dotenv
from benchmark.generation.basic_generator import BasicGeneratorExtra
from benchmark.util import system_prompt, user_prompt
from benchmark.retrieval import GraphExtra
from benchmark.retrieval.database import Neo4jExtra
from graphygie.llm import LLM, OpenAI, Message
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

OPENROUTER_URI = unwrap(os.getenv("OPENROUTER_URI"))
OPENROUTER_TOKEN = unwrap(os.getenv("OPENROUTER_TOKEN"))

CURRENT_DIR: str = os.path.dirname(os.path.abspath(__file__))


def benchmark(
    base: str, generator: LLM, question: str, choices: dict[str, str]
) -> str | Tuple[str, dict[str, int]]:
    result: str = generator.chat(
        chat=[
            Message(
                role="user",
                content=user_prompt(
                    base,
                    intent="Answer to a multiple-choice question",
                    request=question,
                    choices=choices,
                ),
            )
        ]
    )

    if isinstance(generator, BasicGeneratorExtra):
        return (result, unwrap(generator.info))
    return result


def base_grahygie() -> tuple[GraphExtra, LLM]:
    database: Database = Neo4jExtra(
        uri=NEO4J_URI,
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD,
        database=NEO4J_DATABASE,
    )

    retrieval_llm: LLM = OpenAI(
        host=OPENROUTER_URI,
        api_key=OPENROUTER_TOKEN,
        model="qwen/qwen3-235b-a22b:free",
        model_params={"temperature": 0},
        chat=[
            Message(
                role="system",
                content=read_to_string(
                    os.path.join(CURRENT_DIR, "resources/prompt/retrieval_system.md")
                ),
            )
        ],
        cleaner=compose(strip_code_fences, strip_after_double_newline),
        timeout=None,
    )

    retrieval: GraphExtra = GraphExtra(llm=retrieval_llm, database=database)

    generator_llm: LLM = OpenAI(
        host=OPENROUTER_URI,
        api_key=OPENROUTER_TOKEN,
        model="qwen/qwen3-235b-a22b:free",
        model_params={"temperature": 0},
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
                            CURRENT_DIR, "resources/prompt/generator_system_native.md"
                        )
                    ),
                    choices=choices,
                ),
            )
        ],
        maker=generator_system_prompt,
    )


def native(choices: list[str]) -> LLM:
    return OpenAI(
        host=OPENROUTER_URI,
        api_key=OPENROUTER_TOKEN,
        model="qwen/qwen3-235b-a22b:free",
        model_params={"temperature": 0},
        chat=[
            Message(
                role="system",
                content=system_prompt(
                    base=read_to_string(
                        os.path.join(
                            CURRENT_DIR, "resources/prompt/generator_system_native.md"
                        )
                    ),
                    choices=choices,
                ),
            )
        ],
    )


def main() -> None:
    bench: Any = json.load(open(os.path.join(CURRENT_DIR, "benchmark.json")))
    base: str = read_to_string(os.path.join(CURRENT_DIR, "resources/prompt/user.md"))

    (retrieval, generator_llm) = base_grahygie()

    os.makedirs(os.path.join(CURRENT_DIR, "results"), exist_ok=True)

    for dataset, val in bench.items():
        print("Start dataset:", dataset)
        os.makedirs(os.path.join(CURRENT_DIR, f"results/{dataset}"), exist_ok=True)
        for question, val in val.items():
            print("Start question:", question)
            n = native(val["options"].keys())
            g = graphygie(retrieval, generator_llm, val["options"].keys())

            with open(
                os.path.join(CURRENT_DIR, f"results/{dataset}/native_{question}.json"),
                "w",
                encoding="utf-8",
            ) as f:
                while True:
                    try:
                        data = {
                            "response": cast(
                                str,
                                benchmark(base, n, val["question"], val["options"]),
                            )
                        }
                        break
                    except Exception as e:
                        print(str(e))
                        print("Retry")
                        time.sleep(30)
                json.dump(data, f, indent=4, ensure_ascii=False)

            with open(
                os.path.join(CURRENT_DIR, f"results/{dataset}/rag_{question}.json"),
                "w",
                encoding="utf-8",
            ) as f:
                while True:
                    try:
                        (response, data) = cast(
                            Tuple[str, dict[str, int | str]],
                            benchmark(base, g, val["question"], val["options"]),
                        )
                        data["response"] = response
                        break
                    except Exception as e:
                        print(str(e))
                        print("Retry")
                        time.sleep(30)
                json.dump(data, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    main()
