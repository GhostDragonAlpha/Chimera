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
    total = 0
    for p in files:
        bad = lint(p)
        total += len(bad)
        name = os.path.basename(p)
        if bad:
            print(f"\n!! {name}")
            for b in bad:
                print(f"     {b}")
        else:
            print(f"   ok  {name}")
    print("\n" + "=" * 76)
    if total:
        print(f"{total} unknown word(s). REFUSE TO DISPATCH these until they are fixed —")
        print("running one costs a feature; fixing it costs a minute.")
    else:
        print("Every script speaks only words the Sleepwalker knows.")
    print("=" * 76)
    return 1 if total else 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="beat_lint", description=__doc__.split("\n")[1])
    p.add_argument("--beats", action="append", help="lint just this script (repeatable)")
    p.add_argument("--vocab", action="store_true", help="print what the Sleepwalker speaks")
    a = p.parse_args(argv)
    return run(paths=a.beats, show_vocab=a.vocab)


if __name__ == "__main__":
    sys.exit(main())
