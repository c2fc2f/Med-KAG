import json
import os
import re
from pathlib import Path
from statistics import mean, median
from typing import Any, Union
from dataclasses import dataclass


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
class ExtraStatsGraph:
    errors: list[int]
    nodes: list[int]
    edges: list[int]

    def __add__(self, other):
        """Add two ExtraStatsGraph objects by concatenating their lists."""

        if not isinstance(other, ExtraStatsGraph):
            return NotImplemented

        return ExtraStatsGraph(
            errors=self.errors + other.errors,
            nodes=self.nodes + other.nodes,
            edges=self.edges + other.edges,
        )


ExtraStats = Union[ExtraStatsGraph]


class Stats:
    method: str
    correct: int
    total: int

    extra: None | ExtraStats

    def __init__(self, method: str) -> None:
        self.method = method
        self.correct = 0
        self.total = 0

        self.extra = None

    def add(self, total: int, correct: int) -> None:
        """Add total to the total count and correct to the correct count"""

        self.total += total
        self.correct += correct

    def add_extra(self, extra: None | ExtraStats) -> None:
        """ "Add extra statistics to the current extra statistics"""

        if extra is None:
            return
        if self.extra is None:
            self.extra = extra
        else:
            self.extra += extra


def load_benchmark(benchmark_path: str) -> Any:
    """Load the benchmark.json file"""

    with open(benchmark_path, "r", encoding="utf-8") as f:
        return json.load(f)


def display_one_stats(info: Stats, ind: int) -> None:
    """Display one statistic"""

    accuracy: float = (info.correct / info.total * 100) if info.total > 0 else 0
    print(f"{EMOJI[ind]} {info.method.upper().replace('-', ' ')}")
    print(f"  ✅ Correct answers: {info.correct}/{info.total}")
    print(f"  📈 Accuracy rate: {accuracy:.2f}%")
    print()

    match info.extra:
        case None:
            pass
        case ExtraStatsGraph(errors, nodes, edges):
            print(f"  📉 {info.method.upper().replace('-', ' ')} METRICS")
            print(
                f"     Errors     - Mean: {mean(errors):.2f} | Median: {median(errors):.2f}"
            )
            with_nodes = sum(1 for n in nodes if n >= 1)
            print(
                f"     Nodes      - Mean: {mean(nodes):.2f} | Median: {median(nodes):.2f} | ≥ 1: {with_nodes}/{len(nodes)} ({with_nodes / len(nodes) * 100:.1f}%)"
            )
            with_edges = sum(1 for n in edges if n >= 1)
            print(
                f"     Edges      - Mean: {mean(edges):.2f} | Median: {median(edges):.2f} | ≥ 1: {with_edges}/{len(edges)} ({with_edges / len(edges) * 100:.1f}%)"
            )
            print()


def display_stats(
    stats: dict[str, dict[str, Stats]], methods_ind: dict[str, int]
) -> None:
    """Display all the statistics"""

    print("━" * 60)
    print("📊 ANALYSIS RESULTS")
    print("━" * 60)
    print()

    stats_methods: dict[str, list[Stats]] = dict()

    for dataset, infos in sorted(stats.items(), key=lambda e: e[0]):
        print("━" * 45)
        print(f"ANALYSIS RESULTS FOR {dataset}")
        print("━" * 45)
        print()

        for method, info in sorted(infos.items(), key=lambda e: e[0]):
            if method in stats_methods.keys():
                stats_methods[method].append(info)
            else:
                stats_methods[method] = [info]

            display_one_stats(info, methods_ind[method])

        print("━" * 45)
        print()

    print("━" * 45)
    print("ANALYSIS RESULTS TOTAL")
    print("━" * 45)
    print()

    for method, infos in sorted(stats_methods.items(), key=lambda e: e[0]):
        s: Stats = Stats(method)

        correct: int = sum([info.correct for info in infos])
        total: int = sum([info.total for info in infos])
        extra: None | ExtraStats = None

        for info in infos:
            if info.extra is None:
                continue
            if extra is None:
                extra = info.extra
            else:
                extra += info.extra

        s.add(total, correct)
        s.add_extra(extra)

        display_one_stats(s, methods_ind[method])

    print("━" * 60)


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
                    f"⚠️  Question '{question_name}' not found in benchmark[{dataset_name}]"
                )
                continue

            with open(result_file, "r", encoding="utf-8") as f:
                result: Any = json.load(f)

            correct_answer: str = benchmark[dataset_name][question_name]["answer"]
            user_response: str = result.get("response")

            match result_type.split("-")[0]:
                case "rag":
                    if result_type not in stats[dataset_name].keys():
                        stats[dataset_name][result_type] = Stats(result_type)
                    stats[dataset_name][result_type].add(
                        1, 1 if user_response == correct_answer else 0
                    )
                    stats[dataset_name][result_type].add_extra(
                        ExtraStatsGraph(
                            [result.get("error", 0)],
                            [result.get("nodes", 0)],
                            [result.get("edges", 0)],
                        )
                    )
                case _:
                    if result_type not in stats[dataset_name].keys():
                        stats[dataset_name][result_type] = Stats(result_type)
                    stats[dataset_name][result_type].add(
                        1, 1 if user_response == correct_answer else 0
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
