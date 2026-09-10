"""run_falsify.py -- run the elastic-foundation falsification battery and write evidence.

Each invocation creates a UNIQUE timestamped evidence directory under
docs/evidence/elastic_foundation/ and writes:
    results.json       machine-readable per-check records
    battery_report.txt human-readable report
Nothing is ever overwritten; the report records git facts, interpreter, numpy version.

Exit code: 0 == all checks (including all mutations) passed, 1 otherwise.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from . import battery

EVIDENCE_ROOT = Path(__file__).resolve().parent.parent.parent / "docs" / "evidence" / "elastic_foundation"


def git_facts(repo: Path) -> dict:
    out = {}
    for key, args in (("head", ["rev-parse", "HEAD"]),
                      ("describe", ["describe", "--tags", "--always"]),
                      ("status", ["status", "--porcelain"])):
        try:
            r = subprocess.run(["git", "-C", str(repo)] + args,
                               capture_output=True, text=True, timeout=30)
            out[key] = (r.stdout or "").strip()
            if key == "status":
                out["dirty"] = bool(r.stdout and r.stdout.strip())
        except Exception as e:
            out[key] = f"<git error: {e}>"
    return out


def _json_ready(x):
    if x is None or isinstance(x, (str, int, float, bool)):
        return x
    if isinstance(x, (np.bool_,)):
        return bool(x)
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        return float(x)
    if isinstance(x, np.ndarray):
        return [_json_ready(v) for v in x.tolist()]
    if isinstance(x, (tuple, list)):
        return [_json_ready(v) for v in x]
    if isinstance(x, dict):
        return {str(k): _json_ready(v) for k, v in x.items()}
    return str(x)


def run(args) -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    tag = f"run_{stamp}"
    if args.suffix:
        tag += f"_{args.suffix}"
    out_dir = EVIDENCE_ROOT / tag
    out_dir.mkdir(parents=True, exist_ok=False)

    checks = battery.run_all()
    total, failed, _ = battery.summarize(checks)

    records = []
    for c in checks:
        records.append({"tag": c.tag, "name": c.name, "passed": bool(c.passed),
                        "message": c.message,
                        "facts": {k: _json_ready(v) for k, v in c.facts.items()}})

    env = {"python": sys.version.split()[0], "numpy": np.version.version,
           "eps64": float(np.finfo(np.float64).eps),
           "alg_budget": battery.ALG, "fd_budget": battery.FD_LIMIT}
    meta = {"tag": tag, "timestamp_utc": stamp, "env": env,
            "git_e_pythonchimera": git_facts(Path(__file__).resolve().parent.parent.parent),
            "totals": {"run": total, "failed": failed}}
    results = {"meta": meta, "checks": records}

    (out_dir / "results.json").write_text(
        json.dumps(results, indent=2), encoding="utf8")
    report = render_report(results)
    (out_dir / "battery_report.txt").write_text(report, encoding="utf8")

    print(report)
    return 0 if failed == 0 else 1


def render_report(results: dict) -> str:
    m = results["meta"]
    L = []
    L.append("elastic-foundation falsification battery")
    L.append("=" * 60)
    L.append(f"run tag            : {m['tag']}")
    L.append(f"timestamp (UTC)    : {m['timestamp_utc']}")
    L.append(f"python / numpy     : {m['env']['python']} / {m['env']['numpy']}")
    L.append(f"eps64 / ALG / FD   : {m['env']['eps64']:.3e} / {m['env']['alg_budget']:.3e} / "
             f"{m['env']['fd_budget']:.3e}")
    L.append("git (workspace)    : head={head} dirty={dirty} status={status!r}".format(
        **m["git_e_pythonchimera"]))
    L.append(f"totals             : {m['totals']['run']} checks, {m['totals']['failed']} failed")
    L.append("-" * 60)
    for c in results["checks"]:
        mark = "PASS" if c["passed"] else "FAIL"
        L.append(f"[{c['tag']}] {mark}  {c['name']}")
        if c["message"]:
            L.append(f"        message: {c['message']}")
        for k, v in c["facts"].items():
            L.append(f"        {k}: {v}")
    L.append("=" * 60)
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="run the elastic-foundation falsification battery")
    ap.add_argument("--suffix", default="", help="extra tag suffix (must be filesystem-safe)")
    args = ap.parse_args(argv)
    return run(args)


if __name__ == "__main__":
    sys.exit(main())