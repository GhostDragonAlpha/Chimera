"""taste - THE WILL: a human-authored taste reference the machine attunes to.

Stage 5. The human authors docs/objectives/taste.json — weights over the physics axes,
how firmly each is held (conviction), and each axis's scale. This module composes that
Will (a PRIOR) with the operator's recorded comparisons (the LIKELIHOOD) and any transient
in-session chat context (a weak nudge) into a single PreferenceModel — the Bayesian update
we built, now started from the human's authored reference instead of from nothing.

THE GOVERNANCE MEMBRANE, and it is not politeness:
  - taste.json is HUMAN-ONLY-WRITABLE. This module has NO writer for it. The AI may PROPOSE
    an edit (propose_edit -> a draft dict staged to CAPCOM for the human), never commit one.
  - chat context enters ONLY as an explicit {axis: nudge} the caller built from the human's
    actual words, and it is TRANSIENT: it shifts the current decision and vanishes with the
    session unless the human commits it to the Will. It never touches taste.json.
  - the composition is arithmetic on the human's authored numbers and physics's measured
    numbers. No LM judges. An LM may help the human DRAFT the Will (like it drafts the
    physics objectives, which the human owns); it never applies its own opinion per decision.

THE COMPOSITION ORDER (the membranes, in the order the reasoning must place them):
  1. physics gates who is eligible (upstream, in the trainer; taste never touches it),
  2. the WILL is the prior (durable, human-authored, most authoritative taste),
  3. recorded COMPARISONS refine it (durable, the human's actual choices),
  4. CHAT nudges the current decision only (transient, weak, human's words),
  then decide by w . phi over the eligible designs; if it can't confidently separate the
  top two, ask the operator (Stage 3, surfaced via CAPCOM).

Reads a config file only (not the DNA graph) — the caller supplies the comparisons.
"""
from __future__ import annotations

import json
from pathlib import Path

from core.preference import PreferenceModel

TASTE_PATH = Path(__file__).parent.parent / "docs" / "objectives" / "taste.json"

# How strongly a transient chat nudge pulls. Small on purpose: a weak, wide prior that a
# firm Will conviction resists (shift = c/(conviction+c); see _fold_chat).
CHAT_PRECISION = 0.3


def load_will(path=None) -> dict:
    """The authored Will, or {} if none exists yet. Never written here."""
    p = Path(path) if path else TASTE_PATH
    if not p.exists():
        return {}
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return d if isinstance(d, dict) else {}


def will_to_prior(will: dict):
    """Extract (features, prior_mean, prior_precision, center, scale) from the Will spec.

    Each axis declares weight (the standardised taste weight = prior mean), conviction (the
    prior precision — how firmly held), and scale (the axis's spread, for standardisation).
    center is 0: it cancels in the pairwise differences the model actually uses.
    """
    axes = (will or {}).get("axes") or {}
    features = list(axes.keys())
    prior_mean = {f: float(axes[f].get("weight", 0.0)) for f in features}
    prior_precision = {f: float(axes[f].get("conviction", 1.0)) for f in features}
    center = {f: 0.0 for f in features}
    scale = {f: float(axes[f].get("scale", 1.0)) or 1.0 for f in features}
    return features, prior_mean, prior_precision, center, scale


def _fold_chat(prior_mean: dict, prior_precision: dict, chat: dict, c: float):
    """Fold a transient chat nudge into the prior as a weak Gaussian prior product. Per axis:
    precision -> lam0 + c; mean -> w0 + [c/(lam0+c)]*nudge. The shift factor < 1 and shrinks
    as conviction (lam0) grows, so a firm Will axis barely moves and a loose one yields."""
    pm, pp = dict(prior_mean), dict(prior_precision)
    for f, nudge in (chat or {}).items():
        lam0 = pp.get(f, 1.0)
        pp[f] = lam0 + c
        pm[f] = pm.get(f, 0.0) + (c / (lam0 + c)) * float(nudge)
    return pm, pp


def compose(will: dict, comparisons, chat: dict = None, alpha: float = 1.0,
            min_pairs: int = 5, chat_precision: float = CHAT_PRECISION):
    """Compose the Will (prior) + comparisons (likelihood) + chat (transient nudge) into a
    fitted PreferenceModel, or None if there is no taste signal at all.

    - Will present -> a model anchored on the authored taste, usable with ZERO comparisons.
      Comparisons (however few) refine it; chat nudges it (bounded by conviction).
    - No Will, but >= min_pairs comparisons -> the flat model of Stages 2-4 (learn from
      scratch), so the loop still attunes once enough comparisons exist.
    - Neither -> None: no taste, the caller falls back to the physics winner.
    """
    comparisons = list(comparisons or [])
    features, prior_mean, prior_precision, center, scale = will_to_prior(will)

    if features:                                   # a Will exists
        if chat:
            prior_mean, prior_precision = _fold_chat(prior_mean, prior_precision,
                                                     chat, chat_precision)
        return PreferenceModel(features=features, alpha=alpha, prior_mean=prior_mean,
                               prior_precision=prior_precision, center=center,
                               scale=scale).fit(comparisons)

    if len(comparisons) >= min_pairs:              # no Will, but enough to learn
        return PreferenceModel(alpha=alpha).fit(comparisons)

    return None


def propose_edit(axis: str, new_weight: float, reason: str, will: dict = None):
    """A DRAFT of a Will change, for the human to review and commit — never written here.

    Returns a plain dict describing the proposed edit (current -> proposed, with the reason).
    A caller stages this to CAPCOM; the human is the only writer of taste.json.
    """
    will = will if will is not None else load_will()
    axes = (will or {}).get("axes") or {}
    current = axes.get(axis, {}).get("weight")
    return {"kind": "will_edit_proposal", "axis": axis,
            "current_weight": current, "proposed_weight": float(new_weight),
            "reason": reason,
            "note": "PROPOSAL ONLY — taste.json is human-only-writable. Commit it yourself, "
                    "or discard. The AI never edits your Will."}
