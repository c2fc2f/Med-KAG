from dotenv import load_dotenv
from benchmark.util import benchmark, system_prompt, parse_k_argument
from graphygie.llm import Ollama
from graphygie.chat import Chattable, Message
from util import (
    read_to_string,
    unwrap,
)

import json
import os

_ = load_dotenv()

OLLAMA_URI: str = unwrap(value=os.getenv("OLLAMA_URI"))

CURRENT_DIR: str = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR: str = os.path.join(CURRENT_DIR, "../results")
BENCHMARK_FILE: str = os.path.join(CURRENT_DIR, "../benchmark.json")
PROMPT_USER: str = os.path.join(CURRENT_DIR, "../resources/prompt/user.md")
PROMPT_SYSTEM: str = os.path.join(
    CURRENT_DIR, "../resources/prompt/generator_system_native.md"
)


def native(choices_keys: list[str]) -> Chattable:
    return Ollama(
        host=OLLAMA_URI,
        model="qwen3:4b",
        model_params={
            "options": {
                "temperature": 0.0,
            },
        },
        chat=[
            Message(
                role="system",
                content=system_prompt(
                    base=read_to_string(path=PROMPT_SYSTEM),
                    choices_keys=choices_keys,
                ),
            )
        ],
        cleaner=lambda s: s[0] if len(s) > 0 else s,
    )


def main() -> None:
    os.makedirs(name=RESULTS_DIR, exist_ok=True)

    benchmark(
        name="native-qwen3-4b",
        results_dir=RESULTS_DIR,
        bench=json.load(
            fp=open(
                file=BENCHMARK_FILE,
            ),
        ),
        base=read_to_string(path=PROMPT_USER),
        model=native,
        start=parse_k_argument(k=1),
        end=parse_k_argument(k=2),
    )


if __name__ == "__main__":
    main()
