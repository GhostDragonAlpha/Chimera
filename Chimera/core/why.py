"""
why — the system asks the agent one word, mechanically.

THE HUMAN (2026-07-16): "you need to get the system to guide the agent to be able to ask
these questions automatically, even if we just have to ask one question with one word:
WHY."

They are right, and the proof is the audit that prompted it. Every question that caught
sub-04's hollow feature was the same word:

    "0 red atoms, promoted to tier 1"   -> WHY? -> the atom checks that the file it just
                                                   wrote exists. It is circular.
    "generator loads successfully"      -> WHY? -> loading a module says nothing about
                                                   the C++ it emits.
    "int32 MassCount"                   -> WHY is that a Mass crowd entity? -> it is not.
                                                   Zero Mass framework symbols. (H-21:
                                                   "a verb needs behavior, not metadata"
                                                   — ATool_Shovel had DigRadius and no
                                                   Dig(); ADotCharacter has MassCount and
                                                   no Mass.)

The agent never asked. NOTHING ASKED IT. Not because the answer was hidden — the atom's
probe type is DATA, sitting in the battery file — but because the system reported
"0 red atoms" and stopped, and a green number reads as a proof.

WHY THIS IS NOT ANOTHER GATE, AND MUST NOT BE. It renders no verdict and blocks nothing.
It states what the evidence PROBES and asks what the evidence CANNOT answer. That is the
Paraclete (core/council.py) made deterministic: it convicts, it does not judge, and there
is no LLM in it to fabricate anything. A question has no failure mode — a bad one costs
an afternoon, a bad verdict costs the record.

THE CLASSIFICATION IS THE WHOLE TRICK. Six of the ten probe types prove only that a FILE
OR STRING EXISTS. An agent that writes a file and then runs a probe asking whether the
file exists has measured its own hand. That is not a bug in the probe — a
`tree_contains` atom is a perfectly good regression guard — it is a bug in calling it
PROOF OF BEHAVIOUR.

    python -m core.why --feature ADotCharacter
    python -m core.why --feature X --claim "it is verified"
"""
import argparse
import glob
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# What each probe type ACTUALLY establishes. Not what it is named; what it PROVES.
# EXISTENCE  — a file or a string is on disk. An agent that just wrote the file has
#              proved nothing but its own typing.
# RECORDED   — something was written to the graph. Also a thing an agent can just do.
# DISPATCH   — a beat could run (not that it did, and not that it passed).
# MEASURED   — the world was observed. THIS is the only kind that can prove behaviour.
_PROVES = {
    "glob_nonempty":   ("EXISTENCE", "a file exists"),
    "file_contains":   ("EXISTENCE", "a string exists in a file"),
    "tree_contains":   ("EXISTENCE", "a string exists somewhere in the tree"),
    "tree_lacks":      ("EXISTENCE", "a string does NOT exist (a real negative — but still text)"),
    "json_valid":      ("EXISTENCE", "a file parses as JSON"),
    "file_md5_not":    ("EXISTENCE", "a file differs from a known hash"),
    "beats_registered": ("DISPATCH", "a beat COULD run — not that it did, nor that it passed"),
    "graph_status":    ("RECORDED", "a node carries a status — which an agent wrote"),
    "envelope_axis":   ("MEASURED", "a measured value sits inside a wall"),
    "feel_metric":     ("MEASURED", "a metric was measured from the running game"),
}

_QUESTIONS = {
    "EXISTENCE": "WHY does a file/string existing prove {feature} WORKS? "
                 "You wrote that file. (H-14: a compile is not proof. H-21: a verb needs "
                 "behavior, not metadata.)",
    "RECORDED":  "WHY does a status you recorded prove {feature} works? "
                 "Recording is not measuring.",
    "DISPATCH":  "WHY does a beat being runnable prove {feature} works? "
                 "It has not run here.",
}


def _battery(feature):
    p = os.path.join(ROOT, "docs", "rep_batteries", f"{feature}.json")
    if not os.path.exists(p):
        return None
    d = json.loads(io.open(p, encoding="utf-8").read())
    return d if isinstance(d, list) else (d.get("atoms") or [])


def audit(feature):
    """What does this feature's evidence actually PROBE? Deterministic; no LLM."""
    atoms = _battery(feature)
    if atoms is None:
        return None
    rows, kinds = [], {}
    for a in atoms:
        t = str((a.get("probe") or {}).get("type", "?"))
        kind, means = _PROVES.get(t, ("UNKNOWN", "an unrecognised probe"))
        kinds[kind] = kinds.get(kind, 0) + 1
        rows.append({"id": str(a.get("id"))[:20], "type": t, "kind": kind, "means": means,
                     "desc": str(a.get("desc") or "")[:60]})
    return {"feature": feature, "atoms": rows, "kinds": kinds,
            "measured": kinds.get("MEASURED", 0), "total": len(rows)}


def run(feature, claim=""):
    a = audit(feature)
    if a is None:
        print(f"no rep battery for '{feature}' — nothing to ask about "
              f"(docs/rep_batteries/{feature}.json)")
        return 0
    print("=" * 76)
    print(f"WHY  —  {feature}" + (f"   claim: \"{claim}\"" if claim else ""))
    print("  What your evidence PROBES. Not a verdict; a question.")
    print("=" * 76)
    for r in a["atoms"]:
        print(f"  {r['id']:20} {r['type']:16} {r['kind']:9} -> {r['means']}")
    print()
    tally = ", ".join(f"{v} {k}" for k, v in sorted(a["kinds"].items()))
    print(f"  {a['total']} atom(s): {tally}")
    print(f"  probes that MEASURE the running game: {a['measured']}")
    print()
    if a["measured"] == 0:
        asked = set()
        for kind in a["kinds"]:
            q = _QUESTIONS.get(kind)
            if q and kind not in asked:
                asked.add(kind)
                print(f"  ?  {q.format(feature=feature)}")
        print()
        print("  NOTHING HERE OBSERVED THE GAME. Every green atom above is compatible with")
        print("  a feature that does not work — including one that is only its own name.")
        print("  If you cannot answer the question, the honest evidence is a WITNESS RUN:")
        print(f"     python -m core.beat_lint --beats docs/beats/<x>.beats.json   (lint FIRST)")
        print(f"     python -m core.witness_runner --beats docs/beats/<x>.beats.json "
              f"--session obs_{feature[:20]}")
    else:
        print(f"  {a['measured']} probe(s) measured the running game. Ask of each: does it")
        print(f"  measure what {feature} is FOR, or only that something moved?")
    print("=" * 76)
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="why", description=__doc__.split("\n")[1])
    p.add_argument("--feature", required=True)
    p.add_argument("--claim", default="", help="what you are about to assert")
    a = p.parse_args(argv)
    return run(a.feature, a.claim)


if __name__ == "__main__":
    sys.exit(main())
