"""grow.py -- THE ENZYME. One file. It walks `story/` and grows it.

The story is the genome; this is only the chemistry that reads it. At every folder it does the
same three moves, which is what makes this GROWTH and not construction -- a cell does not consult
a blueprint of the finished body, it divides and differentiates from local signals, and its
POSITION determines its identity. Here that is literal: a folder's path IS its address, and its
parent's handed-down numbers ARE its signal.

Each folder holds three things and nothing else:
    story.md      the human story -- WHAT this membrane is          (the NODE, Alan's)
    physics.py    the law -- derive(parent, free) -> this membrane's numbers   (the EDGE, mine)
    trained.json  the free numbers this law leaves open, once fitted (optional)

Adding world means adding a paragraph and a law. It never means adding more of this file.

Run:  python story/grow.py
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _load(py: Path):
    spec = importlib.util.spec_from_file_location(f"law_{py.parent.name}", py)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _fmt(v):
    if isinstance(v, float):
        return f"{v:.4g}"
    return str(v)


def grow(folder: Path, parent: dict | None = None, depth: int = 0) -> None:
    """Grow one membrane from its parent's numbers, then let it grow its children."""
    ind = "   " * depth
    story = folder / "story.md"
    law = folder / "physics.py"

    if not story.exists():
        print(f"{ind}{folder.name}/   -- awaiting the human story")
        return
    if not law.exists():
        print(f"{ind}{folder.name}/   -- story written, LAW MISSING (no edge reaches this membrane)")
        return

    free = {}
    tj = folder / "trained.json"
    if tj.exists():
        free = json.loads(tj.read_text())

    nums = _load(law).derive(parent, free)
    (folder / "numbers.json").write_text(json.dumps(nums, indent=2))
    shown = ", ".join(f"{k}={_fmt(v)}" for k, v in list(nums.items())[:4])
    print(f"{ind}{folder.name}/   {shown}")

    for child in sorted(d for d in folder.iterdir() if d.is_dir() and not d.name.startswith((".", "_"))):
        grow(child, nums, depth + 1)


if __name__ == "__main__":
    print("\nGROWING THE STORY\n" + "=" * 60)
    for top in sorted(d for d in ROOT.iterdir() if d.is_dir() and not d.name.startswith((".", "_"))):
        grow(top)
    print()
