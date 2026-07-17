"""
beat_lint — refuse a beat script whose vocabulary the Sleepwalker does not speak.

WHY, and it is urgent (2026-07-16): an unknown EXPECT does not error. sleepwalker.py:570
returns `False, "unknown expect ..."` — so the beat FAILS, the feature is INDICTED, and
since collapse_proxy now DERIVES the valence from the evidence (2026-07-16), the feature
is AUTOMATICALLY REJECTED.

    a typo in a test  ->  beat fails  ->  feature indicted  ->  valence 'rejected'
                                                            ->  a WORKING FEATURE CONDEMNED

Deriving the valence was the right move — it took a fact the data already settled out of
an LLM's hands. But it converted this from a mistake an agent might notice into one
nothing notices. The mitigation belongs BEFORE dispatch, and the studio already knew:

  H-17 (auto-promoted): "Beat scripts must declare only Sleepwalker-registered actions
                         before playtest dispatch."
  H-30 (auto-promoted): "Expects are schema-bound like actions — unknown expects
                         (screenshot_taken, unreadable controller properties) fail beats
                         at runtime; validate the expect vocabulary at dispatch."

Both are constitution. Neither was ever built. This is that validator.

THE VOCABULARY IS DERIVED FROM THE DISPATCH, NOT COPIED. sleepwalker branches on key
PRESENCE (`elif "move_to" in a:` / `if "actor_exists" in e:`), so this reads those
branches out of the source. A hand-copied list is a second source of truth that drifts —
which is exactly how TORQUE came to be 22.0 in one file and 2.0 in another, and how a
comment blaming walker.py sent a fix to an innocent file for two days.

IT REFUSES; IT DOES NOT REPAIR. A beat that names an expect the engine cannot answer is
not a weak test, it is a test that will blame the wrong thing. Refusing to dispatch it
costs a minute. Running it costs a feature.

    python -m core.beat_lint                       # every docs/beats/*.beats.json
    python -m core.beat_lint --beats docs/beats/x.beats.json
    python -m core.beat_lint --vocab               # what the Sleepwalker actually speaks
"""
import argparse
import glob
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
_SLEEPWALKER = os.path.join(HERE, "sleepwalker.py")

# Keys that are beat STRUCTURE, not actions — they carry the action, they are not one.
_STRUCTURAL = {"name", "beat", "features", "expects", "expect", "actions", "action",
               "note", "notes", "why", "description", "session", "demo", "beats",
               "tags", "timeout_s", "anchor"}


def vocabulary():
    """(actions, expects) — READ OUT OF THE DISPATCH, never hand-listed.

    NO `if|elif` ANCHOR (fixed 2026-07-16). The first cut was:

        re.findall(r'(?:if|elif)\\s+"([a-z_0-9]+)"\\s+in\\s+e\\b', src)

    which requires the keyword IMMEDIATELY before the quoted word — so it captured the
    first alternative of an `or` chain and SILENTLY DROPPED THE REST:

        if "component_property_below" in e or "component_property_above" in e:
           ^^^^^^^^^^^^^^^^^^^^^^^^^ seen          ^^^^^^^^^^^^^^^^^^^^^^^^^ INVISIBLE

    The Sleepwalker dispatches BOTH (sleepwalker.py:527,544). This linter called
    `component_property_above` unknown and told the agent to REFUSE TO DISPATCH
    o2_survival_witness.beats.json — a correct, working beat. Rule 8b says lint before
    dispatch, so my tool would have blocked real work with a confident error message.

    That is this file's own doctrine biting it: "THE VOCABULARY IS DERIVED FROM THE
    DISPATCH, NOT COPIED... a hand-copied list is a second source of truth that drifts."
    I derived it, and the derivation UNDER-READ the source — a subtler second source of
    truth than a copied list, and harder to see, because it looks like it is reading.

    Matching every `"<word>" in e` is deliberately over-inclusive: a stray match only
    ADDS a word the linter will tolerate, so the failure mode is under-reporting a bad
    beat. The other direction CONDEMNS A GOOD ONE, and this file's whole thesis is that
    that error costs a feature while the lint costs a minute.
    """
    src = io.open(_SLEEPWALKER, encoding="utf-8").read()
    acts = set(re.findall(r'"([a-z_0-9]+)"\s+in\s+a\b', src))
    exps = set(re.findall(r'"([a-z_0-9]+)"\s+in\s+e\b', src))
    return acts, exps


