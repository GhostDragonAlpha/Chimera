"""
expectation_violator — discover novel fun by BREAKING player mental models.

The idea the two-brain COUNCIL discovered (2026-07-15, core.council): novel fun is
the moment a player's mental model breaks and they must build a NEW one. So the
highest-leverage way for the studio to discover fun ON ITS OWN is not to add more
content, but to take the seed's implied player-behaviour assumptions, GENERATE
rule-modifiers that VIOLATE them, and keep only the ones that create PRODUCTIVE
cognitive friction (a new mental model worth mastering) rather than mere confusion.

This is generate-then-judge, grounded in the real seed:
  1. SYSTEMS   — read the seed's systems from the helm (name + doc).
  2. ASSUMPTION— derive the strongest player mental-model assumption for a system.
  3. VIOLATE   — the FAST brain generates rule-modifiers that break that assumption.
  4. JUDGE     — the DEEP brain (--deep) or the fast brain scores each for PRODUCTIVE
                 friction (new strategy / 'aha') vs mere breakage (confusion/unfair).
  5. KEEP      — survivors are recorded as design candidates (doc + DNA + CAPCOM).

The LLM writes the mechanics; this engine holds the CONSTRAINT ("fun = a mental
model breaks and a better one forms") and the grounding (the real seed). It never
touches the game build — it produces DESIGN CANDIDATES for the conveyor.

  python -m core.expectation_violator run [--systems N] [--per M] [--deep] [--keep S]
  python -m core.expectation_violator show
"""
import argparse
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOG = os.path.join(ROOT, "docs", "EXPECTATION_VIOLATIONS.md")
KEEP_THRESHOLD = 6  # score >= this survives


def _systems(limit=6):
    """Grounded input: the seed's systems (name + doc) via the helm."""
    try:
        from core.helm import vision_gap
        ts = vision_gap().get("targets", []) or []
    except Exception:
        ts = []
    out = []
    for t in ts[:limit]:
        name = t.get("name")
        doc = (t.get("doc") or "").strip()
        if name:
            out.append((name, doc))
    return out


def _fast(prompt, max_tokens=900):
    from core.council import _fast as council_fast
    return council_fast(prompt, max_tokens=max_tokens, agent="violator")


def _deep(prompt, max_tokens=700):
    from core import ds4_brain
    return ds4_brain.chat([{"role": "user", "content": prompt}],
                          max_tokens=max_tokens, temperature=0.4)


def _last_after(marker, raw, minlen=12):
    """Reasoning models echo the prompt's marker early in their thinking, then draft
    the real answer later — so take the LAST substantial match, not the first."""
    hits = [h.strip() for h in re.findall(marker + r"\s*(.+)", raw)
            if len(h.strip()) >= minlen]
    if hits:
        return hits[-1]
    # fallback: last substantial line of the output
    lines = [l.strip() for l in raw.splitlines() if len(l.strip()) >= minlen]
    return lines[-1] if lines else raw.strip()[:200]


def derive_assumption(name, doc):
    p = (f"A game system: {name}\n{doc[:400]}\n\n"
         "In ONE sentence, state the strongest ASSUMPTION a player will form about "
         "how they are 'supposed' to interact with this system — the mental model "
         "they build without thinking. Give your final answer on its own line as "
         "'ASSUMPTION: <the sentence>'.")
    raw = _fast(p, max_tokens=600)
    return _last_after("ASSUMPTION:", raw)[:280]


def generate_violations(name, assumption, n=3):
    p = (f"System: {name}\nPlayer's assumption: {assumption}\n\n"
         f"Generate exactly {n} concrete RULE-MODIFIERS that VIOLATE this assumption "
         "— each a specific mechanic change that breaks the player's mental model and "
         "forces them to build a new one. Be specific and playable (not vague). "
         "Output each on its own line prefixed exactly 'VIOLATION: '.")
    raw = _fast(p, max_tokens=1000)
    seen, vios = set(), []
    for m in re.finditer(r"VIOLATION:\s*(.+)", raw):
        v = m.group(1).strip()
        if len(v) > 25 and v.lower() not in seen:
            seen.add(v.lower())
            vios.append(v)
    if not vios:  # fallback: substantial numbered/bulleted lines
        for l in raw.splitlines():
            s = l.strip(" -*0123456789.").strip()
            if len(s) > 30 and s.lower() not in seen:
                seen.add(s.lower())
                vios.append(s)
    return vios[:n]


