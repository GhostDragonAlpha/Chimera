#!/usr/bin/env python
"""Clean up task_progress.md by removing duplicate rehearsal decisions."""

from pathlib import Path

tp = Path("task_progress.md")
lines = tp.read_text(encoding="utf-8").split("\n")

# Find all Rehearsal decision lines and their line numbers
rehearsal_lines = []
for i, line in enumerate(lines):
    if line.startswith("# Rehearsal decision"):
        rehearsal_lines.append((i, line))

print(f"Found {len(rehearsal_lines)} rehearsal decisions")

# Group by feature name (extract from title)
from collections import defaultdict

by_feature = defaultdict(list)
for i, line in rehearsal_lines:
    # Extract feature name from title like "next move: Verb_Look"
    if "next move:" in line:
        feature = line.split("next move:")[-1].strip().split(" ")[0]
        by_feature[feature].append((i, line))

print(f"\nGrouped by feature:")
for feature, items in sorted(by_feature.items()):
    print(f"  {feature}: {len(items)} decisions")

# Keep only the most recent decision per feature (highest line number)
kept_lines = set()
for feature, items in by_feature.items():
    # Sort by line number descending, keep only the first (most recent)
    items_sorted = sorted(items, key=lambda x: -x[0])
    kept_lines.add(items_sorted[0][0])  # Keep most recent

print(f"\nKept {len(kept_lines)} decisions out of {len(rehearsal_lines)}")

# Now rebuild the file with duplicates removed
new_lines = []
for i, line in enumerate(lines):
    if i in kept_lines:
        new_lines.append(line)
    elif any(i == r[0] for r in rehearsal_lines):
        # Skip this duplicate rehearsal decision
        continue
    else:
        new_lines.append(line)

print(f"Original file: {len(lines)} lines")
print(f"Cleaned file: {len(new_lines)} lines")
print(f"Savings: {len(lines) - len(new_lines)} lines removed")

# Write cleaned version
tp.write_text("\n".join(new_lines), encoding="utf-8")
print("Done!")