def _walk_beats(doc):
    """Yield (kind, dict) for every action/expect ITEM — the whole dict, not its keys.

    THE ITEM IS THE UNIT, NOT THE KEY. My first cut yielded every key and demanded each
    be in the vocabulary, so it condemned `store_as`, `mode` and `shift` in four REAL,
    WORKING scripts. Those are PARAMETERS: an action is `{"key": "W", "hold_s": 0.5}` —
    ONE dispatch key plus arguments — and sleepwalker's if/elif chain matches the first
    KNOWN key and reads the rest as params. So the honest question is not "is every key a
    word?" but "does this item contain a word the Sleepwalker knows?"

    That was the fifth false positive an instrument of mine produced today, and every one
    had the same shape: I checked something adjacent to the truth and called it the truth.
    """
    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in ("expects", "expect"):
                    for item in (v if isinstance(v, list) else [v]):
                        yield ("expect", item)
                elif k in ("actions", "action"):
                    for item in (v if isinstance(v, list) else [v]):
                        yield ("action", item)
                else:
                    yield from walk(v)
        elif isinstance(o, list):
            for x in o:
                yield from walk(x)
    yield from walk(doc)


def lint(path):
    """[] if the Sleepwalker speaks every word in it; a list of complaints otherwise."""
    acts, exps = vocabulary()
    try:
        doc = json.loads(io.open(path, encoding="utf-8").read())
    except Exception as e:
        return [f"UNREADABLE: {type(e).__name__}: {e}"]
    bad = []
    for kind, item in _walk_beats(doc):
        known = acts if kind == "action" else exps
        keys = set(item) if isinstance(item, dict) else {str(item)}
        if keys & known:
            continue                       # a known dispatch key -> the rest are params
        why = ("RAISES at dispatch (ValueError, sleepwalker:414)" if kind == "action" else
               "FAILS THE BEAT at runtime (sleepwalker:570 returns False) -> the feature "
               "is INDICTED -> derive_valence() -> REJECTED")
        shown = ", ".join(sorted(keys - _STRUCTURAL)) or ", ".join(sorted(keys))
        near = sorted(k for k in known for q in keys if k[:4] == q[:4] or q in k)
        hint = f"  (did you mean: {', '.join(near[:3])}?)" if near else ""
        bad.append(f"{kind} {{{shown}}} names nothing the Sleepwalker dispatches on — "
                   f"{why}{hint}")
    return bad


def already_failed(path, graph=None):
    """Expects in this beat that a PREVIOUS simtest ALREADY failed on. Same bug twice.

    THE PILLARS PROMISE THIS AND THE STUDIO DOES NOT DELIVER IT: "Biology — same bug
    never twice. The DNA learns and immunizes." Measured 2026-07-17:

        2026-07-16T15:19  obs_Tool_Scanner_Model     0/1 beats   expect actor_exists
        2026-07-17T01:24  obs_Tool_Scanner_Material  0/1 beats     ATool_Scanner ->
        2026-07-17T01:27  obs_Tool_Scanner_Material  0/1 beats     present=False

    THREE runs, TWO sessions, TEN hours, ONE cause: nothing anywhere puts an actor
    labelled `ATool_Scanner` in the level (0 hits across all three .umap files). Each
    session honestly wrote a beat, ran it, got 0/1, recorded the rejection, and moved
    on. Every one was CORRECT. Not one was TOLD that the experiment had already been
    run and settled — so the studio paid for the same measurement three times, and the
    feature is no closer.

    THE GRAPH HELD THE ANSWER EVERY TIME. 63 failed SimPlaytests, each carrying its
    exact failing expect in `outcomes[].evidence[].expect`, written by the sleepwalker
    itself. Nobody read them. That is not a missing capability — it is a missing WIRE
    between two correct components, which is the shape of five other bugs found the
    same week.

    This ASKS, it does not refuse. A settled expect is not always a reason to stop —
    if you just fixed the cause, re-running it is exactly right, and that is the whole
    point of a regression. What is never right is running it without KNOWING. So it
    reports the prior verdict and the fix it implies, and lets the agent decide with
    the record in hand instead of without it.
    """
    try:
        from core.graphify_interface import load_dna_graph
        g = graph if graph is not None else load_dna_graph()
    except Exception:
        return []                       # no graph -> no history -> nothing to say
    try:
        doc = json.loads(io.open(path, encoding="utf-8").read())
    except Exception:
        return []                       # lint() already reports unreadable

    mine = [item for kind, item in _walk_beats(doc)
            if kind == "expect" and isinstance(item, dict)]
    if not mine:
        return []

    # FAILED AND NEVER PASSED. Not "has it ever failed" — my first cut asked that and
    # was mostly NOISE: o2_survival_witness failed `component_property_below O2 < 25`
    # once at 2026-07-13 and now runs 10/10, because the beat DRAINS the O2 first and
    # the rig got fixed. Same for `pawn_class: BP_Astronaut_Character_C` (failed
    # 2026-07-07 as DefaultPawn — H-24 — now 9/9). Flagging an expect that a later run
    # PASSED is flagging a bug that got fixed, which is precisely how an instrument
    # teaches everyone to ignore it (doc_audit cried "core/ds.py DOES NOT EXIST" every
    # night for a week and nobody looked).
    #
    # An expect that has EVER passed is settled in the GOOD direction and says nothing.
    # An expect that has failed and NEVER ONCE passed is a wall — like
    # `actor_exists: ATool_Scanner`, which has never passed because nothing anywhere
    # puts that actor in the level.
    # Count and latest are tracked SEPARATELY. The first cut fused them — it only
    # touched the entry when the incoming node was NEWER, so an out-of-order older
    # node was skipped entirely and the count undercounted. It happened to read
    # "failed 3x" correctly only because the node list is roughly chronological;
    # "roughly" is not an invariant, and a counter that depends on iteration order
    # is the kind of adjacent-to-the-truth instrument this file exists to replace.
    counts, latest, passed = {}, {}, set()
    for n in g.get("nodes", []):
        if n.get("type") != "SimPlaytest":
            continue
        for o in (n.get("outcomes") or []):
            for ev in (o.get("evidence") or []):
                if not isinstance(ev.get("expect"), dict):
                    continue
                key = json.dumps(ev["expect"], sort_keys=True)
                if ev.get("ok") is True:
                    passed.add(key)
                elif ev.get("ok") is False:
                    counts[key] = counts.get(key, 0) + 1
                    prev = latest.get(key)
                    if not prev or (n.get("timestamp", "") > prev[1]):
                        latest[key] = (n.get("session", "?"), n.get("timestamp", "")[:16],
                                       str(ev.get("detail") or ev.get("note") or ""))
    settled = {k: (*latest[k], counts[k]) for k in latest if k not in passed}
    out = []
    for e in mine:
        hit = settled.get(json.dumps(e, sort_keys=True))
        if hit:
            sess, when, detail, times = hit
            out.append(f"expect {json.dumps(e)} has failed {times}x and NEVER passed "
                       f"(last: '{sess}' {when}"
                       + (f" — {detail[:56]}" if detail else "") + "). "
                       "This is a WALL, not a flake. Fix the cause first, or you are "
                       "buying the same measurement again.")
    return out


