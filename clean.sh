#!/usr/bin/env bash

TARGETS=(".venv" ".pytest_cache" "__pycache__" ".ruff_cache" ".mypy_cache")

echo "Starting cleanup..."

for item in "${TARGETS[@]}"; do
    find . -name "$item" -exec rm -rf {} +
done

echo "Cleanup complete."
