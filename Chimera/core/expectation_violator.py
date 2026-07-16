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
ARCHIVE = os.path.join(ROOT, "docs", "world", "expectation_map.json")
KEEP_THRESHOLD = 6  # score >= this earns a cell

# ---------------------------------------------------------------------------
# THE BEHAVIOUR SPACE (the human's insight, 2026-07-16: "the choosing of the
# behaviour space - that's what I'm talking about").
#
# This engine used to be an OPTIMISER: generate N, score 0-10, keep >=6, sort. That
# is a leaderboard, and a leaderboard THROWS THE SPACE AWAY - it answers "what is
# best?" when the question was "what is POSSIBLE?".
#
# MAP-Elites instead ILLUMINATES (Mouret & Clune, "Illuminating search spaces by
# mapping elites"): keep the best candidate in EVERY cell of a behaviour space, and
# you get a MAP of the design territory rather than a top-10.
#
# The split that makes this work, and why it escapes the LLM's knowledge ceiling:
#   FITNESS   = "is it good?"      -> productive cognitive friction (score)
#   BEHAVIOUR = "how is it different?" -> these axes
# The LLM picks the AXES (design taste - a small, robust, transferable kind of
# knowledge). SEARCH fills the CELLS (what actually lives at {inversion x deep} -
# which nobody has ever seen). You are not limited by what the model knows EXISTS,
# only by what it knows to CARE ABOUT.
#
# Taste is legal HERE and nowhere else: an axis only says what to measure ALONG,
# never what is good. That keeps "encode physics, not taste" intact for fitness.
#
# A degenerate winner also stops being able to eat the map: it occupies ONE cell.
# ---------------------------------------------------------------------------
FRICTION_KINDS = {
    "inversion":  "the rule does the OPPOSITE of what the player assumes",
    "coupling":   "two things assumed independent turn out to be linked",
    "delay":      "the effect is displaced in time or space from the cause",
    "scarcity":   "a resource assumed free/infinite turns out to be finite",
    "agency":     "something assumed inert/controlled acts on its own",
    "identity":   "a thing assumed to be one kind is actually another",
}
# THE SECOND AXIS MUST BE ORTHOGONAL TO FITNESS. The first attempt used
# mastery_depth (0=trick..3=system) and the map stayed EMPTY: fitness is "productive
# friction that rewards MASTERY", so depth WAS fitness wearing a hat. --fill dutifully
# asked for depth-0 ("surprises once, nothing to master") and the judge scored it 0/10
# for having nothing to master. Half the space was unfillable BY CONSTRUCTION.
#
# That is the literature's warning, met head-on in one run: "the alignment between
# quality measures and behaviour descriptors impacts algorithmic performance". An axis
# that correlates with quality collapses the archive back into a leaderboard.
#
# SCOPE is orthogonal: a brilliant violation can be local, and a terrible one global.
DEPTH_BANDS = {
    0: "local - changes ONE interaction/verb; the rest of the game is untouched",
    1: "system - changes how one whole subsystem behaves (movement, weather, audio)",
    2: "global - changes a rule the player carries into EVERY system",
}


def _cells():
    return [(k, d) for k in FRICTION_KINDS for d in DEPTH_BANDS]


class Archive:
    """MAP-Elites archive: the best candidate per (friction_kind, mastery_depth).

    ACCUMULATES across runs - that is the point. A leaderboard is rewritten every
    night; a map gets filled in. Coverage and QD-score are the standard illumination
    metrics: coverage says how much territory you have SEEN, QD-score says how good
    it is overall. Rising score with flat coverage = converging, not exploring."""

    def __init__(self, cells=None):
        self.cells = cells or {}          # "kind|depth" -> candidate dict

    @staticmethod
    def load():
        try:
            with open(ARCHIVE, encoding="utf-8") as f:
                return Archive(json.load(f).get("cells", {}))
        except Exception:
            return Archive()

    def save(self):
        try:
            os.makedirs(os.path.dirname(ARCHIVE), exist_ok=True)
            with open(ARCHIVE, "w", encoding="utf-8") as f:
                json.dump({"cells": self.cells, "coverage": self.coverage(),
                           "qd_score": self.qd_score()}, f, indent=1)
        except Exception:
            pass

    def insert(self, cand):
        """Elitist insert: a cell keeps only its best. Returns 'new'|'improved'|''."""
        key = f"{cand['kind']}|{cand['depth']}"
        cur = self.cells.get(key)
        if cur is None:
            self.cells[key] = cand
            return "new"
        if cand["score"] > cur["score"]:
            self.cells[key] = cand
            return "improved"
        return ""

    def coverage(self):
        return round(len(self.cells) / max(1, len(_cells())), 3)

    def qd_score(self):
        return round(sum(c["score"] for c in self.cells.values()), 1)

    def empty(self):
        return [c for c in _cells() if f"{c[0]}|{c[1]}" not in self.cells]


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


