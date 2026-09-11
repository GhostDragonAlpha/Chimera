"""Name-contract checker for engine-frost-shader-name-01 (stdlib-only).

Derives the CMake shader-output manifest from ChimeraEngine/engine/shaders
using the SAME rules as engine/CMakeLists.txt:56-62 (comp/glsl -> <stem>.spv;
vert/frag -> <name>.spv keeping the stage extension), extracts every shader
read name from an engine.cpp text, and reports coherence.

Usage:
  python check_names.py --engine-text <path-or-- for stdin> --label PRE|POST \
      --out-dir <checks dir> [--c1] [--c2]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]  # ascend to worktree root
while not (REPO / "ChimeraEngine" / "engine" / "shaders").is_dir():
    if REPO.parent == REPO:
        raise FileNotFoundError("worktree root not found")
    REPO = REPO.parent
SHADERS = REPO / "ChimeraEngine" / "engine" / "shaders"


def manifest() -> dict[str, str]:
    """Derived output name -> source file name (CMakeLists rules)."""
    out: dict[str, str] = {}
    for src in sorted(SHADERS.iterdir()):
        name = src.name
        if name.endswith((".vert", ".frag")):
            out[name + ".spv"] = name
        elif name.endswith((".comp", ".glsl")):
            out[Path(name).stem + ".spv"] = name
    return out


def read_names(engine_text: str) -> list[tuple[int, str]]:
    """Every shader read name with its 1-based line number.

    Captures ALL shader-name literals: direct read_file strings, the
    (base + "/shaders/...) form, the hinge spv_path assignment, and the
    w_make_pipeline call sites. Every 'shaders/<name>.spv' literal in
    engine.cpp is a name the loader expects the runtime to carry.
    """
    names = []
    for m in re.finditer(r'"[/\\]?shaders/([A-Za-z0-9_.]+\.spv)"', engine_text):
        line = engine_text.count("\n", 0, m.start()) + 1
        names.append((line, m.group(1)))
    return names


def classify(read: str) -> str:
    """graphics = stage-suffixed vert/frag read; compute = bare stem read."""
    return ("graphics"
            if re.fullmatch(r"[A-Za-z0-9_]+\.(vert|frag)\.spv", read)
            else "compute")


def incoherent(read: str, man: dict[str, str]) -> bool:
    """A read whose expected derived artifact does not exist."""
    return read not in man


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine-text", required=True,
                    help="path to engine.cpp text (use - for stdin)")
    ap.add_argument("--label", required=True, choices=["PRE", "POST"])
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--rows", type=str, default="")
    args = ap.parse_args()

    text = (sys.stdin.read() if args.engine_text == "-"
            else Path(args.engine_text).read_text(encoding="utf-8",
                                                  errors="replace"))
    man = manifest()
    reads = read_names(text)
    violators = [(ln, nm) for ln, nm in reads if incoherent(nm, man)]

    lines = [f"{args.label} run — engine text: {args.engine_text}",
             f"derived manifest entries: {len(man)} "
             f"(comp/glsl -> bare stem.spv; vert/frag -> name.stage.spv)",
             f"shader read sites found: {len(reads)}",
             ""]
    for ln, nm in reads:
        src = man.get(nm, "<ABSENT FROM DERIVED MANIFEST>")
        lines.append(f"  engine.cpp:{ln} reads {nm:36s} "
                     f"[{classify(nm):8s}] source={src}")
    lines.append("")
    lines.append(f"violators (read name absent from the derived manifest): "
                 f"{len(violators)}")
    for ln, nm in violators:
        lines.append(f"  engine.cpp:{ln} reads {nm} — INCOHERENT")
    (Path(args.out_dir) /
     f"c2_manifest_{args.label.lower()}.txt").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")

    if args.rows:
        rows = dict(p.split("=", 1) for p in args.rows.split(","))
        summary = [f"{args.label} summary (prereg thresholds)",
                   f"  read sites: {len(reads)}",
                   f"  violators: {len(violators)} "
                   f"(prereg: PRE=1, POST=0)",
                   f"  all reads resolve in manifest: "
                   f"{not violators}"]
        for k, v in rows.items():
            summary.append(f"  {k}: {v}")
        (Path(args.out_dir) /
         f"c1_source_trace_{args.label.lower()}.txt").write_text(
            "\n".join(summary) + "\n", encoding="utf-8")

    print(f"{args.label}: reads={len(reads)} violators={len(violators)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
