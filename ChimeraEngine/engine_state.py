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

# THE DECLARATION -- loaded from terms_data.py, which gen_decl.py GENERATES from the story's
# ```chimera-terms``` block (Chimera/docs/THE_STORY.md). The STORY is the single source: edit its
# decomposition block, run `python ChimeraEngine/gen_decl.py`, and _DECL -- and the hierarchy and
# THE_TERMS.md that derive from it -- all re-derive. Each entry is (name, parent, terminal, note).
sys.path.insert(0, str(_HERE))
from terms_data import TERMS as _DECL        # noqa: E402

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
    "APPEARANCE MESSENGER": "render(term) -- render its splat movie; the HUMAN DYAD must hold (a vision "
                            "reading aligns with the physics). Disagreement = the render is wrong, redo it",
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
        if not self.path.exists():
            return {"seed": "theStory", "hierarchy": copy.deepcopy(_SEED_HIERARCHY),
                    "current": "theSolarSystem", "terms": {}, "codebook": ["theStory"]}
        return self._reconcile(json.loads(self.path.read_text(encoding="utf-8")))

    def _reconcile(self, state: dict) -> dict:
        """Fold the CURRENT story into a saved ledger without losing a single proof.

        THE STORY IS THE SOURCE OF THE HIERARCHY'S SHAPE (which membranes exist, nested how); the saved
        ledger is the source of PROGRESS (what is proven/decided, plus every term's records). So when the
        operator adds detail under a membrane -- edits THE_STORY.md's decomposition block and re-runs
        gen_decl.py -- the new terms must appear in the LIVE tree while everything already proven stays
        proven. Before this, `_load` returned the saved ledger verbatim and only ever built the tree from
        the story on FIRST creation, so a saved ledger FROZE the old hierarchy and 'just change the story'
        silently did nothing. Fix: rebuild the shape from the story, carry the saved status onto every term
        that still exists, and leave terms/codebook/records untouched. Idempotent -- an unchanged story
        reconciles to itself."""
        saved_h = state.get("hierarchy", {})
        tree = copy.deepcopy(_SEED_HIERARCHY)                     # the shape, straight from the story
        for name, node in tree.items():                          # carry PROGRESS onto the new shape
            if saved_h.get(name, {}).get("status") in ("proven", "decided"):
                node["status"] = saved_h[name]["status"]
        dropped = [n for n, nd in saved_h.items()
                   if n not in tree and nd.get("status") in ("proven", "decided")]
        if dropped:                                              # a proven term the story dropped -- loud, never silent
            print(f"[engine] the story no longer declares proven term(s) {dropped}; their records are "
                  f"kept in `terms`, but they have left the hierarchy")
        state["hierarchy"] = tree
        state["seed"] = "theStory"
        state.setdefault("terms", {})
        state.setdefault("codebook", ["theStory"])
        if state.get("current") not in tree:
            state["current"] = "theSolarSystem"
        return state

    def _save(self) -> None:
        self.path.write_text(json.dumps(self.state, indent=2), encoding="utf-8")

    def reload_world(self) -> str:
        """OPEN THE LEVEL -- reload the story + scenes into the RUNNING engine, no session restart.

        The MCP server holds ONE Engine built at startup, so a changed story (new terms in THE_STORY.md ->
        gen_decl.py -> terms_data.py) or a changed scene would otherwise wait for a full session restart.
        This is our `OpenLevel`: re-read the declaration, rebuild the seed hierarchy, reconcile the live
        ledger (every proof kept), and reload the scene renderer. NOTE: changes to the engine's OWN logic
        (this file) still need a session restart -- you cannot hot-swap the running class, only its data
        and the modules it calls out to."""
        import importlib
        global _DECL, _SEED_HIERARCHY
        import terms_data as _td
        importlib.reload(_td)                                    # the story, recompiled by gen_decl.py
        before = set(_SEED_HIERARCHY)
        _DECL = _td.TERMS
        _SEED_HIERARCHY = _build_hierarchy()                     # the new world shape
        self.state = self._reconcile(self.state)                # fold it in; proofs preserved
        self._save()
        for _mod in ("senses", "sonify", "splat_appearance", "human_messenger", "sound_messenger"):
            try:                                                # scenes, sounds, and the perception layer, too
                importlib.reload(importlib.import_module(_mod))
            except Exception as e:
                print(f"[engine] reload {_mod} skipped: {e}")
        added = sorted(set(_SEED_HIERARCHY) - before)
        proven = sorted(n for n, v in self.state["hierarchy"].items()
                        if v.get("status") in ("proven", "decided"))
        return (f"WORLD RELOADED from the story: {len(_SEED_HIERARCHY)} terms"
                + (f"; {len(added)} NEW -> {added}" if added else "; no new terms")
                + f". Proofs preserved: {proven}. Next: {self.next_action(self.state.get('current') or 'theSolarSystem')}")

    def _term(self, name: str) -> dict:
        return self.state["terms"].setdefault(name, {
            "status": "open", "claim": None, "rounds": [], "classification": {},
            "visual": None, "movie": None, "dyad": None, "decided": None, "proven_at": None})

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
        vis = t.get("visual")
        dyad = t.get("dyad")
        vis_exists = bool(vis) and Path(vis).exists()
        dyad_pass = bool(dyad) and dyad.get("pass") is True
        if not vis_exists:
            vis_detail = "no render yet -- call render to produce the appearance movie"
        elif not dyad:
            vis_detail = "rendered, but the human dyad has not judged it"
        elif dyad_pass:
            vis_detail = f"the DYAD HOLDS -- {dyad.get('detail', '')}"
        else:
            vis_detail = f"the DYAD did not hold [{dyad.get('verdict')}] -- {dyad.get('detail', '')}"
        out.append(("APPEARANCE MESSENGER", vis_exists and dyad_pass, vis_detail))
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

    def render(self, name: str, reading: str = "", aligns: str = "") -> str:
        """Produce the term's APPEARANCE and let the HUMAN DYAD judge it. Rendering is physics: the
        engine renders the term as a Gaussian-splat MOVIE (beginning->end, `splat_appearance.py`; the
        matplotlib `appearance.py` is a placeholder fallback). Then the HUMAN side reads it -- a vision
        LLM looks at the settled frame BLIND and its reading is cross-referenced to the physics
        (`human_messenger.py`) -> an alignment. The physics (a NUMBER) and the human (a TERM) are two
        DIFFERENT systems; a monad (physics reading its own pixels) is not proof. No vision model = the
        operator is summoned; the human disagreeing means the physics is wrong -- start over.
        THE OPERATOR'S OVERRIDE (their rule): pass your own `reading` (what YOU see) + `aligns`
        ('yes'/'no' or 0-1) and the judgment is authoritative -- taste terminates at the operator,
        and the proxy is their proxy, not their superior."""
        import human_messenger
        movie = self._appearance(name)
        if not movie:
            return (f"REFUSED (APPEARANCE): `{name}` has no scene yet -- no splat movie and no "
                    f"placeholder projector. Rendering is physics; author its scene before proving.")
        frame = movie["end"]                                # the SETTLED end state (the record + the gallery still)
        override = None
        if str(reading).strip():
            a = str(aligns).strip().lower()
            val = True if a in ("", "yes", "y", "true", "1") else (False if a in ("no", "n", "false", "0") else a)
            override = {"reading": reading.strip(), "aligns": val}
        dyad = human_messenger.dyad(name, [movie["begin"], frame], human_override=override)   # judge the MOVIE (the unfolding), not just the still
        t = self._term(name); t["visual"] = frame; t["movie"] = movie; t["dyad"] = dyad
        t["status"] = "rendered"; self._save()
        who = "OPERATOR (authoritative eye)" if override else "vision proxy"
        if not dyad.get("pass"):
            return (f"APPEARANCE for `{name}` rendered ({frame}), but the DYAD did not hold "
                    f"[{dyad.get('verdict')}] [{who}]:\n  {dyad.get('detail', '')}")
        return (f"APPEARANCE for `{name}`: splat movie ({movie['begin']} -> {frame}); the DYAD HOLDS [{who}].\n"
                f"  {dyad.get('detail', '')}\nNext: {self.next_action(name)}")

    def hear(self, name: str, reading: str = "", aligns: str = "") -> str:
        """THE SOUND DYAD -- judge a term by EAR (its matter projected into PRESSURE, sonify.py).

        The OPERATOR is the primary, authoritative ear; the AI ear (Omni via senses) is a logged, MEASURED-
        UNRELIABLE second opinion (it hallucinated highs in a pure-bass rumble), so it can never gate a proof
        on its own. To RULE: pass your own `reading` (what YOU hear) and `aligns` ('yes'/'no', or a 0-1
        number) -- that is authoritative. With no reading, it runs the AI advisory ear and records it, but
        that is NOT a proof. Sound is ADDITIVE (it deepens a term; it does not block `prove`)."""
        import importlib
        import sound_messenger
        importlib.reload(sound_messenger)                   # pick up sonify/senses edits live
        override = None
        if str(reading).strip():
            a = str(aligns).strip().lower()
            val = True if a in ("", "yes", "y", "true", "1") else (False if a in ("no", "n", "false", "0") else a)
            override = {"reading": reading.strip(), "aligns": val}
        sd = sound_messenger.dyad(name, _HERE / "output", human_override=override)
        t = self._term(name); t["sound_dyad"] = sd; self._save()
        if sd.get("verdict") == "FAIL":
            return f"SOUND for `{name}`: {sd.get('detail')}"
        who = "OPERATOR (authoritative ear)" if override else "AI ear (ADVISORY -- untrusted; YOU are the real ear)"
        tail = ("" if override else
                "\n  To rule authoritatively: hear(term, reading='<what YOU hear>', aligns='yes'|'no'). "
                "The AI ear is measured-unreliable; your ear is the terminal.")
        return (f"SOUND for `{name}` [{who}] -> {sd.get('verdict')} (align {sd.get('alignment')}).\n"
                f"  heard: \"{sd.get('observed', '')}\"\n  wav: {sd.get('wav')}\n  {sd.get('detail', '')}{tail}")

    def _appearance(self, name: str):
        """The term's appearance: a splat MOVIE (beginning->end) if it has a scene, else the matplotlib
        placeholder. Returns {"begin": path, "end": path} or None. Rendering is physics -- owned here."""
        try:
            import importlib
            import splat_appearance
            # The MCP server is a long-lived process that imported this module at session start; a plain
            # `import` hits the sys.modules cache, so edits to a term's SCENE would never render until a
            # full server restart. Reload each time -- rendering is physics, and the physics must be the
            # code on disk NOW, not whatever was loaded when the session opened. (This is the bug that
            # made a re-authored aPlanet keep rendering as its old blob.)
            importlib.reload(splat_appearance)
            m = splat_appearance.project_movie(name, _HERE / "output")
            if m:
                return m
        except Exception as e:
            print(f"[engine] splat render failed for `{name}`: {e}")
        import appearance
        p = appearance.project(name, _HERE / "output")
        return {"begin": p, "end": p} if p else None

    def decide(self, name: str, ruling: str) -> str:
        t = self._term(name); t["decided"] = ruling; t["status"] = "decided"
        if name in self.state["hierarchy"]:
            self.state["hierarchy"][name]["status"] = "decided"
        if name not in self.state["codebook"]:
            self.state["codebook"].append(name)
        self._save()
        return f"THE HUMAN terminal: `{name}` DECIDED -- \"{ruling}\".  (The one terminal an LLM cannot stand in for.)"

    def prove(self, name: str, via: str = "api") -> str:
        """Attempt to record `name` as proven. `via` names WHICH SYSTEM is proving: 'mcp' = the
        engine system (this call came through the MCP tool surface, an independent system); 'api' =
        the caller's own system (a driver/script holding the Engine class directly). A term counts as
        proven only when it has CROSSED THE BOUNDARY -- been proven through the engine system -- not
        merely in the prover's own system. (The two-messenger law at the process scale: the prover
        and the engine are two systems, and you cannot measure a system with itself.)"""
        gs = self.gates(name)
        report = "\n".join(f"  [{'PASS' if ok else 'FAIL'}] {g}: {d}" for g, ok, d in gs)
        failing = [(g, d) for g, ok, d in gs if not ok]
        if failing:
            g, d = failing[0]
            return (f"PROVE REFUSED for `{name}` -- blocked at {g}.\n{report}\n\n"
                    f"The engine will NOT record `{name}` as proven until every gate passes.\n"
                    f"Do this next: {GATE_FIX.get(g, g)}")
        t = self._term(name); t["status"] = "proven"; t["proven_at"] = _now()
        t["proven_via"] = via
        t["crossed_boundary"] = (via == "mcp") or t.get("crossed_boundary", False)   # once crossed, stays crossed
        if name in self.state["hierarchy"]:
            self.state["hierarchy"][name]["status"] = "proven"
        if name not in self.state["codebook"]:
            self.state["codebook"].append(name)
        self._save()
        if t["crossed_boundary"]:
            head = (f"PROVEN -- dyadAnalysis COMPLETE: `{name}` -- the dyad agrees across the boundary "
                    f"(both systems: the measured PHYSICS/APPEARANCE membrane AND the engine system "
                    f"itself, through the MCP tool). Written to the codebook.")
        else:
            head = (f"PROVEN (a MONAD -- dyadAnalysis INCOMPLETE): `{name}` -- every gate passes, BUT "
                    f"this came via the API (a driver holding the Engine), not through the engine "
                    f"system: one half of the dyad measuring itself. Re-run `prove` through the MCP "
                    f"tool to complete the dyadAnalysis -- a monad is not proof.")
        return f"{head}\n{report}"

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
        L.append("  ([x] dyadAnalysis complete (both systems) · [~] a monad -- your system only,"
                 " boundary NOT crossed · [HUMAN] decided)")
        for n, v in self.state["hierarchy"].items():
            crossed = self.state["terms"].get(n, {}).get("crossed_boundary", False)
            mark = {"proven": "[x]", "decided": "[HUMAN]"}.get(v["status"], "[ ]")
            if v["status"] == "proven" and not crossed:
                mark = "[~]"                         # proven in the caller's own system, not through the engine
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
