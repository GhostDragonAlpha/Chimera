"""preference_select - THE ATTUNE-BACK: choose the operator-preferred design from a
physics-feasible shortlist.

Stage 4, the piece that closes the loop. trainer.train() now returns top_k — the
physics-FEASIBLE designs (every hard gate passed) plus their measures. This module loads
the operator's recorded preferences (Stage 1 PreferenceObservation nodes), fits the taste
model (Stage 2), and re-ranks that shortlist by taste.

THE DIVISION IS THE WHOLE POINT: physics decided who is ELIGIBLE (the shortlist); taste
decides which eligible design is PREFERRED. Taste never rescues an infeasible design — it
was never on the list. And the taste signal is only ever the human's recorded comparisons;
no LM ranks, labels, or judges here.

GRACEFUL DEGRADATION. With too few recorded preferences to fit a model, select_preferred
returns the PHYSICS winner (source="physics") — on day one, before the operator has
expressed any taste, the loop still ships the best physics design. As preferences
accumulate it attunes. And when taste cannot confidently separate the top two feasible
designs, it returns the current best AND proposes the comparison worth asking (Stage 3) —
the honest "one more comparison, please", not a coin flip dressed as a decision.

This is the integration layer, so unlike core.preference / core.preference_elicit it is NOT
membrane-clean: it reads the DNA graph via core.graphify_interface.
"""
from __future__ import annotations

from core import graphify_interface as gi
from core.preference import PreferenceModel
from core.preference_elicit import select_query


def load_preferences(graph=None):
    """The operator's recorded comparisons as (measures_winner, measures_loser) pairs.

    Reads PreferenceObservation nodes (observer='human'; that is guaranteed by construction
    in record_preference, but re-checked here) that carry both measure vectors. A node
    without stored measures cannot train a taste model over the physics axes, so it is
    skipped.
    """
    graph = graph if graph is not None else gi.load_dna_graph()
    pairs = []
    for n in graph.get("nodes", []):
        if n.get("type") != "PreferenceObservation" or n.get("observer") != "human":
            continue
        mw, ml = n.get("measures_winner") or {}, n.get("measures_loser") or {}
        if isinstance(mw, dict) and isinstance(ml, dict) and mw and ml:
            pairs.append((mw, ml))
    return pairs


def fit_taste(features=None, alpha=1.0, min_pairs=5, graph=None):
    """Fit the taste model from recorded preferences. Returns (model, n_pairs), with model
    None when there are fewer than min_pairs comparisons — too few to trust a taste over
    physics (below this the model is mostly its own prior)."""
    pairs = load_preferences(graph)
    if len(pairs) < min_pairs:
        return None, len(pairs)
    return PreferenceModel(features=features, alpha=alpha).fit(pairs), len(pairs)


def select_preferred(shortlist, model=None, decisive_margin=0.65, rng=None):
    """Re-rank a physics-feasible shortlist by taste.

    shortlist: the trainer's top_k — [{genome, score, measures, ...}, ...].
    Returns {chosen, ranking, source, ask, confidence, n_feasible}:
      - source="empty"   : nothing was feasible; chosen is None.
      - source="physics" : no taste model yet; chosen is the top physics design.
      - source="taste"   : re-ranked by the operator's taste. `ask` is a (i, j) pair of
        shortlist indices to put to the operator when the top two are too close to call
        (predicted prob < decisive_margin) — otherwise None.
    """
    if not shortlist:
        return {"chosen": None, "ranking": [], "source": "empty",
                "ask": None, "confidence": None, "n_feasible": 0}
    if model is None:
        return {"chosen": shortlist[0], "ranking": list(range(len(shortlist))),
                "source": "physics", "ask": None, "confidence": None,
                "n_feasible": len(shortlist)}

    designs = [d.get("measures") or {} for d in shortlist]
    order = model.rank(designs)
    confidence, ask = None, None
    if len(order) >= 2:
        confidence = float(model.prob(designs[order[0]], designs[order[1]]))
        if confidence < decisive_margin:      # top two too close for the current taste
            q = select_query(model, designs, strategy="bald", rng=rng)
            ask = (q.a, q.b) if q is not None else None
    return {"chosen": shortlist[order[0]], "ranking": order, "source": "taste",
            "ask": ask, "confidence": confidence, "n_feasible": len(shortlist)}


def attune(trainer_result, features=None, alpha=1.0, min_pairs=5, decisive_margin=0.65,
           graph=None, rng=None):
    """End to end: physics-feasible shortlist (trainer_result['top_k']) -> taste re-rank.

    Returns select_preferred's dict plus n_preferences (how many recorded comparisons the
    taste was fit from) — so a caller can see whether the choice was physics or taste, and
    how much taste it rests on.
    """
    shortlist = trainer_result.get("top_k") or []
    model, n = fit_taste(features=features, alpha=alpha, min_pairs=min_pairs, graph=graph)
    out = select_preferred(shortlist, model=model, decisive_margin=decisive_margin, rng=rng)
    out["n_preferences"] = n
    return out
