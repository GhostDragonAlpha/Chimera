"""merge_suite.py -- combine the artifacts of two suite invocations (the first
crashed at R06 on the engine-wedge gap; the re-run covers R06-R13 with fresh
twins). Merged artifacts land in --out.

Usage: python merge_suite.py --a .tmp/suite_full --b .tmp/suite_full2 --out .tmp/suite_merged
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    A, B, O = Path(a.a), Path(a.b), Path(a.out)
    O.mkdir(parents=True, exist_ok=True)

    sa = json.loads((A / "suite_summary.json").read_text(encoding="utf-8"))
    sb = json.loads((B / "suite_summary.json").read_text(encoding="utf-8"))
    merged = dict(sa)
    merged["twin"] = {"invocation_A": sa.get("twin"), "invocation_B": sb.get("twin"),
                      "note": "both invocations gate independently on the "
                              "1e-6 m twin bar (cross-boot one-ULP finding)"}
    merged["runs"] = {**sa.get("runs", {}), **sb.get("runs", {})}
    (O / "suite_summary.json").write_text(json.dumps(merged, indent=1))

    bw = json.loads((A / "bandwidth.json").read_text(encoding="utf-8"))
    (O / "bandwidth.json").write_text(json.dumps(bw, indent=1))
    (O / "topology.bin").write_bytes((A / "topology.bin").read_bytes())

    # dumps + truths: R01-R05 from A, R06-R13 from B
    count = 0
    for src in (A, B):
        for f in src.glob("dump_*.json"):
            shutil.copy2(f, O / f.name)
            count += 1
        for f in src.glob("truth_*.bin"):
            shutil.copy2(f, O / f.name)
        for f in src.glob("page_*.png"):
            shutil.copy2(f, O / f.name)
    print("merged runs:", sorted(merged["runs"].keys()))
    print("dump files:", count)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
