"""
Benchmark Launcher
Launches different benchmark functions based on command line parameter
"""

from datetime import datetime
from pathlib import Path

import logging
import os
import sys
import argparse
import importlib
from types import ModuleType
from typing import Callable

CURRENT_DIR: str = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = "logs"

BENCHMARK_MODULES: dict[str, str] = dict()


def load_modules() -> None:
    """
    Add to BENCHMARK_MODULES the list of module in benchmark.programs
    """
    for function in Path(os.path.join(CURRENT_DIR, "programs")).glob(pattern="*.py"):
        function_name: str = function.name.removesuffix(".py")
        if function_name == "__init__":
            continue

        BENCHMARK_MODULES[function_name] = f"benchmark.programs.{function_name}"


def load_benchmark_function(module_path: str) -> Callable[[], None]:
    """
    Dynamically import a module and return its main function
    Handles modules with hyphens in their names
    """
    try:
        module: ModuleType = importlib.import_module(name=module_path)
        return module.main  # pyright: ignore[reportAny]
    except (ImportError, AttributeError) as e:
        raise ImportError(f"Cannot load module '{module_path}': {e}")


def main() -> None:
    """Main entry point for the benchmark launcher"""
    load_modules()

    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Launch different benchmark functions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Available benchmarks:
  {", ".join(BENCHMARK_MODULES.keys())}
        """,
    )

    _ = parser.add_argument(
        "function",
        choices=BENCHMARK_MODULES.keys(),
        help="Function to run",
        type=str,
    )

    _ = parser.add_argument(
        "--logging",
        action="store_true",
        help="Enable logging output (disabled by default).",
    )

    args, remaining_args = parser.parse_known_args()

    function: str = str(args.function)  # pyright: ignore[reportAny]
    is_logging: bool = bool(args.logging)  # pyright: ignore[reportAny]

    module_path: str = BENCHMARK_MODULES[function]
    benchmark_func: Callable[[], None] = load_benchmark_function(module_path)

    if is_logging:
        os.makedirs(name=LOG_DIR, exist_ok=True)
        log_path: str = os.path.join(
            LOG_DIR,
            datetime.now().strftime(format="%Y-%m-%d_%H-%M-%S-%f") + ".log",
        )

        logging.basicConfig(
            level=logging.INFO,
            format="{levelname}:{name}:\n{message}",
            style="{",
            handlers=[
                logging.FileHandler(filename=log_path),
                logging.StreamHandler(),
            ],
        )

    print(f"Launching benchmark: {function}")
    print("-" * 50)

    try:
        original_argv: list[str] = sys.argv
        sys.argv = [sys.argv[0]] + remaining_args

        benchmark_func()

        sys.argv = original_argv
    except Exception as e:
        print(f"Error running benchmark '{function}': {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
