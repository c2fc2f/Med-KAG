from typing import Any
from dotenv import load_dotenv
from benchmark.util import benchmark, system_prompt
from graphygie.llm import LLM, OpenAI, Message
from util import (
    read_to_string,
    unwrap,
)

import json
import os

load_dotenv()

OPENROUTER_URI = unwrap(os.getenv("OPENROUTER_URI"))
OPENROUTER_TOKEN = unwrap(os.getenv("OPENROUTER_TOKEN"))

CURRENT_DIR: str = os.path.dirname(os.path.abspath(__file__))


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
    results_dir = os.path.join(CURRENT_DIR, "results")

    os.makedirs(results_dir, exist_ok=True)

    benchmark("native-qwen3-235b", results_dir, bench, base, native)


if __name__ == "__main__":
    main()
