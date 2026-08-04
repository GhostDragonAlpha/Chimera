"""human_messenger.py -- THE HUMAN SIDE of a dyadAnalysis (a TERM, not a number).

The physics side produces a NUMBER (convergence.py, from the law). The human side produces a TERM: a
SEPARATE vision LLM (LM Studio, adopting whatever the operator loaded) LOOKS at the render -- BLIND to
the physics number -- and says what it sees. A cross-reference then scores the ALIGNMENT between the
physics's expected reading and the human's observed reading, 0.0 -> 1.0.

Two genuinely different systems: one turns the LAW into words, the other turns the PIXELS into words,
neither seeing the other. They can only align if the render truly carries the physics -- a
blue-painted star reads "blue" and the alignment collapses. That is the dyad convergence.py could
never be (it read pixels back into a number, one domain measuring itself).

THE OPERATOR'S RULES (2026-07-25), and they are hard:
  1. No vision model resident -> the human eye is DARK -> the dyadAnalysis FAILS. Not a skip, not
     "unavailable" -- a FAIL. Half a dyad is a monad, and a monad is not proof.
  2. The human is the ARBITER. If the vision reading does NOT match the physics, you do not doubt the
     human -- you ASSUME THE PHYSICS ARE WRONG and START THE PROCESS OVER (redo the render/physics).
     The render must be legible to a mind as the thing it claims to be, or the thing is wrong.

Transport: the shared `senses` layer -- ONE Omni model (qwen2.5-omni) on a dedicated llama-server that
sees, hears, and watches movies, so the operator's LM Studio is left free for their own dev agent. If the
senses server is down the eye is DARK -- a FAIL, the honest outcome (start it: ChimeraEngine/serve_senses).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (_HERE, _HERE.parent / "Chimera"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import senses                                                  # the unified Omni perception (eye/ear/movie)

# The physics's EXPECTED reading, in words -- derived from each term's LAW (deterministic, never from
# the pixels). The cross-reference aligns THIS against the vision LLM's blind reading of the render.
PHYSICS_READING = {
    "theStar": "a single warm yellow-white star or sun, glowing softly, with a bright white-hot core; "
               "NOT blue, NOT red or orange",
    "theSolarSystem": "a bright star at the CENTER with planets on rings or orbits around it; the "
                      "brightest thing sits in the middle",
    "thePlanets": "a set of planets running from hot colors (red, orange) on one side to cold colors "
                  "(blue, then white/frozen) on the other -- a temperature gradient across the worlds",
    "aPlanet": "a single planet seen from space: blue oceans, green continents of land, and white "
               "polar ice caps -- a living habitable world like Earth",
    "theTerrain": "a spherical world's solid surface seen from space with rugged, uneven RELIEF: large "
                  "dark-blue low basins, green lowland, and tan-and-brown higher ground -- a bumpy "
                  "topographic globe of basins, plains and uplands, not a smooth flat ball",
    "theAtmosphere": "a thin translucent glowing shell or bubble of air with NO solid planet inside "
                     "it -- pale blue-white on the brighter side, reddening to orange-red at the "
                     "day-night edge, dark on the far side, with wispy white cloud streaks; a glowing "
                     "ring of air, not a solid ball",
    "theOcean": "a dark deep-blue water sphere or ocean world with a bright white sun glint on the "
                "day side and white frozen polar regions; NO land, NO clouds -- open ocean alone",
    "theBiomes": "a globe wrapped in horizontal climate BANDS by latitude: white frozen poles, "
                 "dark green forest bands, tan-and-olive dry grassland belts, greener lush band "
                 "near the equator -- a banded climate map, striped not random",
    "theGround": "a small human figure standing upright on a brown patch of stony ground that "
                 "holds it, the patch textured like soil or gravel, floating against a dark "
                 "background -- a person held by the ground",
    "theInterior": "a planet cut open like a diagram: a thin dark rocky crust, a thick red-orange "
                   "glowing mantle, and a bright yellow-white molten metal core at the center -- "
                   "a layered cutaway sphere with a glowing hot center, not a whole planet",
    "theMining": "an open-pit mine seen from above: terraced benches stepping down in rings or a "
                 "spiral to a darker ore floor, in grey-brown rock with a red-brown rusty bottom "
                 "-- a big stepped hole in the ground",
    "theGarden": "a lush green garden or forest full of vegetation, with a prominent tree",
    "theEcosystem": "a green grassy field with trees AND several grazing animals -- deer-like "
                    "herbivores standing among the trees, a living wildlife scene with creatures "
                    "in it, NOT empty land and NOT plants alone",
    "theTree": "a single tree with a brown branching trunk and a spreading green leafy crown "
               "standing on a patch of green ground -- ONE tree alone, NOT a forest, NOT "
               "several trees",
    "theTreeForm": "a stylized tree with a brown trunk and visible brown branches carrying "
                   "green foliage, against a dark black background",
    "theFruit": "a tree with green leaves and round orange-red fruit hanging below the "
                "branches, against a dark background",
    "thePlanting": "a grid of small green dots -- young seedlings -- in straight rows and "
                   "columns at even spacing on a dark ground: a deliberate planted pattern, "
                   "NOT random scatter; the field starts bare and the seedlings appear",
    "theFarming": "a grid of green dots in straight rows and columns with yellow-gold "
                  "dots among them -- a tended crop field whose green plants ripened to "
                  "golden grain heads at harvest -- on a dark textured ground: deliberate "
                  "tended growth, NOT wild random scatter",
    "thePlanetaryFarm": "a grid-like pattern of orange and green spheres on a dark "
                        "textured surface, with scattered green dots outside the grid: "
                        "the ordered grid is a tended farm crop field rooted in a world's "
                        "own open terrain, NOT wild scatter",
    "theLunarFarm": "a circular object with a textured surface against a dark background, "
                    "with a green grid pattern at its center -- a sealed farm dome on a "
                    "barren grey world, the circle is the dome and the grid is the crop "
                    "growing INSIDE, NOT open ground",
    "theOrbitalFarm": "a large ring structure of green and yellow segments against a dark "
                      "starry background with a blue planet below -- a spinning farm ring "
                      "in orbit, the crop band growing along the ring, NOT on a world's "
                      "surface",
    "theSpace": "a starry sky of numerous small white dots against a dark background, "
                "with a few larger circular objects -- distant planets -- suspended among "
                "the stars: deep empty space, the dark medium itself, NO ground or "
                "horizon anywhere",
}

_SEE_PROMPT = ("Look at this image and describe what you actually see in one or two short sentences: "
               "the main colors, the shapes, and what it appears to depict. Describe ONLY what is "
               "visually present. Do NOT mention numbers, temperatures, kelvin, or measurements.")

_WATCH_PROMPT = ("These images are frames from a short video, in order (first to last). Describe what you "
                 "see across the sequence in one or two short sentences: the main colors, the shapes, what "
                 "it depicts, and how it changes from first frame to last. Describe ONLY what is visually "
                 "present. If the frames look nearly the same, say the scene stays the same -- do NOT "
                 "invent changes, blur, focus shifts, or fading that are not clearly visible. Do NOT "
                 "mention numbers, temperatures, or measurements.")


def see(png: str, timeout: int = 300) -> str | None:
    """The human messenger: the Omni EYE reads one render frame BLIND -> a term. None if the eye is dark."""
    return senses.see(png, _SEE_PROMPT, timeout)


def watch(frames: list[str], timeout: int = 360) -> str | None:
    """The Omni eye reads the MOVIE (ordered frames) BLIND -> a term describing the unfolding. None if dark.
    This is the operator's insight made real: the dyad judges the movie, not just the settled end still."""
    return senses.watch(frames, _WATCH_PROMPT, timeout)


