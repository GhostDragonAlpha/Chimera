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
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent
sys.path.insert(0, str(_REPO / "Chimera"))       # reach the real S2b gate
from core.saturation import measure as _measure   # noqa: E402

STATE_PATH = _HERE / "engine_state.json"

# The hierarchy, seeded setting-first from the seed (docs/THE_WORKFLOW.md 9), pinned to where we
# actually are: theStory is DECIDED (ratified), everything under theSolarSystem is open. The engine
# advances from here; its ledger reflects only what is proven THROUGH it, from now on.
_SEED_HIERARCHY = {
    "theStory":       {"parent": None,             "kind": "seed",     "status": "decided", "children": ["theSolarSystem"]},
    "theSolarSystem": {"parent": "theStory",       "kind": "membrane", "status": "open",    "children": ["theStar", "thePlanets", "theSpace", "theLoop"]},
    "theStar":        {"parent": "theSolarSystem", "kind": "membrane", "status": "open",    "children": []},
    "thePlanets":     {"parent": "theSolarSystem", "kind": "membrane", "status": "open",    "children": ["aPlanet"]},
    "aPlanet":        {"parent": "thePlanets",     "kind": "membrane", "status": "open",    "children": ["aScene"]},
    "aScene":         {"parent": "aPlanet",        "kind": "membrane", "status": "open",    "children": []},
    "theSpace":       {"parent": "theSolarSystem", "kind": "membrane", "status": "open",    "children": []},
    "theLoop":        {"parent": "theSolarSystem", "kind": "membrane", "status": "open",    "children": ["theVerbs"]},
    "theVerbs":       {"parent": "theLoop",        "kind": "membrane", "status": "open",    "children": []},
}

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

    # --- helm: the next move, setting-first --------------------------------------
    def next_term(self):
        """The shallowest node not yet proven/decided whose PARENT is proven/decided."""
        h = self.state["hierarchy"]

        def depth(n):
            d = 0
            while h[n]["parent"] is not None:
                n = h[n]["parent"]; d += 1
            return d

        def parent_ready(n):
            p = h[n]["parent"]
            return p is None or h[p]["status"] in ("proven", "decided")

        ready = [n for n, v in h.items()
                 if v["status"] not in ("proven", "decided") and parent_ready(n)]
        ready.sort(key=lambda n: (depth(n), n))
        return ready[0] if ready else None

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
