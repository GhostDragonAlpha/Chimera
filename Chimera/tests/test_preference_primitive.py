"""Stage 1 proof — the comparative primitive (PreferenceObservation).

Witnesses, HERMETICALLY (the DNA graph is redirected to an in-memory store, so this
never writes to or pushes the live graph), that:

  1. record_preference mints a PreferenceObservation node with the right shape.
  2. It is human BY CONSTRUCTION — observer is not caller-settable, and an agent-sim
     process cannot mint one (a taste terminal the machine can forge is not a terminal).
  3. Validation refuses the meaningless cases (missing side; a thing preferred over
     itself).
  4. The terminal is wired: _CITED_PROVES[PreferenceObservation] == HUMAN, and HUMAN is
     a legal terminal.
  5. THE WHOLE POINT: a design-selection claim that cites a preference, walked by the
     REAL core.why.walk(), reaches "THE HUMAN". Not asserted — walked.

Run from E:/PythonChimera/Chimera:
    python tests/test_preference_primitive.py
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # the Chimera root

from core import graphify_interface as gi
from core import why


def _hermetic():
    """Redirect the DNA graph to an in-memory dict. record_* do load-modify-save on the
    module globals, so patching them here isolates the test from the live graph."""
    store = {"nodes": [], "edges": []}
    gi.load_dna_graph = lambda: {"nodes": list(store["nodes"]), "edges": list(store["edges"])}

    def _save(g):
        store["nodes"] = list(g.get("nodes", []))
        store["edges"] = list(g.get("edges", []))

    gi.save_dna_graph = _save
    return store


def _check(label, cond):
    print(f"  [{'ok' if cond else 'XX'}] {label}")
    return bool(cond)


def main():
    store = _hermetic()
    ok = True

    # 1. Happy path — a minted node with the physics fact-vectors stored on it.
    pid = gi.record_preference(
        "design_A", "design_B", seed=7,
        measures_winner={"skill_gap": 5.0, "punishes_naive": 4.0, "headroom": 0.3},
        measures_loser={"skill_gap": 2.0, "punishes_naive": 1.5, "headroom": 0.7},
        notes="A felt like it had more to master")
    ok &= _check("mints a preference id", isinstance(pid, str) and pid.startswith("preference_"))
    node = next((n for n in store["nodes"] if n.get("id") == pid), None)
    ok &= _check("node stored", node is not None)
    ok &= _check("type is PreferenceObservation", bool(node) and node.get("type") == "PreferenceObservation")
    ok &= _check("winner/loser recorded", bool(node) and node.get("winner") == "design_A" and node.get("loser") == "design_B")
    ok &= _check("seed recorded", bool(node) and node.get("seed") == 7)
    ok &= _check("measure vectors stored on node",
                 bool(node) and node.get("measures_winner", {}).get("skill_gap") == 5.0
                 and node.get("measures_loser", {}).get("headroom") == 0.7)
    ok &= _check("observer is human by construction", bool(node) and node.get("observer") == "human")

    # 2. Validation refuses the meaningless cases.
    ok &= _check("missing loser refused", str(gi.record_preference("A", "")).startswith("rejected_"))
    ok &= _check("missing winner refused", str(gi.record_preference("", "B")).startswith("rejected_"))
    ok &= _check("self-preference refused", str(gi.record_preference("A", "A")).startswith("rejected_"))
    ok &= _check("non-dict measures refused",
                 str(gi.record_preference("A", "B", measures_winner=[1, 2])).startswith("rejected_"))

    # 3. Terminal wiring.
    ok &= _check("_CITED_PROVES maps PreferenceObservation -> HUMAN",
                 why._CITED_PROVES.get("PreferenceObservation") == "HUMAN")
    ok &= _check("HUMAN is a legal terminal (THE HUMAN)",
                 why._EDGE_TERMINAL.get("HUMAN") == "THE HUMAN")

    # 4. THE POINT — a claim citing a preference WALKS to THE HUMAN (real why.walk).
    claim_id = "claim_design_A_is_operator_preferred"
    store["nodes"].append({"id": claim_id, "type": "Proposal",
                           "timestamp": "2026-07-22T00:00:00"})
    edge = gi.record_because(claim_id, pid,
                             "which design does the operator prefer?", "HUMAN")
    ok &= _check("because-edge created with proves=HUMAN",
                 isinstance(edge, dict) and edge.get("proves") == "HUMAN")
    graph = {"nodes": list(store["nodes"]), "edges": list(store["edges"])}
    hops = why.walk(claim_id, graph=graph)
    ok &= _check("walk reaches THE HUMAN terminal",
                 any(h.get("terminal") == "THE HUMAN" for h in hops))

    # 5. An agent-sim process cannot forge a human taste terminal.
    os.environ["CHIMERA_AGENT_SIM"] = "1"
    forged = gi.record_preference("X", "Y")
    os.environ.pop("CHIMERA_AGENT_SIM", None)
    ok &= _check("agent-sim mint refused", str(forged).startswith("rejected_"))

    print()
    print("PASS — the comparative primitive is a real, walkable HUMAN terminal"
          if ok else "FAIL — see the [XX] lines above")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
