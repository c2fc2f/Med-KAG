"""
Benchmark Launcher
Launches different benchmark functions based on command line parameter
"""

import os
import sys
import argparse
import importlib
from pathlib import Path

CURRENT_DIR: str = os.path.dirname(os.path.abspath(__file__))

BENCHMARK_MODULES: dict[str, str] = dict()

def load_modules():
    """
    Add to BENCHMARK_MODULES the list of module in benchmark.programs
    """
    for function in Path(os.path.join(CURRENT_DIR, "programs")).glob("*.py"):
        function = function.name.removesuffix(".py")
        if function == "__init__":
            continue

        BENCHMARK_MODULES[function] = f"benchmark.programs.{function}"


def load_benchmark_function(module_path):
    """
    Dynamically import a module and return its main function
    Handles modules with hyphens in their names
    """
    try:
        module = importlib.import_module(module_path)
        return module.main
    except (ImportError, AttributeError) as e:
        raise ImportError(f"Cannot load module '{module_path}': {e}")


def main():
    """Main entry point for the benchmark launcher"""
    load_modules()

    parser = argparse.ArgumentParser(
        description="Launch different benchmark functions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Available benchmarks:
  {", ".join(BENCHMARK_MODULES.keys())}
        """,
    )

    parser.add_argument(
        "function", choices=BENCHMARK_MODULES.keys(), help="Function to run"
    )

    args = parser.parse_args()

    module_path = BENCHMARK_MODULES[args.function]
    benchmark_func = load_benchmark_function(module_path)

    print(f"Launching benchmark: {args.function}")
    print("-" * 50)

    try:
        benchmark_func()
    except Exception as e:
        print(f"Error running benchmark '{args.benchmark}': {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
