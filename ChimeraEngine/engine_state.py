"""ChimeraEngine engine state -- the source of truth the engine OWNS.

This is the hinge. "`term` is proven" is a fact only this module writes, and only after every
PROVE gate passes. Raw tools can touch files, but a term cannot COUNT as proven without going
through prove(), which checks the OWNED state through the gates (S0 frame, provenance, measured
saturation, classify, a real visual, a legal terminal). The engine owns truth; the tool list is
just the door. That is what makes the workflow force the agent instead of ask it.
"""
from __future__ import annotations

import copy
import json
import sys
import time
import zlib
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent
sys.path.insert(0, str(_REPO / "Chimera"))       # reach the real S2b gate
from core.saturation import measure as _measure   # noqa: E402

STATE_PATH = _HERE / "engine_state.json"

# THE DECLARATION -- the SINGLE SOURCE. The terms, named in STORY ORDER (docs/THE_STORY.md), each
# with its terminal ([P] physics measured / [H] the human decided) and a one-line note. Like a
# Python assignment: naming IS declaring, there is no separate step; ORDER is the depth-first proving
# order; and this ONE list is what BOTH the engine's hierarchy AND THE_TERMS.md are built from
# (run gen_terms.py to regenerate the doc). Change the declaration, or the story, and it all
# re-derives. This is the story decomposed into the game.
#            name,             parent,           term, note
_DECL = [
    ("theStory",        None,             "H", "the seed / the timeline"),
    ("theSeed",         "theStory",       "P", "the number + the laws that unfold the world"),
    ("theDeterminism",  "theSeed",        "P", "same seed -> same world, bit-identical"),
    ("theLaws",         "theSeed",        "P", "the trained physics the seed runs under"),
    ("theTruth",        "theSeed",        "P", "every fact reaches physics; the world cannot lie"),
    ("theSolarSystem",  "theStory",       "P", "the setting you fly"),
    ("theStar",         "theSolarSystem", "P", "the yellow hearth"),
    ("thePlanets",      "theSolarSystem", "P", "the worlds in orbit"),
    ("aPlanet",         "thePlanets",     "P", "the world you fall toward"),
    ("theTerrain",      "aPlanet",        "P", "the whole-sphere surface"),
    ("theAtmosphere",   "aPlanet",        "P", "air, sky, weather"),
    ("theOcean",        "aPlanet",        "P", "the water"),
    ("theBiomes",       "aPlanet",        "P", "climate + life bands"),
    ("theGround",       "aPlanet",        "P", "the surface underfoot (matter under boots)"),
    ("theInterior",     "aPlanet",        "P", "layers, ore, caves"),
    ("theGarden",       "aPlanet",        "P", "the lush living place (lushEden)"),
    ("theEcosystem",    "theGarden",      "P", "life cascading from physics"),
    ("theTree",         "theGarden",      "P", "the Tree of Knowledge"),
    ("theTreeForm",     "theTree",        "P", "grown from one genome"),
    ("theFruit",        "theTree",        "H", "knowledge of good and evil"),
    ("thePlanting",     "theGarden",      "P", "the tree grows into the surface (the seam)"),
    ("theSpace",        "theSolarSystem", "P", "the medium you fly (the dark, gravity, scale)"),
    ("theDensityClock", "theSolarSystem", "P", "time leans with mass and speed"),
    ("theShip",         "theStory",       "P", "the player's vessel; the cold start"),
    ("theDescent",      "theStory",       "P", "traversing the scales (the membrane onion; LOD of meaning)"),
    ("theStanding",     "theDescent",     "P", "you stand on real ground, witnessed by contact"),
    ("theBlackHole",    "theDescent",     "P", "the density clock's ceiling; the hole you can't see into"),
    ("theVerbs",        "theStory",       "P", "how you act -- verb over nouns"),
    ("theThrust",       "theVerbs",       "P", "energy -> motion (the density clock)"),
    ("theDig",          "theVerbs",       "P", "into the ground (grain physics)"),
    ("theBalance",      "theVerbs",       "P", "center-of-mass vs center-of-thrust"),
    ("theGrow",         "theVerbs",       "P", "life from energy (logistic)"),
    ("theScan",         "theVerbs",       "P", "read composition (spectral)"),
    ("theNavigate",     "theVerbs",       "P", "orbital mechanics, reach a target"),
    ("theLoop",         "theStory",       "P", "world + player + input -> verbs -> state -> tick"),
    ("thePlayer",       "theLoop",        "P", "the character; presence before action (the Dot)"),
    ("theInput",        "theLoop",        "P", "keystrokes -> verb dials"),
    ("theState",        "theLoop",        "P", "what ticks"),
    ("thePersistence",  "theLoop",        "P", "same seed, same world, forever (save / return)"),
    ("theMeaning",      "theStory",       "H", "deciding what things mean; the gift, your terminal"),
    ("theParadise",     "theMeaning",     "H", "does Eden read as paradise"),
    ("theChoice",       "theMeaning",     "H", "good and evil; the human decides"),
    ("theWorthPlaying", "theMeaning",     "H", "is it a game worth playing"),
    ("theExperience",   "theMeaning",     "H", "the felt whole; understood, not won"),
]

