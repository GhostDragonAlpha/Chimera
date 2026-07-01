#!/usr/bin/env python3
"""count_systems.py - Count C++ files and lines per subsystem in the Chimera project."""

import os
import sys
from collections import defaultdict

PROJECT_ROOT = r"E:\PythonChimera\Chimera"
SOURCE_DIR = os.path.join(PROJECT_ROOT, "Source", "Chimera")


def count_files_and_lines(directory: str) -> tuple[int, int]:
    """Count .h/.cpp files and total lines in a directory (non-recursive)."""
    file_count = 0
    line_count = 0
    if not os.path.isdir(directory):
        return file_count, line_count

    for entry in os.listdir(directory):
        path = os.path.join(directory, entry)
        if os.path.isfile(path):
            ext = os.path.splitext(entry)[1].lower()
            if ext in (".h", ".cpp"):
                file_count += 1
                try:
                    with open(path, "r", encoding="utf-8", errors="replace") as f:
                        line_count += sum(1 for _ in f)
                except OSError:
                    pass

    return file_count, line_count


def main() -> None:
    if not os.path.isdir(SOURCE_DIR):
        print(f"Error: Source directory not found: {SOURCE_DIR}", file=sys.stderr)
        sys.exit(1)

    subsystems = defaultdict(lambda: [0, 0])  # {name: [file_count, line_count]}

    for entry in sorted(os.listdir(SOURCE_DIR)):
        path = os.path.join(SOURCE_DIR, entry)
        if not os.path.isdir(path):
            continue
        files, lines = count_files_and_lines(path)
        if files > 0:
            subsystems[entry] = [files, lines]

    # Print table
    print("=" * 52)
    print("  Chimera C++ Subsystem File & Line Counts")
    print("=" * 52)
    print(f"{'Subsystem':<30} {'Files':>6} {'Lines':>8}")
    print("-" * 52)

    total_files = 0
    total_lines = 0

    for name, (files, lines) in subsystems.items():
        total_files += files
        total_lines += lines
        print(f"{name:<30} {files:>6} {lines:>8}")

    print("-" * 52)
    print(f"{'TOTAL':<30} {total_files:>6} {total_lines:>8}")
    print("=" * 52)


if __name__ == "__main__":
    main()