def _read(png, timeout: int = 300) -> str | None:
    """Read a render: a MOVIE if given a list of frames (watch), else a single still (see)."""
    return watch(png, timeout) if isinstance(png, (list, tuple)) else see(png, timeout)


def align(expected: str, observed: str, timeout: int = 240):
    """The cross-reference: score how well the human's observed reading matches the physics's expected
    reading, 0.0 -> 1.0 -- the needle where the two independent readings land. Delegates to the shared
    senses layer (the same Omni model). Returns None on failure (-> FAIL)."""
    return senses.align(expected, observed, timeout)


def _notify_operator(term: str, png: str, reason: str) -> None:
    """Guarantee the HUMAN's presence at the decision. When the vision proxy is dark, a silent FAIL
    would let the proof stall unwitnessed -- so PUSH the reason to the operator channel (CAPCOM). A
    human is summoned: they load a model so the proxy can read, or they judge the render themselves.
    Either way a mind is present at the critical decision, which is the whole point of the human side."""
    msg = (f"dyadAnalysis BLOCKED for `{term}`: {reason} The HUMAN is required at this decision -- start the "
           f"senses server (the Omni model on llama-server: ChimeraEngine/serve_senses) so the proxy can read "
           f"the render ({png}), or interpret it yourself. No proof completes until a human (proxy or you) judges it.")
    try:
        from core.capcom import post_safe
        post_safe("human", msg, level="warn", source="dyadAnalysis")
        print(f"[human_messenger] operator SUMMONED via CAPCOM -- `{term}` needs a human.")
    except Exception as e:
        print(f"[human_messenger] CAPCOM unreachable; surfacing for the operator here: {e}\n  {msg}")


