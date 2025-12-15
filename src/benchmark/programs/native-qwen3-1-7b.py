from typing import Any
from dotenv import load_dotenv
from benchmark.util import benchmark, system_prompt, parse_k_argument
from graphygie.llm import LLM, Ollama, Message
from util import (
    read_to_string,
    unwrap,
)

import json
import os

load_dotenv()

OLLAMA_URI = unwrap(os.getenv("OLLAMA_URI"))

CURRENT_DIR: str = os.path.dirname(os.path.abspath(__file__))


def native(choices: list[str]) -> LLM:
    return Ollama(
        host=OLLAMA_URI,
        model="qwen3:1.7b",
        model_params={"options": {"temperature": 0.0}},
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
        cleaner=lambda s: s[0] if len(s) > 0 else s,
    )


def main() -> None:
    bench: Any = json.load(open(os.path.join(CURRENT_DIR, "../benchmark.json")))
    base: str = read_to_string(os.path.join(CURRENT_DIR, "../resources/prompt/user.md"))
    results_dir = os.path.join(CURRENT_DIR, "../results")

    os.makedirs(results_dir, exist_ok=True)

    benchmark(
        "native-qwen3-1.7b",
        results_dir,
        bench,
        base,
        native,
        start=parse_k_argument(1),
        end=parse_k_argument(2),
    )


if __name__ == "__main__":
    main()
