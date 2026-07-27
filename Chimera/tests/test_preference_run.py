"""Proof of the autonomous turn — run_cycle: train -> attune to the Will -> surface.

Runs the whole loop end to end against the pref_selftest fixture with an inline Schema-A
objective and an injected Will, a mock CAPCOM post, and an empty graph — so nothing touches
the live channel, the live graph, or the drifted objective files.

Run from E:/PythonChimera/Chimera:
    python tests/test_preference_run.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # the Chimera root

from core import graphify_interface as gi
from core import preference_select as ps


def _check(label, cond):
    print(f"  [{'ok' if cond else 'XX'}] {label}")
    return bool(cond)


def main():
    ok = True
    gi.load_dna_graph = lambda: {"nodes": [], "edges": []}      # no recorded comparisons

    posted = []

    def fake_post(channel, msg, level="info", data=None, source="system"):
        posted.append({"channel": channel, "level": level, "data": data})
        return f"sig_{len(posted)}"

    # Schema-A objective over the fixture's 'sum'; a Will over the same axis (prefers high sum).
    obj = {"name": "runtest", "scenario": "",
           "constraints": [{"measure": "sum", "kind": "maximize", "ref": 1.0, "weight": 1.0}]}
    will = {"axes": {"sum": {"weight": 2.0, "conviction": 1.0, "scale": 1.0}}}

    out = ps.run_cycle("core.trainables.pref_selftest", obj, pop=24, gens=5, seed=0,
                       will=will, post=fake_post)

    ok &= _check("run_cycle trained the feature (score > 0)", (out.get("trained_score") or 0) > 0)
    ok &= _check("produced a physics-feasible shortlist", out["n_feasible"] >= 1)
    ok &= _check("chose a design", out.get("chosen") is not None)
    ok &= _check("attuned to the Will (source=taste)", out["source"] == "taste")
    ok &= _check("no recorded comparisons were used (Will-only)", out["n_preferences"] == 0)
    # Whatever it decided, an ask (if any) must have gone to CAPCOM and nowhere else.
    if out.get("ask"):
        ok &= _check("any ask was surfaced to CAPCOM (mock)", out.get("ask_signal") is not None
                     and posted and posted[-1]["channel"] == "preference")
    else:
        ok &= _check("taste decided without asking", out.get("ask_signal") is None)

    print()
    print("PASS — the loop runs one autonomous turn: train -> attune -> (ask only if needed)"
          if ok else "FAIL — see the [XX] lines above")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