# Terms with substrate already built/measured elsewhere (the ~): prove THROUGH the engine, not from
# scratch. Not part of the hierarchy shape -- a planning note for the generated doc.
BUILT = {
    "theDeterminism", "aPlanet", "theTerrain", "theBiomes", "theGround", "theInterior",
    "theGarden", "theTree", "theTreeForm", "thePlanting", "theDensityClock", "theStanding",
    "theBlackHole", "theVerbs", "theThrust", "theDig", "theBalance", "theGrow", "theLoop",
    "thePlayer", "theState",
}

# The story's movements -> the top-level pillars they open (section headers for the generated doc).
MOVEMENTS = {
    "theSeed":        ("I. The Seed",               "in the beginning, a number -- this universe is true"),
    "theSolarSystem": ("II. Arrival",               "the solar system is the first room (the Garden, Movement IV, grows deep inside it)"),
    "theShip":        ("II. Arrival -- the vessel", "a ship, a cold start, the dark between worlds"),
    "theDescent":     ("III. Descent",              "orbit -> atmosphere -> ground -> grain; stand, dig, scan"),
    "theVerbs":       ("How you act (threads every movement)", "verb over nouns"),
    "theLoop":        ("The loop (threads every movement)",    "world + player + input -> verbs -> state -> tick"),
    "theMeaning":     ("V. The Gift -- meaning",    "the knowledge of good and evil -- you decide what things mean"),
}


def _build_hierarchy():
    h = {n: {"parent": p, "status": ("decided" if p is None else "open"), "children": []}
         for n, p, *_ in _DECL}
    for n, p, *_ in _DECL:
        if p is not None:
            h[p]["children"].append(n)          # children keep declaration order = traversal order
    return h


_SEED_HIERARCHY = _build_hierarchy()

GATE_FIX = {
    "S0 FRAME":        "frame(term, claim)  -- state it as exactly one claim",
    "S2a PROVENANCE":  "question(term, ...) -- discover variables by asking, never declare them",
    "S2b SATURATION":  "question(term, ...) -- keep asking until the discovery curve is over the hump",
    "S3 CLASSIFY":     "classify(term, {var: PHYSICS|THE HUMAN}) -- send each variable to a terminal",
    "VISUAL":          "render(term, path) -- record a REAL rendered image (the play button)",
    "S5 WHY-TERMINAL": "classify each variable to a LEGAL terminal (PHYSICS or THE HUMAN)",
}


def _now() -> float:
    return time.time()


