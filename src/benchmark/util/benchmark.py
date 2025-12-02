import time
from typing import Any, Callable, Tuple, cast
from benchmark.util import user_prompt
from benchmark.llm import LLMExtra
from graphygie.llm import LLM, Message
from util import (
    unwrap,
)

import json
import os


def run(
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

    if isinstance(generator, LLMExtra):
        return (result, unwrap(generator.info()))
    return result


def benchmark(
    name: str,
    results_dir: str,
    bench: dict[str, Any],
    base: str,
    model: Callable[[list[str]], LLM],
) -> None:
    for dataset, val in bench.items():
        print("Start dataset:", dataset)
        os.makedirs(f"{results_dir}/{dataset}", exist_ok=True)
        for question, val in val.items():
            print("Start question:", question)
            llm = model(val["options"].keys())

            with open(
                f"{results_dir}/{dataset}/{name}_{question}.json",
                "w",
                encoding="utf-8",
            ) as f:
                while True:
                    try:
                        data = {
                            "response": cast(
                                str,
                                run(base, llm, val["question"], val["options"]),
                            )
                        }
                        break
                    except Exception as e:
                        print(str(e))
                        print("Retry")
                        time.sleep(30)
                json.dump(data, f, indent=4, ensure_ascii=False)