# The violator is NOT in a council dialogue - it wants ONE answer in a fixed format.
# Reusing council._fast's persona (FAST_SYS: "you are one of two minds... think
# together with the DEEP mind") made the model draft, deliberate, and echo the persona
# back as a candidate. The system prompt IS the fix; the regex filters are the net.
VIOLATOR_SYS = (
    "You are a precise game-design analyst. Answer ONLY in the exact output format "
    "requested - nothing else. Do NOT show your reasoning, do NOT draft alternatives, "
    "do NOT restate or quote the instructions, do NOT address anyone. Every line you "
    "emit must be a real answer, never a label, a placeholder, or a step in your "
    "thinking.")


# H-3, THE HARD WAY (2026-07-16). Every candidate scored exactly 3.0 -- the DISCARD
# fallback -- and the raw output showed why: this is a REASONING model that thinks IN
# the output. At max_tokens=800 it opened with "Thinking Process:", reasoned its way to
# "Let's go with 8", and was CUT OFF before emitting its answer block. The only DISCARD
# left in the buffer was the echoed answer template, so the judge graded its own
# instructions. It had decided 8/10 and never got to say it.
#
# H-3 says a reasoning dump is a RETRY WITH A LARGER BUDGET, never a verdict. The
# telling detail: no prompt instruction stops the thinking (VIOLATOR_SYS says "do NOT
# show your reasoning" and it reasons anyway) -- only headroom does. max_tokens is a
# CEILING, not a target: a model that finishes in 300 tokens still costs 300, so this
# is paid only by the calls that were being truncated. Uniform scores = starvation.
_BUDGET = int(os.environ.get("CHIMERA_LM_MAX_TOKENS", "8192"))


def _fast(prompt, max_tokens=None):
    from core.council import _fast as council_fast
    return council_fast(prompt, max_tokens=max_tokens or _BUDGET, agent="violator",
                        system=VIOLATOR_SYS)


def _deep(prompt, max_tokens=None):
    # ds4 is a REASONING model too - CLAUDE.md: "give `ask` a large --max-tokens or it
    # stops mid-think". Same starvation bug, slower to notice at ~1.6 t/s.
    max_tokens = max_tokens or _BUDGET
    from core import ds4_brain
    return ds4_brain.chat([{"role": "user", "content": prompt}],
                          max_tokens=max_tokens, temperature=0.4)


_PLACEHOLDER = re.compile(r"<|the sentence|the modifier|the assumption|specific mechanic|"
                          r"thinking process|1-2 sentences|analyze the request", re.I)

# The model ECHOES its instructions before answering, and the longer the prompt the
# more it echoes. A hand-written blocklist is the WRONG SHAPE for this: every prompt
# edit opens a new leak, and it was patched by hand three times (the --fill aim came
# back as a candidate; then the anti-echo system prompt itself came back). So DERIVE
# the filter from what was actually sent - any candidate sharing a long word-run with
# the prompt IS the prompt returning. No list to maintain, and it catches leaks nobody
# thought of.
_ECHO_N = 6


def _echoes(text, *sources):
    """True if `text` shares an N-word run with anything we sent the model."""
    tw = text.lower().split()
    if len(tw) < _ECHO_N:
        return False
    runs = set()
    for src in sources:
        w = (src or "").lower().split()
        runs.update(" ".join(w[i:i + _ECHO_N]) for i in range(len(w) - _ECHO_N + 1))
    return any(" ".join(tw[i:i + _ECHO_N]) in runs
               for i in range(len(tw) - _ECHO_N + 1))