class Engine:
    """The owned state + the gates. The MCP tools are a thin wrapper over this."""

    def __init__(self, path: Path = STATE_PATH):
        self.path = Path(path)
        self.state = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            return json.loads(self.path.read_text(encoding="utf-8"))
        return {"seed": "theStory", "hierarchy": copy.deepcopy(_SEED_HIERARCHY),
                "current": "theSolarSystem", "terms": {}, "codebook": ["theStory"]}

    def _save(self) -> None:
        self.path.write_text(json.dumps(self.state, indent=2), encoding="utf-8")

    def _term(self, name: str) -> dict:
        return self.state["terms"].setdefault(name, {
            "status": "open", "claim": None, "rounds": [], "classification": {},
            "visual": None, "decided": None, "proven_at": None})

    def _vars(self, name: str) -> list:
        seen = []
        for r in self._term(name)["rounds"]:
            for v in r:
                if v not in seen:
                    seen.append(v)
        return seen

    def compression(self, name: str) -> float:
        """MEASURED compression of the term's genome: distinct variables represented per compressed
        byte -- meaning-density. Higher = more world in less data = the smarter, more compressed
        term (compression IS intelligence). 0 while the term has no data. This is what ranks terms
        that have been worked; SOURCE_WEIGHT only breaks ties among fresh ones."""
        t = self.state["terms"].get(name)
        if not t or not t["rounds"]:
            return 0.0
        blob = json.dumps({"claim": t["claim"], "rounds": t["rounds"]}, sort_keys=True).encode()
        return len(self._vars(name)) / max(len(zlib.compress(blob, 9)), 1)

    # --- helm: the next move, DEPTH-FIRST down the declared story order ----------
    def next_term(self):
        """The next term to prove, DEPTH-FIRST: continue a branch already started (a proven node)
        to its bottom before opening a sibling; at a fork, take the MOST COMPRESSED (smartest) open
        child, else the declared story order. Walk the path from the seed to the ground."""
        h = self.state["hierarchy"]
        DONE = ("proven", "decided")

        def dfs(node):
            kids = h[node]["children"]
            for c in kids:                                   # depth: finish started branches first
                if h[c]["status"] in DONE:
                    r = dfs(c)
                    if r:
                        return r
            for c in sorted(kids, key=lambda c: (-self.compression(c), kids.index(c))):
                if h[c]["status"] not in DONE:               # then open the smartest/next child here
                    return c
            return None

        root = self.state["seed"]
        if h[root]["status"] not in DONE:
            return root
        return dfs(root)

    def context(self, name: str) -> list:
        """The path from the seed to `name` -- the accumulated story you carry to work here."""
        h = self.state["hierarchy"]
        if name not in h:
            return [name]
        chain = []
        n = name
        while n is not None:
            chain.append(n)
            n = h[n]["parent"]
        return list(reversed(chain))

    # --- the gates: the PROVE formula, checked against OWNED state ----------------
    def gates(self, name: str) -> list:
        t = self._term(name)
        vs = self._vars(name)
        out = [("S0 FRAME", bool(t["claim"]),
                t["claim"] or "no claim recorded")]
        out.append(("S2a PROVENANCE", len(vs) > 0,
                    f"{len(vs)} variables, each born of a question" if vs else "no variables discovered"))
        if t["rounds"]:
            sat = _measure(t["rounds"])
            out.append(("S2b SATURATION", sat.saturated, sat.verdict))
        else:
            out.append(("S2b SATURATION", False, "no question rounds"))
        unclassified = [v for v in vs if v not in t["classification"]]
        out.append(("S3 CLASSIFY", bool(vs) and not unclassified,
                    "all variables classified" if vs and not unclassified else f"unclassified: {unclassified}"))
        vis = t["visual"]
        vis_ok = bool(vis) and Path(vis).exists()
        out.append(("VISUAL", vis_ok,
                    f"visual at {vis}" if vis_ok else "no rendered visual -- the true measure is SEEING it"))
        why_ok = bool(vs) and all(term in ("PHYSICS", "THE HUMAN")
                                  for term in t["classification"].values())
        out.append(("S5 WHY-TERMINAL", why_ok,
                    "every variable reaches PHYSICS or THE HUMAN" if why_ok else "a variable's terminal is not legal"))
        return out

    def next_action(self, name) -> str:
        if name is None:
            return "the hierarchy is complete at this resolution."
        for g, ok, d in self.gates(name):
            if not ok:
                return f"{GATE_FIX.get(g, g)}   (blocked at {g}: {d})"
        return f"prove({name!r}) -- every gate passes."

    # --- tool verbs (the MCP surface wraps these) --------------------------------
    def frame(self, name: str, claim: str) -> str:
        if len(claim.split(" and ")) > 1 or " AND " in claim:
            return f"REFUSED (S0): a claim must be ATOMIC. '{claim}' looks compound -- split it."
        t = self._term(name); t["claim"] = claim; t["status"] = "framed"
        self.state["current"] = name; self._save()
        return f"S0 FRAME recorded: `{name}` = \"{claim}\".  Next: {self.next_action(name)}"

    def question(self, name: str, question: str, variables: list) -> dict:
        t = self._term(name)
        t["rounds"].append(list(dict.fromkeys(variables)))
        t["status"] = "questioning"; self._save()
        sat = _measure(t["rounds"])
        return {"term": name, "asked": question, "round": len(t["rounds"]),
                "variables_so_far": self._vars(name), "saturation": sat.verdict,
                "saturated": sat.saturated,
                "next": ("classify(...)" if sat.saturated
                         else "keep asking -- the curve is NOT over the hump yet")}

    def classify(self, name: str, assignments: dict) -> str:
        t = self._term(name)
        for v, term in assignments.items():
            if term not in ("PHYSICS", "THE HUMAN"):
                return f"REFUSED (S3): `{term}` is not a terminal. Only PHYSICS or THE HUMAN."
            t["classification"][v] = term
        t["status"] = "classified"; self._save()
        return f"S3 CLASSIFY: {assignments}.  Next: {self.next_action(name)}"

    def render(self, name: str, path: str) -> str:
        if not Path(path).exists():
            return (f"REFUSED (VISUAL): no file at {path}. render records a REAL image "
                    f"(the play button), not a claim. Produce the render first.")
        t = self._term(name); t["visual"] = str(path); t["status"] = "rendered"; self._save()
        return f"VISUAL recorded: `{name}` -> {path}.  Next: {self.next_action(name)}"

    def decide(self, name: str, ruling: str) -> str:
        t = self._term(name); t["decided"] = ruling; t["status"] = "decided"
        if name in self.state["hierarchy"]:
            self.state["hierarchy"][name]["status"] = "decided"
        if name not in self.state["codebook"]:
            self.state["codebook"].append(name)
        self._save()
        return f"THE HUMAN terminal: `{name}` DECIDED -- \"{ruling}\".  (The one terminal an LLM cannot stand in for.)"

    def prove(self, name: str) -> str:
        gs = self.gates(name)
        report = "\n".join(f"  [{'PASS' if ok else 'FAIL'}] {g}: {d}" for g, ok, d in gs)
        failing = [(g, d) for g, ok, d in gs if not ok]
        if failing:
            g, d = failing[0]
            return (f"PROVE REFUSED for `{name}` -- blocked at {g}.\n{report}\n\n"
                    f"The engine will NOT record `{name}` as proven until every gate passes.\n"
                    f"Do this next: {GATE_FIX.get(g, g)}")
        t = self._term(name); t["status"] = "proven"; t["proven_at"] = _now()
        if name in self.state["hierarchy"]:
            self.state["hierarchy"][name]["status"] = "proven"
        if name not in self.state["codebook"]:
            self.state["codebook"].append(name)
        self._save()
        return f"PROVEN: `{name}` written to the codebook by the engine.\n{report}"

    def orient(self) -> str:
        cur = self.state.get("current")
        nxt = self.next_term()
        L = [f"CURRENT TERM: {cur}"]
        if cur:
            L.append("  gate progress:")
            for g, ok, d in self.gates(cur):
                L.append(f"    [{'x' if ok else ' '}] {g}")
        L.append("")
        L.append("HIERARCHY (setting-first from the seed):")
        for n, v in self.state["hierarchy"].items():
            mark = {"proven": "[x]", "decided": "[HUMAN]"}.get(v["status"], "[ ]")
            depth = len(self.context(n)) - 1
            L.append(f"  {'  ' * depth}{mark} {n}")
        L.append("")
        L.append(f"CODEBOOK (proven serials): {self.state['codebook']}")
        L.append("")
        if nxt:
            L.append(f"NEXT MOVE -> term `{nxt}`  (context: {' > '.join(self.context(nxt))})")
            L.append(f"            {self.next_action(nxt)}")
        else:
            L.append("NEXT MOVE -> hierarchy complete at this resolution.")
        return "\n".join(L)