def dyad(term: str, png: str, threshold: float = 0.6, human_override: dict | None = None) -> dict:
    """Run the human side + cross-reference for `term`'s render. Verdicts (hard, per the operator):
      PASS         -- alignment >= threshold: the two systems agree, the dyad holds.
      FAIL_RESTART -- the human saw something that does NOT match the physics: ASSUME THE PHYSICS ARE
                      WRONG, redo the render/physics, start over.
      FAIL_NO_HUMAN-- no vision model / the eye is dark: a FAIL, never a skip; the operator is SUMMONED.

    THE OVERRIDE (the operator's rule): a dark eye can be overridden ONLY by the human providing the
    analysis THEMSELVES instead of LM Studio -- pass human_override={"reading": "<what you see>",
    "aligns": True|False (or a 0-1 number)}. The operator IS the human terminal, so their judgment is
    authoritative and needs no LLM judge; taste terminates at the operator."""
    expected = PHYSICS_READING.get(term)
    if not expected:
        return {"verdict": "FAIL", "pass": False, "term": term,
                "detail": f"no physics reading authored for `{term}` yet -- build it before proving"}

    if human_override is not None:                          # OVERRIDE: the operator supplies the human side
        observed = str(human_override.get("reading", "")).strip()
        aligns = human_override.get("aligns", True)
        a = (1.0 if aligns else 0.0) if isinstance(aligns, bool) else max(0.0, min(1.0, float(aligns)))
        source = "operator (direct -- overriding the proxy)"
    else:                                                   # the vision proxy reads BLIND
        source = "vision proxy (omni movie)" if isinstance(png, (list, tuple)) else "vision proxy (omni)"
        observed = _read(png)
        if not observed:
            _notify_operator(term, png, "no vision model is resident (the eye is dark).")
            return {"verdict": "FAIL_NO_HUMAN", "pass": False, "term": term, "expected": expected,
                    "detail": "the human eye is DARK (the senses server is not running). Per the rule this is "
                              "a FAIL, not a skip -- the operator has been SUMMONED via CAPCOM. Start the senses "
                              "server (serve_senses) and re-run, or override with your own reading (human_override)."}
        a = align(expected, observed)
        if a is None:
            _notify_operator(term, png, "the cross-reference could not score (no model / bad output).")
            return {"verdict": "FAIL_NO_HUMAN", "pass": False, "term": term, "expected": expected,
                    "observed": observed, "detail": "cross-reference could not score -- FAIL. Operator SUMMONED via CAPCOM."}

    if a >= threshold:
        return {"verdict": "PASS", "pass": True, "term": term, "expected": expected, "observed": observed,
                "alignment": round(a, 3), "threshold": threshold, "source": source,
                "detail": f"[{source}] saw \"{observed}\"; alignment {a:.3f} >= {threshold} -- the dyad holds."}
    return {"verdict": "FAIL_RESTART", "pass": False, "term": term, "expected": expected, "observed": observed,
            "alignment": round(a, 3), "threshold": threshold, "source": source,
            "detail": (f"[{source}] saw \"{observed}\", which does NOT match the physics; alignment {a:.3f} "
                       f"< {threshold}. ASSUME THE PHYSICS ARE WRONG -- redo the render/physics for "
                       f"`{term}` and start over.")}


if __name__ == "__main__":
    term = sys.argv[1] if len(sys.argv) > 1 else "theStar"
    png = sys.argv[2] if len(sys.argv) > 2 else str(Path(__file__).parent / "output" / f"appear_{term}.png")
    print(f"=== dyad human-side for `{term}` ({png}) ===")
    print(json.dumps(dyad(term, png), indent=2))
