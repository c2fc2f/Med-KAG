from dotenv import load_dotenv
from benchmark.util import benchmark, system_prompt, parse_k_argument
from graphygie.llm import OpenAI
from graphygie.chat import Chattable, Message
from util import (
    read_to_string,
    unwrap,
)

import json
import os

load_dotenv()

OPENAI_URI = unwrap(os.getenv("OPENAI_URI"))
OPENAI_TOKEN = unwrap(os.getenv("OPENAI_TOKEN"))

CURRENT_DIR: str = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR: str = os.path.join(CURRENT_DIR, "../results")
BENCHMARK_FILE: str = os.path.join(CURRENT_DIR, "../benchmark.json")
PROMPT_USER: str = os.path.join(CURRENT_DIR, "../resources/prompt/user.md")
PROMPT_SYSTEM: str = os.path.join(
    CURRENT_DIR, "../resources/prompt/generator_system_native.md"
)


def native(choices_keys: list[str]) -> Chattable:
    return OpenAI(
        host=OPENAI_URI,
        api_key=OPENAI_TOKEN,
        model="qwen/qwen3-235b-a22b:free",
        model_params={"temperature": 0},
        chat=[
            Message(
                role="system",
                content=system_prompt(
                    base=read_to_string(PROMPT_SYSTEM),
                    choices_keys=choices_keys,
                ),
            )
        ],
        cleaner=lambda s: s[0] if len(s) > 0 else s,
    )


def main() -> None:
    os.makedirs(RESULTS_DIR, exist_ok=True)

    benchmark(
        "native-qwen3-235b",
        RESULTS_DIR,
        json.load(open(BENCHMARK_FILE)),
        read_to_string(PROMPT_USER),
        native,
        start=parse_k_argument(1),
        end=parse_k_argument(2),
    )


if __name__ == "__main__":
    main()