# Kept as a cheap first pass for the short, recurring boilerplate that `_echoes` can
# miss when the model paraphrases rather than quotes.
_ECHO = re.compile(r"aim at an unexplored|unexplored region|design map|rule-modifier|"
                   r"generate exactly|output each|player's assumption|own line prefixed|"
                   r"be specific and playable|violations \(the|nothing has explored|"
                   r"no other text|drafting alternatives|fast worker|deep mind", re.I)


def _ok(h):
    """A substantial line of real answer — not a template echo, a numbered
    reasoning-step header ('5. **Draft...'), or a bare header (ends in ':')."""
    h = h.strip()
    return (len(h) >= 12 and not _PLACEHOLDER.search(h)
            and not re.match(r"^\d+[.)]\s", h) and not h.rstrip("* ").endswith(":"))


def _last_after(marker, raw, minlen=12):
    """Reasoning models echo the prompt's marker (and its <placeholder>) early in
    their thinking, then draft the real answer later — so take the LAST substantial,
    non-echo, non-step-header match."""
    hits = [h.strip() for h in re.findall(marker + r"\s*(.+)", raw) if _ok(h)]
    if hits:
        return hits[-1]
    lines = [l.strip() for l in raw.splitlines() if _ok(l)]
    return lines[-1] if lines else raw.strip()[:200]


def derive_assumption(name, doc):
    p = (f"A game system: {name}\n{doc[:400]}\n\n"
         "In ONE sentence, state the strongest ASSUMPTION a player will form about "
         "how they are 'supposed' to interact with this system — the mental model "
         "they build without thinking. Give your final answer on its own line as "
         "'ASSUMPTION: <the sentence>'.")
    raw = _fast(p)
    return _last_after("ASSUMPTION:", raw)[:280]


def generate_violations(name, assumption, n=3, target=None):
    """`target`=(kind, depth) aims the generator at an EMPTY cell of the map.

    This is the move a leaderboard cannot make. A top-10 list has no idea what it is
    missing; an archive knows exactly which regions are dark and can send the
    generator there. Illumination, not optimisation."""
    aim = ""
    if target:
        k, d = target
        aim = (f"\n\nAIM AT AN UNEXPLORED REGION of the design map: make them "
               f"{k.upper()} violations ({FRICTION_KINDS[k]}), at scope {d} "
               f"({DEPTH_BANDS[d]}). Nothing has explored this region yet.")
    p = (f"System: {name}\nPlayer's assumption: {assumption}\n\n"
         f"Generate exactly {n} concrete RULE-MODIFIERS that VIOLATE this assumption "
         "- each a specific mechanic change that breaks the player's mental model and "
         "forces them to build a new one. Be specific and playable (not vague). "
         "Output each on its own line prefixed exactly 'VIOLATION: '." + aim)
    raw = _fast(p)
    seen, vios = set(), []

    def _real(v, minlen):
        return (len(v) > minlen and v.lower() not in seen
                and not _ECHO.search(v) and not _echoes(v, p, VIOLATOR_SYS))

    for m in re.finditer(r"VIOLATION:\s*(.+)", raw):
        v = m.group(1).strip()
        if _real(v, 25):
            seen.add(v.lower())
            vios.append(v)
    if not vios:  # fallback: substantial numbered/bulleted lines
        for l in raw.splitlines():
            s = l.strip(" -*0123456789.").strip()
            if _real(s, 30):
                seen.add(s.lower())
                vios.append(s)
    return vios[:n]


