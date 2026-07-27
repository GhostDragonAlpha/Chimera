"""Proof of the schema-drift fix — the trainer now reads the real (Schema-B) objective files.

Before: docs/objectives/*.json are Schema B ({field, min/max} + maximize/minimize + walls),
and trainer.Objective parsed only Schema A ({measure, kind, ...}) — so Objective.load on a
real file raised KeyError 'kind'. normalize_objective() now translates B -> A at load, and
Schema A passes through unchanged.

Run from E:/PythonChimera/Chimera:
    python tests/test_objective_schema.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # the Chimera root

from core.trainer import Objective, normalize_objective, _KINDS

OBJ = Path(__file__).resolve().parent.parent / "docs" / "objectives"


def _check(label, cond):
    print(f"  [{'ok' if cond else 'XX'}] {label}")
    return bool(cond)


def main():
    ok = True

    # 1. The real Schema-B files now LOAD (used to raise KeyError 'kind').
    for name in ("granular", "economy", "brain_gpu"):
        try:
            obj = Objective.load(OBJ / f"{name}.json")
            loaded = True
        except Exception as e:
            loaded = False
            print(f"      {name}: {e}")
        ok &= _check(f"{name}.json loads via Objective.load", loaded)
        if not loaded:
            continue
        ok &= _check(f"{name}: every term has a valid kind",
                     all(c.get("kind") in _KINDS for c in obj.constraints))
        ok &= _check(f"{name}: every term has a measure",
                     all(c.get("measure") for c in obj.constraints))

    # 2. Schema B specifics translate correctly (granular). NOTE a field can yield TWO terms
    # — e.g. angle_mean_deg has a band (from its constraint) AND a maximize (from the list) —
    # so check for term EXISTENCE, not one-kind-per-measure.
    g = Objective.load(OBJ / "granular.json")

    def _has(measure, kind):
        return any(c["measure"] == measure and c["kind"] == kind for c in g.constraints)

    ok &= _check("granular: {field,min,max} -> a band term (angle_mean_deg)",
                 _has("angle_mean_deg", "band"))
    ok &= _check("granular: {field,max} -> an at_most term (angle_spread_deg)",
                 _has("angle_spread_deg", "at_most"))
    ok &= _check("granular: a field in BOTH constraint and maximize yields both terms",
                 _has("angle_mean_deg", "band") and _has("angle_mean_deg", "maximize"))
    ok &= _check("granular: maximize list -> a maximize term (probe_locality_worst)",
                 _has("probe_locality_worst", "maximize"))
    ok &= _check("granular: a wall became a term's why",
                 any(c.get("why") for c in g.constraints))
    ok &= _check("granular: maximize term got a derived ref",
                 all("ref" in c for c in g.constraints if c["kind"] in ("maximize", "minimize")))

    # 3. It actually SCORES now (the whole point — used to crash before scoring).
    m = {"angle_mean_deg": 40.0, "unsettled_worst": 0.0, "angle_spread_deg": 5.0,
         "frozen_fraction_mean": 0.1, "probe_locality_worst": 0.5, "settle_sweeps_worst": 100.0,
         "avalanche_max_worst": 50.0, "angle_consistency_deg": 3.0, "topples_per_grain_mean": 0.5,
         "avalanche_mean_worst": 5.0}
    score, detail = g.score(m)
    ok &= _check(f"granular scores a measures dict (score={score:.3f} in [0,1])",
                 0.0 <= score <= 1.0 and len(detail) > 0)

    # 4. Schema A passes through UNCHANGED (nothing already using it is affected).
    a_spec = {"name": "x", "scenario": "s",
              "constraints": [{"measure": "sum", "kind": "maximize", "ref": 2.0, "weight": 1.0}]}
    passthrough = normalize_objective(dict(a_spec))
    ok &= _check("Schema A is returned unchanged", passthrough == a_spec)
    a = Objective(a_spec)
    ok &= _check("Schema A still constructs and scores",
                 abs(a.score({"sum": 2.0})[0] - 0.5) < 1e-9)   # 2/(2+2) = 0.5

    # 5. Idempotent: normalizing an already-normalized spec is a no-op.
    once = normalize_objective(json.loads((OBJ / "economy.json").read_text(encoding="utf-8")))
    twice = normalize_objective(once)
    ok &= _check("normalize is idempotent", once == twice)

    print()
    print("PASS — the trainer reads the real objective files; the drift is closed"
          if ok else "FAIL — see the [XX] lines above")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