def assess(name, assumption, violation, deep=False):
    p = ("You judge a proposed game rule-modifier. GOOD = it forces the player to "
         "abandon an old mental model and build a NEW one that REWARDS MASTERY "
         "(new strategies, an 'aha', emergent depth). BAD = merely confusing, random, "
         "frustrating, or unfair — breaks the game without opening a better one.\n\n"
         f"System: {name}\nPlayer's assumption: {assumption}\nProposed violation: {violation}\n\n"
         "Score the PRODUCTIVE cognitive friction 0-10 (a new model worth mastering, "
         "not mere disruption). Answer exactly:\nSCORE: <0-10>\nVERDICT: KEEP|DISCARD\n"
         "WHY: <1-2 sentences>")
    raw = (_deep(p, max_tokens=700) if deep else _fast(p, max_tokens=700))
    scores = re.findall(r"SCORE:\s*(\d+(?:\.\d+)?)", raw)  # last = the settled score
    score = float(scores[-1]) if scores else -1.0
    whys = re.findall(r"WHY:\s*(.+)", raw)
    return {"score": score, "reasoning": (whys[-1].strip()[:300] if whys else raw[:300])}


def run(n_systems=4, per=3, deep=False, keep=KEEP_THRESHOLD, record=True, echo=True):
    systems = _systems(n_systems)
    if not systems:
        print("no seed systems from the helm — is CHIMERA_VISION.py present?")
        return []
    keepers = []
    for name, doc in systems:
        assumption = derive_assumption(name, doc)
        if echo:
            print(f"\n### {name}\nASSUMPTION: {assumption}", flush=True)
        for vio in generate_violations(name, assumption, per):
            a = assess(name, assumption, vio, deep=deep)
            mark = "KEEP" if a["score"] >= keep else "drop"
            if echo:
                print(f"  [{a['score']:.0f}/10 {mark}] {vio[:110]}", flush=True)
            if a["score"] >= keep:
                keepers.append({"system": name, "assumption": assumption,
                                "violation": vio, "score": a["score"],
                                "why": a["reasoning"]})
    keepers.sort(key=lambda k: -k["score"])
    if record and keepers:
        _record(keepers, deep)
    return keepers


def _record(keepers, deep):
    lines = ["", f"## Run ({'deep' if deep else 'fast'} judge) — {len(keepers)} kept",
             ""]
    for k in keepers:
        lines += [f"### {k['system']}  ({k['score']:.0f}/10)",
                  f"- **assumption:** {k['assumption']}",
                  f"- **violation:** {k['violation']}",
                  f"- **why it works:** {k['why']}", ""]
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        header = ("# Expectation Violations — design candidates\n\n"
                  "> Auto-generated by `core.expectation_violator` (the idea the two-brain "
                  "council found: fun = a player's mental model breaks and a better one "
                  "forms). Each is a rule-modifier that violates a seed assumption and "
                  "scored high for PRODUCTIVE friction. Feed the good ones to the DSL.\n")
        prior = ""
        if os.path.exists(LOG):
            prior = open(LOG, encoding="utf-8").read()
        else:
            prior = header
        open(LOG, "w", encoding="utf-8").write(prior + "\n".join(lines))
    except Exception:
        pass
    try:
        from core.capcom import post_safe
        top = keepers[0]
        post_safe("violator", f"{len(keepers)} expectation-violation candidates kept; "
                  f"top ({top['score']:.0f}/10, {top['system']}): {top['violation'][:90]}",
                  level="note", source="expectation_violator")
    except Exception:
        pass
    try:
        from core.graphify_interface import record_surprise
        for k in keepers[:6]:
            record_surprise(
                context=f"expectation-violation candidate for {k['system']} (score {k['score']:.0f})",
                reality=f"VIOLATE '{k['assumption']}' -> {k['violation']}",
                expectation="the player's assumed mental model for the system",
                source="agent")
    except Exception:
        pass


def show():
    if not os.path.exists(LOG):
        print("no candidates yet — run: python -m core.expectation_violator run")
        return
    print(open(LOG, encoding="utf-8").read())


def main(argv=None):
    p = argparse.ArgumentParser(prog="expectation_violator",
                                description=__doc__.split("\n")[1])
    sub = p.add_subparsers(dest="cmd", required=True)
    pr = sub.add_parser("run")
    pr.add_argument("--systems", type=int, default=4)
    pr.add_argument("--per", type=int, default=3)
    pr.add_argument("--deep", action="store_true", help="judge with the deep brain (ds4, slow)")
    pr.add_argument("--keep", type=int, default=KEEP_THRESHOLD)
    pr.add_argument("--no-record", action="store_true")
    sub.add_parser("show")
    a = p.parse_args(argv)
    if a.cmd == "show":
        show()
        return 0
    t0 = time.time()
    keepers = run(n_systems=a.systems, per=a.per, deep=a.deep, keep=a.keep,
                  record=not a.no_record)
    print(f"\n=== {len(keepers)} candidate(s) kept in {time.time()-t0:.0f}s "
          f"-> docs/EXPECTATION_VIOLATIONS.md ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
