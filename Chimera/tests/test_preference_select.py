"""Stage 4 proof — the attune-back: physics-feasible shortlist -> taste re-rank.

Covers the three seams:
  - trainer._shortlist: feasibility filter (score>0), best-first, dedup, sort, k-cap.
  - trainer.train(): really returns a correct top_k (run against the pref_selftest fixture
    with an inline Schema-A objective, so it does not depend on the drifted objective files).
  - core.preference_select: load recorded preferences, graceful physics fallback with no
    taste, taste re-rank, and the "ask one more comparison" path when the top two are close.

The graph reads are hermetic (in-memory), so nothing touches the live DNA graph.

Run from E:/PythonChimera/Chimera:
    python tests/test_preference_select.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # the Chimera root

import numpy as np

from core import graphify_interface as gi
from core import preference_select as ps
from core.preference import PreferenceModel, synth_designs, synth_pairs
from core.trainer import Objective, _shortlist, train


def _check(label, cond):
    print(f"  [{'ok' if cond else 'XX'}] {label}")
    return bool(cond)


def _patch_graph(nodes):
    gi.load_dna_graph = lambda: {"nodes": list(nodes), "edges": []}


def main():
    ok = True

    # 1. _shortlist: feasibility, best-first, dedup, sort, cap.
    eval_pop = [{"id": 0}, {"id": 1}, {"id": 2}, {"id": 3}]
    eval_res = [(0.0, {}, []), (0.9, {"m": 9}, []), (0.5, {"m": 5}, []), (0.7, {"m": 7}, [])]
    best, best_score, best_m, best_d = {"id": 1}, 0.9, {"m": 9}, []
    sl = _shortlist(eval_pop, eval_res, best, best_score, best_m, best_d, k=10)
    ok &= _check("infeasible (score 0) is excluded", all(e["genome"] != {"id": 0} for e in sl))
    ok &= _check("best-ever leads the shortlist", sl[0]["genome"] == {"id": 1})
    ok &= _check("best is not duplicated (dedup by genome)",
                 sum(1 for e in sl if e["genome"] == {"id": 1}) == 1)
    ok &= _check("scores are non-increasing", all(sl[i]["score"] >= sl[i + 1]["score"]
                                                  for i in range(len(sl) - 1)))
    ok &= _check("k-cap respected", len(_shortlist(eval_pop, eval_res, best, best_score,
                                                   best_m, best_d, k=2)) == 2)
    ok &= _check("all-infeasible -> empty shortlist",
                 _shortlist(eval_pop, [(0.0, {}, [])] * 4, {"id": 0}, 0.0, {}, [], 10) == [])

    # 2. trainer.train() really returns a correct top_k (Schema-A objective, fast fixture).
    obj = Objective({"name": "selftest", "scenario": "",
                     "constraints": [{"measure": "sum", "kind": "maximize", "ref": 1.0, "weight": 1.0}]})
    res = train("core.trainables.pref_selftest", obj, pop=24, gens=4, seed=0,
                workers=1, log=lambda *a: None, top_k=6)
    tk = res.get("top_k")
    ok &= _check("train() returns a top_k list", isinstance(tk, list) and len(tk) >= 1)
    ok &= _check("top_k respects the cap", len(tk) <= 6)
    ok &= _check("every shortlisted design is physics-feasible (score>0)",
                 all(e["score"] > 0 for e in tk))
    ok &= _check("top_k[0] is the trainer's best-ever", tk[0]["score"] == res["score"])
    ok &= _check("each entry carries genome + measures",
                 all("genome" in e and "measures" in e and "sum" in e["measures"] for e in tk))
    ok &= _check("backward compatible: the old keys are still there",
                 all(k in res for k in ("genome", "score", "measures", "detail", "pinned")))

    # 3. load_preferences: pulls valid human comparisons, ignores the rest.
    _patch_graph([
        {"id": "p1", "type": "PreferenceObservation", "observer": "human",
         "measures_winner": {"skill_gap": 5.0}, "measures_loser": {"skill_gap": 2.0}},
        {"id": "p2", "type": "PreferenceObservation", "observer": "human",
         "measures_winner": {}, "measures_loser": {"skill_gap": 1.0}},          # no winner measures
        {"id": "p3", "type": "PreferenceObservation", "observer": "agent-sim",
         "measures_winner": {"skill_gap": 9.0}, "measures_loser": {"skill_gap": 1.0}},  # not human
        {"id": "o1", "type": "Observation", "verdict": "accepted"},             # not a preference
    ])
    pairs = ps.load_preferences()
    ok &= _check("load_preferences keeps only the one valid human pair", len(pairs) == 1)

    # 4. select_preferred: physics fallback with no taste; taste re-rank with a model.
    shortlist = [{"genome": {"i": i}, "score": 0.5, "measures": d}
                 for i, d in enumerate(synth_designs(np.random.default_rng(4),
                                                      ["skill_gap", "punishes_naive", "headroom"], 8))]
    phys = ps.select_preferred(shortlist, model=None)
    ok &= _check("no taste model -> physics winner (source=physics)",
                 phys["source"] == "physics" and phys["chosen"] is shortlist[0])
    ok &= _check("empty shortlist -> source=empty, chosen None",
                 ps.select_preferred([], model=None)["source"] == "empty")

    rng = np.random.default_rng(5)
    feats = ["skill_gap", "punishes_naive", "headroom"]
    designs = synth_designs(rng, feats, 60)
    model = PreferenceModel(alpha=1.0).fit(synth_pairs(rng, feats, designs, np.array([2.0, 1.0, -1.0]), 60))
    taste = ps.select_preferred(shortlist, model=model)
    top_by_model = model.rank([d["measures"] for d in shortlist])[0]
    ok &= _check("taste model chooses the max-utility feasible design",
                 taste["source"] == "taste" and taste["chosen"] is shortlist[top_by_model])

    # 5. the "ask one more comparison" path: two ~equal designs -> propose a comparison.
    tie = [{"genome": {"i": 0}, "score": 0.5, "measures": {"skill_gap": 1.0, "punishes_naive": 1.0, "headroom": 1.0}},
           {"genome": {"i": 1}, "score": 0.5, "measures": {"skill_gap": 1.0, "punishes_naive": 1.0, "headroom": 1.0}}]
    close = ps.select_preferred(tie, model=model, rng=np.random.default_rng(6))
    ok &= _check("near-tie -> proposes a comparison to the operator (ask is set)",
                 close["ask"] is not None)

    # 6. attune end to end (hermetic graph with enough preferences).
    pref_nodes = []
    dsn = synth_designs(np.random.default_rng(9), feats, 40)
    for w, l in synth_pairs(np.random.default_rng(9), feats, dsn, np.array([2.0, 1.0, -1.0]), 8):
        pref_nodes.append({"id": f"pref_{len(pref_nodes)}", "type": "PreferenceObservation",
                           "observer": "human", "measures_winner": w, "measures_loser": l})
    _patch_graph(pref_nodes)
    out = ps.attune({"top_k": shortlist}, min_pairs=5)
    ok &= _check("attune fits taste from the graph and re-ranks (source=taste)",
                 out["source"] == "taste" and out["n_preferences"] == 8 and out["chosen"] is not None)

    print()
    print("PASS — physics shortlists, taste re-ranks, and the loop asks when unsure"
          if ok else "FAIL — see the [XX] lines above")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
