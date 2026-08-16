"""score_saturation.py — the quality-band instrument (operator directive 2026-08-16).

The P/V band is set by SATURATION, driven by taste (operator directive
2026-08-16): a taste judgment — the human's or an LLM's, EQUALLY valuable,
no hierarchy — is the discovery instrument. Each critique round names what
offends; each offense is a deficiency class. When the discovery curve
saturates (Chao2 completeness + dry tail), the scores at that point ARE the
band floor. Same mathematics as the engine's S1 question saturation:
species accumulation with a Chao2 estimate of the unseen.

Rule 0 (stated before use): a deliverable's deficiency space is finite and
discoverable by repeated skeptical critique. Prediction: rounds produce a
rising-then-dry discovery curve. Falsifier: rounds keep discovering NEW
deficiency classes at a flat rate — the curve never humps — meaning the
rubric's categories are wrong, not incomplete; re-frame (rule 8), don't keep
scoring.

Ledger: score_ledger.json (tracked — it IS the band's evidence).
Each entry: {task, P, V, p_breakdown, v_breakdown, deficiencies: [ids...]}.
A deficiency id is stable text (e.g. "v:subject<15%-of-frame") so repeat
sightings are the SAME species, not new ones.

Saturation rule (standard species-accumulation stopping rule, the same one
the engine's S1 uses):
  completeness = S_obs / S_chao2,  S_chao2 = S_obs + f1^2 / (2*f2)
  (f1 = deficiency classes seen in exactly ONE round, f2 = in exactly TWO)
  SATURATED when completeness >= 0.9 AND the last 3 rounds discovered 0 new
  classes (dry tail). Both thresholds are the conventional stopping rule;
  the operator can raise them, never lower them, per scoreband.

Usage:
  python score_saturation.py add <task> <P> <V> <def-id> [def-id...]
  python score_saturation.py status
"""
import json
import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parent / "score_ledger.json"
DRY_TAIL = 3
COMPLETENESS_MIN = 0.9


def load():
    if LEDGER.exists():
        return json.loads(LEDGER.read_text())
    return {"rounds": []}


def stats(rounds):
    seen = {}
    order = []
    per_round_new = []
    for r in rounds:
        new = 0
        for d in r["deficiencies"]:
            if d not in seen:
                seen[d] = 0
                order.append(d)
                new += 1
            seen[d] += 1
        per_round_new.append(new)
    s_obs = len(seen)
    f1 = sum(1 for v in seen.values() if v == 1)
    f2 = sum(1 for v in seen.values() if v == 2)
    s_chao2 = s_obs + (f1 * f1 / (2 * f2) if f2 else (f1 * (f1 - 1) / 2 if f1 > 1 else 0))
    completeness = s_obs / s_chao2 if s_chao2 else 1.0
    tail = 0
    for n in reversed(per_round_new):
        if n == 0:
            tail += 1
        else:
            break
    saturated = completeness >= COMPLETENESS_MIN and tail >= DRY_TAIL and len(rounds) > DRY_TAIL
    return {
        "rounds": len(rounds), "S_obs": s_obs, "f1": f1, "f2": f2,
        "S_chao2": round(s_chao2, 2), "completeness": round(completeness, 3),
        "per_round_new": per_round_new, "dry_tail": tail,
        "saturated": saturated,
    }


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1
    led = load()
    if args[0] == "add":
        task, p, v = args[1], float(args[2]), float(args[3])
        defs = args[4:]
        led["rounds"].append({"task": task, "P": p, "V": v, "deficiencies": defs})
        LEDGER.write_text(json.dumps(led, indent=2) + "\n")
        s = stats(led["rounds"])
        print(f"logged {task}: P={p} V={v} deficiencies={len(defs)} "
              f"({s['per_round_new'][-1]} new)")
    elif args[0] == "status":
        s = stats(led["rounds"])
        print(json.dumps(s, indent=2))
        if led["rounds"]:
            last = led["rounds"][-1]
            print(f"latest: {last['task']} P={last['P']} V={last['V']}")
        if s["saturated"]:
            band = led["rounds"][-1]
            print(f"SATURATED — band floor set at P={band['P']} V={band['V']} "
                  f"(completeness {s['completeness']}, dry tail {s['dry_tail']})")
        else:
            print(f"NOT saturated — completeness {s['completeness']} "
                  f"(need >= {COMPLETENESS_MIN}), dry tail {s['dry_tail']} "
                  f"(need >= {DRY_TAIL}); keep discovering")
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
