from pathlib import Path
from statistics import mean, median, quantiles, stdev
from typing import Any, List, Mapping, Tuple, Union
from dataclasses import dataclass
from util.serializable import Atome, Serializable

import json
import os
import re

CURRENT_DIR: str = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR: str = os.path.join(CURRENT_DIR, "../results")
BENCHMARK_FILE: str = os.path.join(CURRENT_DIR, "../benchmark.json")
EMOJI: list[str] = [
    "🔴",
    "🟠",
    "🟡",
    "🟢",
    "🔵",
    "🟣",
    "🟤",
    "⚫",
    "⚪",
    "🟥",
    "🟧",
    "🟨",
    "🟩",
    "🟦",
    "🟪",
    "🟫",
    "⬛",
    "⬜",
    "❤️",
    "🧡",
    "💛",
    "💚",
    "💙",
    "💜",
    "🤎",
    "🖤",
    "🤍",
]


@dataclass()
class Stats:
    method: str
    correct: int
    total: int

    extra: dict[str, list[Atome]]

    def __init__(self, method: str) -> None:
        self.method = method
        self.correct = 0
        self.total = 0

        self.extra = dict()

    def add(self, total: int, correct: int, extra: Mapping[str, Serializable]) -> None:
        """
        Updates aggregate counts and flattens nested dictionaries into JSON
        paths.

        Args:
            total: Increment for the total count.
            correct: Increment for the correct count.
            extra: A nested dictionary to be flattened. Keys are joined by
                dots (e.g., {'a': {'b': 1}} becomes 'a.b'). Leaf values are
                appended to lists in self.extra.
        """

        def flatten_and_store(
            data: Mapping[str, Serializable], prefix: str = ""
        ) -> None:
            """Recursively flattens a dictionary into dot-notated paths."""
            for key, value in data.items():
                path = f"{prefix}.{key}" if prefix else key

                if isinstance(value, dict):
                    flatten_and_store(value, path)
                else:
                    if path not in self.extra:
                        self.extra[path] = []
                    self.extra[path].append(value)

        self.total += total
        self.correct += correct
        flatten_and_store(extra)


def load_benchmark(benchmark_path: str) -> Serializable:
    """Load the benchmark.json file"""

    with open(benchmark_path, "r", encoding="utf-8") as f:
        return json.load(f)


def display_one_stats(
    info: Stats,
    ind: int,
    key_len: int,
    total_len: int,
) -> None:
    """Display one statistic"""

    accuracy: float = (info.correct / info.total * 100) if info.total > 0 else 0
    print(f"{EMOJI[ind]} {info.method.upper().replace('-', ' ')}")
    print(f"  ✅ Correct answers: {info.correct:>{total_len}}/{info.total}")
    print(f"  📈 Accuracy rate: {accuracy:.2f}%")
    print()
    print(f"  📉 {info.method.upper().replace('-', ' ')} METRICS")

    print(
        " " * 2,
        "|",
        f"{'key':^{key_len}}",
        "|",
        f"{'Average':^9}",
        "|",
        f"{'Median':^9}",
        "|",
        f"{'Std Dev':^9}",
        "|",
        f"{'P90':^9}",
        "|",
        f"{'Non-empty':^{total_len * 2 + 5 + 5}}",
        "|",
    )

    print(
        " " * 2,
        "|",
        "-" * key_len,
        "|",
        "-" * 9,
        "|",
        "-" * 9,
        "|",
        "-" * 9,
        "|",
        "-" * 9,
        "|",
        "-" * (total_len * 2 + 5 + 5),
        "|",
    )

    for key, values in info.extra.items():
        numeric_values: List[Union[int, float]] = [
            int(v) if isinstance(v, bool) else (v if v is not None else 0)
            for v in values
            if isinstance(v, (int, float, bool)) or v is None
        ]

        if not numeric_values:
            continue

        with_sth: int = sum(1 for n in numeric_values if n >= 1)
        total_count: int = len(numeric_values)

        avg: float = mean(numeric_values)
        med: float = median(numeric_values)
        std: float = stdev(numeric_values) if len(numeric_values) > 1 else float("nan")
        p90: float = quantiles(numeric_values, n=10)[8]
        nz_pct: float = with_sth / total_count * 100

        print(
            " " * 2,
            "|",
            f"{key:<{key_len}}",
            "|",
            f"{avg:9.2f}",
            "|",
            f"{med:9.2f}",
            "|",
            f"{std:9.2f}",
            "|",
            f"{p90:9.2f}",
            "|",
            f"{with_sth:>{total_len}}/{total_count:>{total_len}} ({nz_pct:5.1f}%)",
            "|",
        )

    print()


