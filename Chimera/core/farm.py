"""farm — the method, batched like a crop. Grow a FIELD of features, harvest the ripe ones.

The operator's insight: a farmer never tends one plant -- they run each STEP across the whole
field (sow, irrigate, grow, harvest), and that is how you drive many product concepts at once.
The train-everything method is a fixed pipeline every feature walks:

    author domain -> author objective -> probe -> train -> read walls -> iterate -> verify -> wire

A fixed pipeline over many items IS a batch. This runs the MACHINE steps of it -- train, check,
harvest -- across a whole field of (domain, objective) pairs, and reports which came in ripe,
which need another season (their objective still pins a wall), and which failed. The AUTHORING
of each domain is still CODE, one at a time (the floor you cannot batch); everything downstream
is here, automated, no human-in-the-loop per feature.

This is "GPU for the population" gone up one level: the trainer already batches the POPULATION
of genomes; the farm batches the FEATURES across the field. Same move, one scale up.

    python -m core.farm                         # a small default field
    python -m core.farm --field economy,granular --pop 80 --gens 25
    python -m core.farm --all --pop 60 --gens 15   # the whole crop
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBJ_DIR = ROOT / "docs" / "objectives"
TRAINABLES = ROOT / "core" / "trainables"

# A fast default field -- analytical domains that grow in seconds. --all runs everything.
DEFAULT_FIELD = ["economy", "resource_economy", "granular"]


def discover_field() -> list:
    """Every (domain, objective) seed pair: docs/objectives/X.json with a core/trainables/X.py."""
    out = []
    for obj in sorted(OBJ_DIR.glob("*.json")):
        stem = obj.stem
        if stem.endswith(".trained") or stem.endswith(".farm"):
            continue
        if (TRAINABLES / f"{stem}.py").exists():
            out.append(stem)
    return out


def check_constraints(spec: dict, measures: dict):
    """Re-check the objective's constraints against the winner's measures. Returns (passed,
    violations) -- the harvest test: a crop is RIPE only if every wall is satisfied."""
    passed, viols = True, []
    for c in spec.get("constraints", []) or []:
        f = c.get("field") or c.get("measure")
        if not f or f not in measures:
            continue
        v = float(measures[f])
        lo, hi = c.get("min"), c.get("max")
        if lo is not None and v < float(lo) - 1e-9:
            passed = False
            viols.append(f"{f}={v:.3g} < {lo}")
        if hi is not None and v > float(hi) + 1e-9:
            passed = False
            viols.append(f"{f}={v:.3g} > {hi}")
    return passed, viols


def grow_one(name: str, pop: int, gens: int, timeout: float = 120.0):
    """Run the trainer over one seed (a subprocess -- clean isolation, writes its own winner).
    Returns (result_dict_or_None, status_or_None)."""
    obj = OBJ_DIR / f"{name}.json"
    out = OBJ_DIR / f"{name}.farm.trained.json"
    if out.exists():
        out.unlink()
    cmd = [sys.executable, "-m", "core.trainer", "--domain", f"core.trainables.{name}",
           "--objective", str(obj), "--pop", str(pop), "--gens", str(gens), "--out", str(out)]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=str(ROOT))
    except subprocess.TimeoutExpired:
        return None, "timed out"
    except Exception as e:
        return None, f"launch failed: {e}"
    if not out.exists():
        return None, "no winner (domain/objective error)"
    try:
        return json.loads(out.read_text(encoding="utf-8")), None
    except Exception as e:
        return None, f"unreadable winner: {e}"


def harvest(field: list, pop: int, gens: int, timeout: float = 120.0) -> list:
    """Grow every seed and sort the field: ripe / needs-another-season / composted."""
    rows = []
    for name in field:
        res, err = grow_one(name, pop, gens, timeout)
        if res is None:
            rows.append({"name": name, "status": "composted", "detail": err})
            continue
        spec = json.loads((OBJ_DIR / f"{name}.json").read_text(encoding="utf-8"))
        passed, viols = check_constraints(spec, res.get("measures", {}))
        rows.append({
            "name": name, "status": "ripe" if passed else "needs-season",
            "score": res.get("score"), "violations": viols,
        })
    return rows


def _main() -> int:
    import argparse
    import sys as _sys
    try:
        _sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="the method, batched like a crop")
    ap.add_argument("--field", type=str, default=None, help="comma-separated seed names")
    ap.add_argument("--all", action="store_true", help="grow every discoverable seed")
    ap.add_argument("--pop", type=int, default=80)
    ap.add_argument("--gens", type=int, default=25)
    ap.add_argument("--timeout", type=float, default=120.0, help="per-seed timeout (s)")
    a = ap.parse_args()

    if a.all:
        field = discover_field()
    elif a.field:
        field = [s.strip() for s in a.field.split(",") if s.strip()]
    else:
        field = DEFAULT_FIELD
    all_seeds = discover_field()

    print(f"  === THE FARM: sowing {len(field)} of {len(all_seeds)} seeds "
          f"(pop {a.pop} x gens {a.gens} each) ===")
    print("  each seed = a (domain, objective); the trainer grows it, the walls test it ripe\n")
    import time
    t0 = time.time()
    rows = harvest(field, a.pop, a.gens, a.timeout)
    dt = time.time() - t0

    ripe = [r for r in rows if r["status"] == "ripe"]
    season = [r for r in rows if r["status"] == "needs-season"]
    compost = [r for r in rows if r["status"] == "composted"]

    print(f"  {'seed':20} {'status':14} {'score':>8}   note")
    for r in rows:
        sc = f"{r.get('score'):.3f}" if isinstance(r.get("score"), (int, float)) else "-"
        note = (r.get("detail") or ("; ".join(r.get("violations", [])[:2]) if r.get("violations")
                                    else "all walls satisfied"))
        print(f"  {r['name']:20} {r['status']:14} {sc:>8}   {note[:52]}")

    print(f"\n  === HARVEST ({dt:.0f}s) ===")
    print(f"    RIPE ({len(ripe)}): {', '.join(r['name'] for r in ripe) or '-'}  -> ready to wire")
    print(f"    NEEDS SEASON ({len(season)}): {', '.join(r['name'] for r in season) or '-'}  "
          f"-> iterate the objective (the walls it rides)")
    print(f"    COMPOSTED ({len(compost)}): {', '.join(r['name'] for r in compost) or '-'}  "
          f"-> recorded, not lost")
    print("\n  the method ran across the whole field in one pass, no human-in-the-loop per seed.")
    print("  author the domains one at a time (the floor); grow + harvest them in batches (the farm).")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
