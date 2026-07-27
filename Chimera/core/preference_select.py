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
from core import taste
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


def fit_taste(alpha=1.0, min_pairs=5, graph=None, will=None, chat=None):
    """Compose the human's WILL (prior) + recorded comparisons (likelihood) + any transient
    chat nudge into a taste model. Returns (model, n_pairs).

    model is None only when there is NEITHER a Will NOR enough comparisons — then the caller
    falls back to the physics winner. With a Will, a model is returned even at zero
    comparisons (it decides from the authored taste alone). See core.taste.compose."""
    pairs = load_preferences(graph)
    will = will if will is not None else taste.load_will()
    model = taste.compose(will, pairs, chat=chat, alpha=alpha, min_pairs=min_pairs)
    return model, len(pairs)


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


def attune(trainer_result, alpha=1.0, min_pairs=5, decisive_margin=0.65,
           graph=None, will=None, chat=None, rng=None):
    """End to end: physics-feasible shortlist (trainer_result['top_k']) -> taste re-rank,
    where taste = WILL (prior) composed with recorded comparisons and any chat nudge.

    Returns select_preferred's dict plus n_preferences (how many recorded comparisons the
    taste rests on) — so a caller sees whether the choice was physics or taste, and on how
    much of each. Pure: no CAPCOM side effect (use attune_and_surface for that).
    """
    shortlist = trainer_result.get("top_k") or []
    model, n = fit_taste(alpha=alpha, min_pairs=min_pairs, graph=graph, will=will, chat=chat)
    out = select_preferred(shortlist, model=model, decisive_margin=decisive_margin, rng=rng)
    out["n_preferences"] = n
    return out


# ---------------------------------------------------------------------------
# CAPCOM wiring — the operator channel carries the frontier asks and the AI's
# proposed Will edits. The AI never writes taste.json; it only surfaces.
# ---------------------------------------------------------------------------
def _label(design):
    m = design.get("measures") or {}
    return "[" + ", ".join(f"{k}={float(v):.2f}" for k, v in list(m.items())[:4]) + "]"


def surface_ask(ask, shortlist, source="preference-loop", post=None):
    """Post the frontier comparison to CAPCOM — the one physics couldn't settle and only the
    operator can. `ask` is (i, j) indices into shortlist (from attune/select_preferred).
    No-op returning None if ask is falsy. `post` is injectable for testing; default is
    capcom.post_safe (fire-and-forget, never raises)."""
    if not ask:
        return None
    if post is None:
        from core import capcom
        post = capcom.post_safe
    i, j = ask
    a, b = shortlist[i], shortlist[j]
    msg = (f"TASTE ASK — which is more fun? A {_label(a)} vs B {_label(b)}. "
           f"Physics can't decide this; only you can.")
    data = {"kind": "preference_ask",
            "A": {"genome": a.get("genome"), "measures": a.get("measures")},
            "B": {"genome": b.get("genome"), "measures": b.get("measures")},
            "answer_with": ("python -m core.graphify_record preference --winner <A|B> "
                            "--loser <the other> --measures-winner '<json>' "
                            "--measures-loser '<json>'")}
    return post("preference", msg, level="ask", data=data, source=source)


def propose_will_edit(draft, source="preference-loop", post=None):
    """Stage an AI-PROPOSED Will edit to CAPCOM for the human to commit or discard. The AI
    never writes taste.json — this only surfaces the proposal (see core.taste.propose_edit)."""
    if post is None:
        from core import capcom
        post = capcom.post_safe
    msg = (f"WILL EDIT PROPOSAL — axis '{draft.get('axis')}' "
           f"{draft.get('current_weight')} -> {draft.get('proposed_weight')}: "
           f"{draft.get('reason')} (yours to commit or discard; the AI won't touch taste.json)")
    return post("preference", msg, level="proposal", data=draft, source=source)


def attune_and_surface(trainer_result, source="preference-loop", post=None, **kw):
    """attune(), and if taste cannot confidently settle the top two, surface that comparison
    to CAPCOM. Returns the attune result with 'ask_signal' = the posted signal id (or None
    when nothing needed asking)."""
    out = attune(trainer_result, **kw)
    out["ask_signal"] = (surface_ask(out.get("ask"), trainer_result.get("top_k") or [],
                                     source=source, post=post) if out.get("ask") else None)
    return out


# ---------------------------------------------------------------------------
# RUN ON ITS OWN — one autonomous turn of the whole loop, schedulable.
# ---------------------------------------------------------------------------
def run_cycle(domain, objective, pop=200, gens=40, seed=1, top_k=12,
              will=None, chat=None, graph=None, min_pairs=5, decisive_margin=0.65,
              source="preference-loop", post=None, rng=None, log=print):
    """One turn: TRAIN `domain` against the physics `objective`, ATTUNE the feasible
    shortlist to the operator's Will, and SURFACE any comparison it can't settle to CAPCOM.
    Returns attune_and_surface's dict plus trained_score / n_feasible.

    `objective` may be a trainer.Objective, a Schema-A spec dict, or a path to a Schema-A
    objective JSON. Schedule this (cron / circadian tick) and the loop runs on its own — it
    only ever ASKS via CAPCOM, so the operator stays the taste terminal.

    NOTE: training real features needs a Schema-A objective the trainer can read; the current
    docs/objectives/*.json are Schema-B (the drift flagged in the preference-loop plan), so
    autonomous runs over real features wait on that fix. The mechanism itself is complete.
    """
    from core import trainer as _trainer
    if isinstance(objective, _trainer.Objective):
        obj = objective
    elif isinstance(objective, dict):
        obj = _trainer.Objective(objective)
    else:
        obj = _trainer.Objective.load(objective)
    result = _trainer.train(domain, obj, pop=pop, gens=gens, seed=seed,
                            workers=1, log=log, top_k=top_k)
    out = attune_and_surface(result, source=source, post=post, will=will, chat=chat,
                             graph=graph, min_pairs=min_pairs,
                             decisive_margin=decisive_margin, rng=rng)
    out["trained_score"] = result.get("score")
    out["n_feasible"] = len(result.get("top_k") or [])
    return out


def _main(argv=None):
    import argparse
    p = argparse.ArgumentParser(prog="python -m core.preference_select",
                                description="run the preference loop on its own")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="TRAIN a feature, ATTUNE to the Will, SURFACE asks to CAPCOM")
    r.add_argument("--domain", required=True, help="a trainable module, e.g. core.trainables.economy")
    r.add_argument("--objective", required=True, help="a Schema-A objective JSON path")
    r.add_argument("--pop", type=int, default=200)
    r.add_argument("--gens", type=int, default=40)
    r.add_argument("--seed", type=int, default=1)
    a = p.parse_args(argv)
    if a.cmd == "run":
        out = run_cycle(a.domain, a.objective, pop=a.pop, gens=a.gens, seed=a.seed)
        print(f"\ntrained score {out.get('trained_score')}, {out['n_feasible']} physics-feasible")
        print(f"taste source={out['source']}  (fit from {out['n_preferences']} recorded comparisons)")
        if out.get("chosen"):
            print(f"chosen design: {out['chosen'].get('measures')}")
        if out.get("ask"):
            print(f"asked the operator via CAPCOM (signal {out.get('ask_signal')}): pair {out['ask']}")
        else:
            print("taste decided; nothing needed asking")
        return 0
    return 1


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(_main())