def run(paths=None, show_vocab=False):
    acts, exps = vocabulary()
    if show_vocab:
        print(f"ACTIONS the Sleepwalker speaks ({len(acts)}):\n  {', '.join(sorted(acts))}\n")
        print(f"EXPECTS it speaks ({len(exps)}):\n  {', '.join(sorted(exps))}")
        return 0
    files = paths or sorted(glob.glob(os.path.join(ROOT, "docs", "beats", "*.beats.json")))
    print("=" * 76)
    print("BEAT LINT — does the Sleepwalker speak every word in these scripts?")
    print("  An unknown EXPECT does not error: it FAILS THE BEAT, the feature is")
    print("  indicted, and the derived valence REJECTS it. A typo condemns a feature.")
    print("=" * 76)
    total, settled_total = 0, 0
    _graph = None
    try:                                # ONE load for every file, not one per file
        from core.graphify_interface import load_dna_graph
        _graph = load_dna_graph()
    except Exception:
        pass
    for p in files:
        bad = lint(p)
        old = already_failed(p, _graph)
        total += len(bad)
        settled_total += len(old)
        name = os.path.basename(p)
        if bad:
            print(f"\n!! {name}")
            for b in bad:
                print(f"     {b}")
        elif old:
            print(f"   ok  {name}   (but see SETTLED below)")
        else:
            print(f"   ok  {name}")
        for o in old:                   # a QUESTION, never a refusal — see already_failed
            print(f"    ?  {o}")
    print("\n" + "=" * 76)
    if total:
        print(f"{total} unknown word(s). REFUSE TO DISPATCH these until they are fixed —")
        print("running one costs a feature; fixing it costs a minute.")
    else:
        print("Every script speaks only words the Sleepwalker knows.")
    if settled_total:
        print(f"\n{settled_total} expect(s) the DNA has ALREADY SETTLED (marked '?' above).")
        print("Not a refusal: re-running a settled expect is exactly right IF you fixed")
        print("the cause — that is a regression test. It is only waste if you did not")
        print("know. ATool_Scanner cost 3 runs across 2 sessions because nothing said this.")
    print("=" * 76)
    return 1 if total else 0            # settled expects never fail the lint


def main(argv=None):
    p = argparse.ArgumentParser(prog="beat_lint", description=__doc__.split("\n")[1])
    p.add_argument("--beats", action="append", help="lint just this script (repeatable)")
    p.add_argument("--vocab", action="store_true", help="print what the Sleepwalker speaks")
    a = p.parse_args(argv)
    return run(paths=a.beats, show_vocab=a.vocab)


if __name__ == "__main__":
    sys.exit(main())