def display_stats(
    stats: dict[str, dict[str, Stats]], methods_ind: dict[str, int]
) -> None:
    """Display all the statistics"""

    print("━" * 100)
    print("📊 ANALYSIS RESULTS")
    print("━" * 100)
    print()

    keyl = 0
    totallm: Mapping[str, int] = dict()
    for dataset, dstats in stats.items():
        for mstat in dstats.values():
            for key in mstat.extra.keys():
                keyl = max(keyl, len(key))
            totallm[dataset] = max(
                totallm.get(dataset, 0),
                len(str(mstat.total)),
            )

    stats_methods: dict[str, list[Stats]] = dict()

    for dataset, infos in sorted(stats.items(), key=lambda e: e[0]):
        print("━" * 90)
        print(f"ANALYSIS RESULTS FOR {dataset}")
        print("━" * 90)
        print()

        for method, info in sorted(infos.items(), key=lambda e: e[0]):
            if method not in stats_methods.keys():
                stats_methods[method] = []
            stats_methods[method].append(info)

            display_one_stats(
                info=info,
                ind=methods_ind[method],
                key_len=keyl,
                total_len=totallm[dataset],
            )

        print("━" * 90)
        print()

    print("━" * 90)
    print("ANALYSIS RESULTS TOTAL")
    print("━" * 90)
    print()

    totall: int = 0

    rtotal: List[Tuple[Stats, int]] = list()

    for method, infos in sorted(stats_methods.items(), key=lambda e: e[0]):
        s: Stats = Stats(method)

        for info in infos:
            s.total += info.total
            s.correct += info.correct

            # Assume consistent schema: all 'info' objects for a specific
            # method provide the same set of keys in 'extra'.
            for key, values in info.extra.items():
                if key not in s.extra:
                    s.extra[key] = list(values)
                else:
                    s.extra[key].extend(values)

        totall = max(totall, len(str(s.total)))
        rtotal.append((s, methods_ind[method]))

    for s, method_ind in rtotal:
        display_one_stats(
            info=s,
            ind=method_ind,
            key_len=keyl,
            total_len=totall,
        )

    print("━" * 100)


def analyze_results(results_dir: str, benchmark_path: str) -> None:
    """Analyze all results"""

    benchmark: Any = load_benchmark(benchmark_path)

    stats: dict[str, dict[str, Stats]] = dict()
    methods: list[str] = list()

    results_path = Path(results_dir)

    for dataset_dir in results_path.iterdir():
        if not dataset_dir.is_dir():
            continue

        dataset_name: str = dataset_dir.name

        if dataset_name not in benchmark:
            print(f"⚠️  Dataset '{dataset_name}' not found in benchmark.json")
            continue

        stats[dataset_name] = dict()

        for result_file in dataset_dir.glob("*.json"):
            if result_file.stat().st_size == 0:
                continue

            filename: str = result_file.name

            pattern = r"^(.+?)_(.+)\.json$"
            match = re.match(pattern, filename)

            if match:
                result_type: str = match.group(1)
                if result_type not in methods:
                    methods.append(result_type)
                question_name: str = match.group(2)
            else:
                continue

            if question_name not in benchmark[dataset_name]:
                print(
                    f"⚠️  Question '{question_name}' not found in "
                    f"benchmark[{dataset_name}]"
                )
                continue

            with open(result_file, "r", encoding="utf-8") as f:
                result: Any = json.load(f)

            correct: str = benchmark[dataset_name][question_name]["answer"]
            model_res: str = result.get("response")
            model_stats: dict[str, Serializable] = result.get("stats")

            if result_type not in stats[dataset_name].keys():
                stats[dataset_name][result_type] = Stats(result_type)
            stats[dataset_name][result_type].add(
                1, 1 if model_res == correct else 0, model_stats
            )

    display_stats(stats, methods_ind={v: k for k, v in enumerate(sorted(methods))})


def main() -> None:
    if not os.path.exists(RESULTS_DIR):
        print(f"❌ Error: Directory '{RESULTS_DIR}' does not exist")
        exit(1)

    if not os.path.exists(BENCHMARK_FILE):
        print(f"❌ Error: File '{BENCHMARK_FILE}' does not exist")
        exit(1)

    analyze_results(RESULTS_DIR, BENCHMARK_FILE)


if __name__ == "__main__":
    main()
