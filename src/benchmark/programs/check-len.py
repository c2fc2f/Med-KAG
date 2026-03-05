"""Script to check JSON files for field length mismatches."""

from pathlib import Path
from typing import Sized
from util import Serializable

import argparse
import json


def get_nested_value(
    data: dict[str, Serializable],
    key_path: str,
) -> Sized | None:
    """Traverse nested dict using dot-separated key path."""
    keys: list[str] = key_path.split(sep=".")
    current: Serializable = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    if not isinstance(current, Sized):
        return None
    return current


def check_files(
    target_dir: str, pattern: str, key_path: str, expected_length: int
) -> None:
    """Check JSON files matching pattern for field length mismatches."""
    directory: Path = Path(target_dir)
    matched_files: list[Path] = list(directory.glob(pattern))

    if not matched_files:
        print(f"No files found matching pattern: {pattern}")
        return

    for file_path in sorted(matched_files):
        try:
            with file_path.open("r", encoding="utf-8") as f:
                data: dict[str, Serializable] = json.load(fp=f)  # pyright: ignore[reportAny]

            value: Sized | None = get_nested_value(data, key_path)
            length: int = len(value) if value is not None else 0

            if length != expected_length:
                print(f"Mismatch found: {file_path} (Length: {length})")

        except (json.JSONDecodeError, OSError) as e:
            print(f"Error reading {file_path}:\n\t{e}")


def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Check JSON files for field length mismatches."
    )
    _ = parser.add_argument(
        "--dir",
        type=str,
        help="Target directory to search in",
        required=True,
    )
    _ = parser.add_argument(
        "--pattern",
        type=str,
        help="Glob pattern for matching files",
        required=True,
    )
    _ = parser.add_argument(
        "--key",
        type=str,
        default="stats.generator.full-response",
        help="Dot-separated key path to the field (default: stats.generator.full-response)",
    )
    _ = parser.add_argument(
        "--expected-length",
        type=int,
        default=1,
        help="Expected length of the field (default: 1)",
    )

    args: argparse.Namespace = parser.parse_args()
    check_files(
        target_dir=args.dir,  # pyright: ignore[reportAny]
        pattern=args.pattern,  # pyright: ignore[reportAny]
        key_path=args.key,  # pyright: ignore[reportAny]
        expected_length=args.expected_length,  # pyright: ignore[reportAny]
    )


if __name__ == "__main__":
    main()
