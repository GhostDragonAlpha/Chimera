"""Stage 5 proof — the Will (human-authored taste prior) + CAPCOM wiring.

Covers:
  - will_to_prior / compose: the Will decides with ZERO comparisons; comparisons refine it;
    a firm-conviction axis resists a contradicting comparison more than a loose one.
  - the chat fold: a transient nudge moves a loose axis and barely moves a firm one, and
    never overrides (shift factor < 1).
  - the Will actually steers a decision the flat model couldn't make.
  - governance: core.taste has NO writer for taste.json; propose_edit only drafts.
  - CAPCOM: surface_ask / propose_will_edit / attune_and_surface post the right signals
    (hermetic — a mock post; nothing hits the real operator channel or the live graph).

Run from E:/PythonChimera/Chimera:
    python tests/test_taste.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # the Chimera root

from core import graphify_interface as gi
from core import preference_select as ps
from core import taste


def _check(label, cond):
    print(f"  [{'ok' if cond else 'XX'}] {label}")
    return bool(cond)


def _will(axes):
    return {"axes": axes}


def main():
    ok = True

    # 1. The Will decides from zero comparisons (prior returned as weights).
    will = _will({"skill_gap": {"weight": 2.0, "conviction": 1.0, "scale": 20.0},
                  "headroom": {"weight": -1.0, "conviction": 0.8, "scale": 0.25}})
    m0 = taste.compose(will, [])
    ok &= _check("Will-only model exists at 0 comparisons",
                 m0 is not None and m0.n_pairs == 0)
    ok &= _check("Will-only weights are the authored weights",
                 abs(m0.weights["skill_gap"] - 2.0) < 1e-6 and abs(m0.weights["headroom"] + 1.0) < 1e-6)
    hi = {"measures": {"skill_gap": 60.0, "headroom": 0.3}}
    lo = {"measures": {"skill_gap": 5.0, "headroom": 0.3}}
    ok &= _check("Will ranks the higher-skill_gap design above the lower",
                 m0.utility(hi["measures"]) > m0.utility(lo["measures"]))

    # 2. No Will: too few comparisons -> None; enough -> a flat learned model.
    ok &= _check("no Will + too few comparisons -> None (fall back to physics)",
                 taste.compose({}, [({"a": 1.0}, {"a": 0.0})] * 3, min_pairs=5) is None)
    ok &= _check("no Will + enough comparisons -> a model",
                 taste.compose({}, [({"a": 1.0}, {"a": 0.0})] * 6, min_pairs=5) is not None)

    # 3. Firm conviction resists a contradicting comparison; loose yields.
    w2 = _will({"firm": {"weight": 0.0, "conviction": 12.0, "scale": 1.0},
                "loose": {"weight": 0.0, "conviction": 0.2, "scale": 1.0}})
    pairs = [({"firm": 1.0, "loose": 1.0}, {"firm": -1.0, "loose": -1.0})] * 6  # push both up equally
    mf = taste.compose(w2, pairs)
    ok &= _check(f"firm axis moves less than loose under equal evidence "
                 f"({mf.weights['firm']:.3f} < {mf.weights['loose']:.3f})",
                 mf.weights["firm"] < mf.weights["loose"])

    # 4. Chat fold: loose axis yields to a nudge, firm resists, neither exceeds the nudge.
    mc = taste.compose(w2, [], chat={"firm": 1.0, "loose": 1.0})
    ok &= _check(f"chat moves the loose axis more than the firm ({mc.weights['loose']:.3f} > "
                 f"{mc.weights['firm']:.3f})", mc.weights["loose"] > mc.weights["firm"])
    ok &= _check("chat never overrides: firm axis barely moves (<0.1)", mc.weights["firm"] < 0.1)
    ok &= _check("chat is bounded: no axis exceeds the raw nudge (1.0)",
                 mc.weights["loose"] < 1.0 and mc.weights["firm"] < 1.0)

    # 5. The Will steers a decision the flat/physics path could not make.
    steer = _will({"A": {"weight": 3.0, "conviction": 1.0, "scale": 1.0},
                   "B": {"weight": 0.0, "conviction": 1.0, "scale": 1.0}})
    Y = {"genome": {"n": "Y"}, "score": 0.5, "measures": {"A": 0.0, "B": 3.0}}
    X = {"genome": {"n": "X"}, "score": 0.5, "measures": {"A": 3.0, "B": 0.0}}
    shortlist = [Y, X]                                    # physics order puts Y first
    phys = ps.select_preferred(shortlist, model=None)
    tasteful = ps.select_preferred(shortlist, model=taste.compose(steer, []))
    ok &= _check("no taste -> physics winner (Y, the shortlist head)", phys["chosen"] is Y)
    ok &= _check("the Will re-ranks to X (its favoured axis)", tasteful["chosen"] is X)

    # 6. Governance: the taste module never writes taste.json; propose_edit only drafts.
    src = Path(taste.__file__).read_text(encoding="utf-8")
    ok &= _check("core.taste has NO writer (no write_text / open-for-write)",
                 "write_text" not in src and "open(" not in src)
    ok &= _check("TASTE_PATH is taste.json (the human's file), not the example",
                 taste.TASTE_PATH.name == "taste.json")
    draft = taste.propose_edit("skill_gap", 3.0, "recent comparisons lean higher",
                               will=_will({"skill_gap": {"weight": 2.0}}))
    ok &= _check("propose_edit drafts current->proposed, no write",
                 draft["current_weight"] == 2.0 and draft["proposed_weight"] == 3.0
                 and draft["kind"] == "will_edit_proposal")

    # 7. CAPCOM surfacing (mock post; nothing hits the real channel).
    posted = []

    def fake_post(channel, msg, level="info", data=None, source="system"):
        posted.append({"channel": channel, "level": level, "data": data, "source": source})
        return f"sig_{len(posted)}"

    sig = ps.surface_ask((0, 1), shortlist, post=fake_post)
    ok &= _check("surface_ask posts a preference_ask on the 'preference' channel",
                 sig == "sig_1" and posted[-1]["channel"] == "preference"
                 and posted[-1]["data"]["kind"] == "preference_ask")
    ok &= _check("surface_ask is a no-op when there is nothing to ask",
                 ps.surface_ask(None, shortlist, post=fake_post) is None)
    ps.propose_will_edit(draft, post=fake_post)
    ok &= _check("propose_will_edit posts a proposal carrying the draft",
                 posted[-1]["level"] == "proposal" and posted[-1]["data"] is draft)

    # 8. attune_and_surface end to end: a tie under the Will -> a comparison is surfaced.
    gi.load_dna_graph = lambda: {"nodes": [], "edges": []}     # no recorded prefs; Will decides
    tie = [{"genome": {"n": 0}, "score": 0.5, "measures": {"A": 1.0, "B": 1.0}},
           {"genome": {"n": 1}, "score": 0.5, "measures": {"A": 1.0, "B": 1.0}}]
    out = ps.attune_and_surface({"top_k": tie}, will=steer, min_pairs=5, post=fake_post)
    ok &= _check("attune_and_surface fits from the Will (source=taste, 0 comparisons)",
                 out["source"] == "taste" and out["n_preferences"] == 0)
    ok &= _check("a tie the Will can't break is surfaced to CAPCOM",
                 out["ask"] is not None and out["ask_signal"] is not None)

    print()
    print("PASS — the Will is the prior, chat nudges within bounds, and only the human writes it"
          if ok else "FAIL — see the [XX] lines above")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