def assess(name, assumption, violation, deep=False):
    """Score the candidate AND place it in the behaviour space.

    Placement rides the SAME LLM call as the score - so the archive costs nothing
    extra over the old leaderboard, and returns a map instead of a list. (With no
    simulator to derive descriptors from, the model is the placer; cf. QD-through-AI-
    feedback. When a surrogate sim exists, DERIVE these instead - a measured
    descriptor beats a judged one.)"""
    kinds = "\n".join(f"  {k}: {v}" for k, v in FRICTION_KINDS.items())
    depths = "\n".join(f"  {d}: {v}" for d, v in DEPTH_BANDS.items())
    p = ("You judge a proposed game rule-modifier. GOOD = it forces the player to "
         "abandon an old mental model and build a NEW one that REWARDS MASTERY "
         "(new strategies, an 'aha', emergent depth). BAD = merely confusing, random, "
         "frustrating, or unfair - breaks the game without opening a better one.\n\n"
         f"System: {name}\nPlayer's assumption: {assumption}\nProposed violation: {violation}\n\n"
         "Score the PRODUCTIVE cognitive friction 0-10 (a new model worth mastering, "
         "not mere disruption). Then CLASSIFY it.\n\n"
         f"KIND - how is the mental model broken? Pick exactly one:\n{kinds}\n\n"
         f"SCOPE - how much of the game does it reach? Pick one number:\n{depths}\n\n"
         "Answer exactly:\nSCORE: <0-10>\nKIND: <one word from the list>\n"
         "SCOPE: <0-2>\nVERDICT: KEEP|DISCARD\nWHY: <1-2 sentences>")
    raw = (_deep(p, max_tokens=_BUDGET) if deep else _fast(p))
    # STRIP THE ECHOED ANSWER TEMPLATE BEFORE PARSING. The model repeats the format
    # spec back ("SCORE: <0-10>", "VERDICT: KEEP|DISCARD") and the parsers below read
    # it as an answer: "<0-10>" has no digits so SCORE never matched, then the literal
    # word DISCARD in the echoed template hit the fallback ladder - so EVERY candidate
    # scored exactly 3.0 (the DISCARD default) and the judge was grading its own
    # instructions instead of the mechanic. Uniform scores are the fingerprint.
    raw = "\n".join(l for l in raw.splitlines()
                    if "KEEP|DISCARD" not in l and "<0-10>" not in l
                    and "<0-2>" not in l and "<one word" not in l
                    and "<1-2 sentences>" not in l)
    # SCORE is the critical parse (a miss drops the candidate). Try, in order: an
    # explicit "SCORE: N", any "N/10", then fall back to the KEEP/DISCARD verdict.
    scores = (re.findall(r"SCORE:\s*(\d+(?:\.\d+)?)", raw)
              or re.findall(r"(\d+(?:\.\d+)?)\s*/\s*10", raw))
    if scores:
        score = float(scores[-1])
    elif re.search(r"\bKEEP\b", raw, re.I) and not re.search(r"\bDISCARD\b", raw, re.I):
        score = 7.0
    elif re.search(r"\bDISCARD\b", raw, re.I):
        score = 3.0
    else:
        score = -1.0
    # WHY: last substantial non-placeholder match (reject prompt echoes like
    # "<1-2 sentences>" and reasoning headers like "Thinking Process:").
    reasoning = _last_after("WHY:", raw, minlen=20)
    # COORDINATES. A candidate the model won't place is still real: it lands in the
    # nearest legible cell rather than being dropped, and the fallbacks are the most
    # conservative reading (a plain inversion, a shallow trick) so an unplaced
    # candidate can never squat in a deep cell it didn't earn.
    kind = ""
    for m in re.finditer(r"KIND:\s*([A-Za-z]+)", raw):
        k = m.group(1).strip().lower()
        if k in FRICTION_KINDS:
            kind = k
    if not kind:
        hits = [k for k in FRICTION_KINDS if re.search(rf"\b{k}\b", raw, re.I)]
        kind = hits[-1] if hits else "inversion"
    dhits = re.findall(r"SCOPE:\s*([0-2])", raw)
    depth = int(dhits[-1]) if dhits else 0
    return {"score": score, "reasoning": reasoning[:300], "kind": kind, "depth": depth}


def render_map(arc):
    """The archive as a grid - the whole point of the rewrite. A leaderboard says
    'here are the 4 best'; this says 'here is the territory, and here is what is
    still DARK'."""
    w = max(len(k) for k in FRICTION_KINDS) + 2
    out = ["".ljust(w) + "".join(f"   scope{d}" for d in DEPTH_BANDS)]   # 9 per column
    for k in FRICTION_KINDS:
        row = k.ljust(w)
        for d in DEPTH_BANDS:
            c = arc.cells.get(f"{k}|{d}")
            row += f"  {c['score']:>4.0f}/10" if c else "      .  "     # 9 either way
        out.append(row)
    out.append(f"\ncoverage {len(arc.cells)}/{len(_cells())} cells ({arc.coverage()*100:.0f}%)"
               f"   QD-score {arc.qd_score()}")
    return "\n".join(out)


