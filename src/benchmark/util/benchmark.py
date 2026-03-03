from collections.abc import Iterator
from typing import Callable, TypedDict
from itertools import dropwhile
from .user_prompt import user_prompt
from graphygie.chat import Chattable, Message
from datetime import datetime
from util import unwrap_or, Serializable

import json
import os
import sys
import logging
import time


class Entry(TypedDict):
    question: str
    options: dict[str, str]
    answer: str


type Dataset = dict[str, Entry]
type Benchmark = dict[str, Dataset]


def run(
    base: str,
    generator: Chattable,
    question: str,
    choices: dict[str, str],
) -> dict[str, Serializable]:
    data: dict[str, Serializable] = dict()

    data["response"] = generator.chat(
        chat=[
            Message(
                role="user",
                content=user_prompt(
                    base,
                    request=question,
                    choices=choices,
                ),
            )
        ]
    )

    data["stats"] = unwrap_or(value=generator.info(), default=dict())

    return data


def benchmark(
    name: str,
    results_dir: str,
    bench: Benchmark,
    base: str,
    model: Callable[[list[str]], Chattable],
    start: tuple[str, str] | None = None,
    end: tuple[str, str] | None = None,
) -> None:
    logger: logging.Logger = logging.getLogger(name=__name__)
    logger.info(f"start: {start} - end: {end}")

    iterator: Iterator[tuple[int, tuple[str, Dataset]]] = enumerate(bench.items())
    dcount: int = len(bench)
    if start is not None:
        iterator = dropwhile(lambda item: item[1][0] != start[0], iterator)

    for didx, (dataset_name, dataset) in iterator:
        print(
            f"Start of the {dataset_name} ({didx + 1}/{dcount}) dataset at {datetime.now()}"
        )
        os.makedirs(name=f"{results_dir}/{dataset_name}", exist_ok=True)

        sub_iter: Iterator[tuple[int, tuple[str, Entry]]] = enumerate(dataset.items())
        qcount: int = len(dataset)

        if start is not None and dataset_name == start[0]:
            sub_iter = dropwhile(lambda item: item[1][0] != start[1], sub_iter)

        for qidx, (question_name, question) in sub_iter:
            print(
                f"Start of the {question_name} ({qidx + 1}/{qcount}) question at {datetime.now()}"
            )
            llm: Chattable = model(list(question["options"].keys()))

            with open(
                file=f"{results_dir}/{dataset_name}/{name}_{question_name}.json",
                mode="w",
                encoding="utf-8",
            ) as f:
                while True:
                    try:
                        data: dict[str, Serializable] = run(
                            base,
                            generator=llm,
                            question=question["question"],
                            choices=question["options"],
                        )
                        break
                    except Exception as e:
                        print(str(e))
                        print("Retry")
                        time.sleep(30)

                logger.info(msg=data)
                json.dump(
                    obj=data,
                    fp=f,
                    indent=4,
                    ensure_ascii=False,
                )

            if end is not None and dataset_name == end[0] and question_name == end[1]:
                return


def parse_k_argument(k: int) -> tuple[str, str] | None:
    """
    Parse the k-nth command-line argument and split by '/'
    Returns a tuple of two strings if valid, None otherwise
    """
    if len(sys.argv) <= k:
        return None

    first_arg: str = sys.argv[k]
    parts: list[str] = first_arg.split(sep="/")

    if len(parts) == 2:
        return (parts[0], parts[1])

    return None
