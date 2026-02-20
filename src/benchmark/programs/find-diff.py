from dataclasses import dataclass
from pathlib import Path
from typing import Any 

import argparse
import os
import re
import json
import sys

from util import Serializable

CURRENT_DIR: str = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR: str = os.path.join(CURRENT_DIR, "../results")
BENCHMARK_FILE: str = os.path.join(CURRENT_DIR, "../benchmark.json")


@dataclass()
class Pair:
    method1: Path | None = None
    method2: Path | None = None


def load_json(file_path: str | Path) -> Any | None:
    """Helper function to load a JSON file."""
    try:
        with open(file=file_path, mode="r", encoding="utf-8") as f:
            return json.load(fp=f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}", file=sys.stderr)
        return None


def find_diff(
    results: Path,
    benchmark: dict[str, Serializable],
    method1: str,
    method2: str,
    check: bool,
) -> None:
    method1_pattern: re.Pattern[str] = re.compile(
        rf"^{re.escape(pattern=method1)}_(.+)\.json$"
    )
    method2_pattern: re.Pattern[str] = re.compile(
        rf"^{re.escape(pattern=method2)}_(.+)\.json$"
    )

    print("━" * 110)

    for dataset in sorted(results.iterdir(), key=lambda e: e.name):
        pairs: dict[str, Pair] = dict()

        print("━" * 100)
        print(f"Dataset {dataset.name}")

        for file in dataset.glob("*.json"):
            filename: str = file.name

            method1_match: re.Match[str] | None = method1_pattern.match(filename)
            if method1_match:
                file_id = method1_match.group(1)
                if file_id not in pairs:
                    pairs[file_id] = Pair()
                pairs[file_id].method1 = file
                continue

            method2_match: re.Match[str] | None = method2_pattern.match(filename)
            if method2_match:
                file_id = method2_match.group(1)
                if file_id not in pairs:
                    pairs[file_id] = Pair()
                pairs[file_id].method2 = file

        print("━" * 100)
        print(
            f"{'ID':<8} {'Method 1 File':<30} {'Method 2 File':<30} {'Who is right':<30}"
        )
        print("━" * 100)

        different: int = 0
        total: int = 0
        method1_correct: int = 0
        method2_correct: int = 0

        for file_id, file_pair in sorted(pairs.items(), key=lambda e: e[0]):
            if file_pair.method1 is None or file_pair.method2 is None:
                continue

            method1_content: dict[str, str] | None = load_json(file_path=file_pair.method1)
            method2_content: dict[str, str] | None = load_json(file_path=file_pair.method2)

            if method1_content is None or method2_content is None:
                continue

            method1_ans: str | None = method1_content.get("response")
            method2_ans: str | None = method2_content.get("response")

            try:
                correct_ans: str | None = (
                    benchmark.get(dataset.name, {}).get(file_id, {}).get("answer")
                )
                if not correct_ans:
                    continue
            except AttributeError:
                continue

            total += 1

            are_different: bool = method1_ans != method2_ans
            one_is_correct: bool = (method1_ans == correct_ans) or (
                method2_ans == correct_ans
            )

            if are_different and (not check or one_is_correct):
                which: str = "N/A"
                if method1_ans == correct_ans:
                    method1_correct += 1

                    which = method1
                elif method2_ans == correct_ans:
                    method2_correct += 1

                    which = method2

                different += 1

                m1_name: str = file_pair.method1.name if file_pair.method1 else "N/A"
                m2_name: str = file_pair.method2.name if file_pair.method2 else "N/A"
                print(f"{file_id:<8} {m1_name:<30} {m2_name:<30} {which:<30}")

        print("━" * 100)
        print(
            f"{'Total':<8} {method1_correct:<30} {method2_correct:<30} {f'{different}/{total}':<30}"
        )

    print("━" * 110)


def main() -> None:
    if not os.path.exists(path=RESULTS_DIR):
        print(f"❌ Error: Directory '{RESULTS_DIR}' does not exist")
        sys.exit(1)

    if not os.path.exists(path=BENCHMARK_FILE):
        print(f"❌ Error: File '{BENCHMARK_FILE}' does not exist")
        sys.exit(1)

    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Comparison tool for results between two inference methods (e.g., Native vs RAG).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage Example:
  python compare.py native-qwen3 rag-qwen3
  python compare.py native-qwen3 rag-qwen3 --check
        """,
    )

    _ = parser.add_argument(
        "method1",
        type=str,
        help="Prefix of the first method (e.g., 'native-qwen3-235b').",
    )

    _ = parser.add_argument(
        "method2",
        type=str,
        help="Prefix of the second method (e.g., 'rag-qwen3-235b').",
    )

    _ = parser.add_argument(
        "--check",
        action="store_true",
        help="If enabled, shows all differences even if neither method found the correct answer.",
    )

    args: argparse.Namespace = parser.parse_args()

    find_diff(
        results=Path(RESULTS_DIR),
        benchmark=load_json(file_path=BENCHMARK_FILE) or {},
        args.method1,
        args.method2,
        args.check,
    )


if __name__ == "__main__":
    main()
