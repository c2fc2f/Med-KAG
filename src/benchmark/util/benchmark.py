import logging
import time
from typing import Any, Callable, Dict, Optional, Tuple
from itertools import dropwhile
from benchmark.util import user_prompt
from graphygie.llm import LLM, Message
from datetime import datetime
from util import unwrap_or, Serializable

import json
import os
import sys


def run(
    base: str, generator: LLM, question: str, choices: dict[str, str]
) -> Dict[str, Serializable]:
    data: Dict[str, Serializable] = dict()

    data["response"] = generator.chat(
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

    data["stats"] = unwrap_or(generator.info(), dict())

    return data


def benchmark(
    name: str,
    results_dir: str,
    bench: dict[str, Any],
    base: str,
    model: Callable[[list[str]], LLM],
    start: Optional[Tuple[str, str]] = None,
    end: Optional[Tuple[str, str]] = None,
) -> None:
    logger: logging.Logger = logging.getLogger(__name__)
    logger.info(f"start: {start} - end: {end}")

    iterator = enumerate(bench.items())
    dcount = len(bench)
    if start is not None:
        iterator = dropwhile(lambda item: item[1][0] != start[0], iterator)

    for didx, (dataset, val) in iterator:
        print(
            f"Start of the {dataset} ({didx + 1}/{dcount}) dataset at {datetime.now()}"
        )
        os.makedirs(f"{results_dir}/{dataset}", exist_ok=True)

        sub_iter = enumerate(val.items())
        qcount = len(val)

        if start is not None and dataset == start[0]:
            sub_iter = dropwhile(lambda item: item[1][0] != start[1], sub_iter)

        for qidx, (question, val) in sub_iter:
            print(
                f"Start of the {question} ({qidx + 1}/{qcount}) question at {datetime.now()}"
            )
            llm = model(val["options"].keys())

            with open(
                f"{results_dir}/{dataset}/{name}_{question}.json",
                "w",
                encoding="utf-8",
            ) as f:
                while True:
                    try:
                        data = run(base, llm, val["question"], val["options"])
                        break
                    except Exception as e:
                        print(str(e))
                        print("Retry")
                        time.sleep(30)

                logger.info(data)
                json.dump(data, f, indent=4, ensure_ascii=False)

            if end is not None and dataset == end[0] and question == end[1]:
                return


def parse_k_argument(k: int) -> Optional[Tuple[str, str]]:
    """
    Parse the k-nth command-line argument and split by '/'
    Returns a tuple of two strings if valid, None otherwise
    """
    if len(sys.argv) <= k:
        return None

    first_arg = sys.argv[k]
    parts = first_arg.split("/")

    if len(parts) == 2:
        return (parts[0], parts[1])

    return None