def run(n_systems=4, per=3, deep=False, keep=KEEP_THRESHOLD, record=True, echo=True,
        fill=False):
    """Illuminate the space of ways to break a player's mental model.

    Was: generate -> score -> keep the top few (an optimiser; the space was discarded
    every night). Now: generate -> score AND place -> elitist insert per cell, an
    archive that ACCUMULATES across runs. Same LLM calls, a map instead of a list."""
    systems = _systems(n_systems)
    if not systems:
        print("no seed systems from the helm - is CHIMERA_VISION.py present?")
        return []
    arc = Archive.load()
    cov0, qd0 = arc.coverage(), arc.qd_score()
    kept = []
    for i, (name, doc) in enumerate(systems):
        assumption = derive_assumption(name, doc)
        target = None
        if fill:
            empties = arc.empty()
            target = empties[i % len(empties)] if empties else None
        if echo:
            aim = f"  -> aiming at empty cell {target[0]}|scope{target[1]}" if target else ""
            print(f"\n### {name}{aim}\nASSUMPTION: {assumption}", flush=True)
        for vio in generate_violations(name, assumption, per, target=target):
            a = assess(name, assumption, vio, deep=deep)
            cand = {"system": name, "assumption": assumption, "violation": vio,
                    "score": a["score"], "why": a["reasoning"],
                    "kind": a["kind"], "depth": a["depth"]}
            verdict = arc.insert(cand) if a["score"] >= keep else ""
            if verdict:
                kept.append(cand)
            if echo:
                tag = {"new": "NEW CELL", "improved": "IMPROVED", "": "drop"}[verdict]
                print(f"  [{a['score']:.0f}/10 {a['kind']}|s{a['depth']} {tag}] {vio[:88]}",
                      flush=True)
    arc.save()
    if echo:
        print(f"\n{render_map(arc)}")
        print(f"\nillumination: coverage {cov0*100:.0f}% -> {arc.coverage()*100:.0f}%,"
              f"  QD-score {qd0} -> {arc.qd_score()}")
        if arc.empty():
            e = arc.empty()[:3]
            print("still dark: " + ", ".join(f"{k}|s{d}" for k, d in e)
                  + (f" (+{len(arc.empty())-3} more)" if len(arc.empty()) > 3 else "")
                  + "   -> `run --fill` aims there")
    if record and kept:
        _record(kept, deep, arc)
    return kept


def _record(keepers, deep, arc=None):
    lines = ["", f"## Run ({'deep' if deep else 'fast'} judge) - {len(keepers)} cell(s) claimed",
             ""]
    if arc is not None:
        lines += ["```", render_map(arc), "```", ""]
    for k in keepers:
        lines += [f"### {k['system']}  ({k['score']:.0f}/10)  `{k.get('kind')}|scope{k.get('depth')}`",
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
    pr.add_argument("--fill", action="store_true",
                    help="aim the generator at EMPTY cells of the map (illumination)")
    pr.add_argument("--no-record", action="store_true")
    sub.add_parser("show")
    sub.add_parser("map", help="print the archive: what is explored, what is still dark")
    a = p.parse_args(argv)
    if a.cmd == "show":
        show()
        return 0
    if a.cmd == "map":
        arc = Archive.load()
        print(render_map(arc))
        if arc.empty():
            print("\nstill dark:")
            for k, d in arc.empty():
                print(f"  {k}|scope{d}   ({FRICTION_KINDS[k]}; {DEPTH_BANDS[d]})")
        return 0
    t0 = time.time()
    keepers = run(n_systems=a.systems, per=a.per, deep=a.deep, keep=a.keep,
                  record=not a.no_record, fill=a.fill)
    print(f"\n=== {len(keepers)} cell(s) claimed in {time.time()-t0:.0f}s "
          f"-> docs/EXPECTATION_VIOLATIONS.md + docs/world/expectation_map.json ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
