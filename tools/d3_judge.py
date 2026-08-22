"""d3_judge.py -- convert every d3_*.ply to .splat (the proven laneD conversion recipe),
copy to the HTTP viewer dir, then run the FIXED judge (verdict-line photo gate) on each.

Usage:  .venv-gs/Scripts/python.exe tools/d3_judge.py            # all d3 candidates
        .venv-gs/Scripts/python.exe tools/d3_judge.py d3_r0_vintage_s0   # one
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path("E:/PythonChimera")
VIEWER_DIR = ROOT / "models" / "triposplat" / "static" / "viewer"
GENBEAR3 = ROOT / "models" / "genbear3"
PYTHON = str(ROOT / ".venv-gs" / "Scripts" / "python.exe")


def convert(ply: Path) -> Path | None:
    splat_out = GENBEAR3 / f"{ply.stem}.splat"
    cmd = [PYTHON, str(ROOT / "tools" / "orient_splat.py"), str(ply),
           "--out", str(splat_out),
           "--alpha-min", "0.1", "--lum-min", "0.10",
           "--no-envelope", "--density-k", "3", "--blob-keep"]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0:
        print(f"CONVERT FAILED {ply.stem}: {r.stderr[-300:]}")
        return None
    shutil.copy2(splat_out, VIEWER_DIR / f"{ply.stem}.splat")
    return splat_out


def judge(tag: str) -> None:
    r = subprocess.run([PYTHON, str(ROOT / "tools" / "judge_lane.py"), f"{tag}.splat", tag],
                       capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0:
        print(f"JUDGE FAILED {tag}: {(r.stderr or r.stdout)[-300:]}")
        return
    print(r.stdout.strip()[-400:])


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1].endswith("_"):
        # batch mode: judge every <prefix>* ply, e.g. `d3_judge.py d5_`
        plys = sorted(GENBEAR3.glob(f"{sys.argv[1]}*.ply"))
    elif len(sys.argv) > 1:
        tag = sys.argv[1]
        ply = GENBEAR3 / f"{tag}.ply"
        if ply.exists():
            print(f"\n### {tag}")
            if convert(ply):
                judge(tag)
        elif (GENBEAR3 / f"{tag}.splat").exists():
            # already-converted splat (e.g. laneD_diffsplat) -- judge it directly
            print(f"\n### {tag} (existing splat)")
            src = GENBEAR3 / f"{tag}.splat"
            if not (VIEWER_DIR / f"{tag}.splat").exists():
                shutil.copy2(src, VIEWER_DIR / f"{tag}.splat")
            judge(tag)
        else:
            print(f"missing {ply}")
        return
    else:
        plys = sorted(GENBEAR3.glob("d3_*.ply"))
    for ply in plys:
        if not ply.exists():
            print(f"missing {ply}")
            continue
        print(f"\n### {ply.stem}")
        if convert(ply):
            judge(ply.stem)


if __name__ == "__main__":
    main()
