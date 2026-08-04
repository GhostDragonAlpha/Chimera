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
    "theSeed": "small dots connected by lines to larger circular nodes, with one large "
               "bright node at the center of the network against a dark background -- a "
               "world unfolded from a single origin, every colored node a world attached "
               "to the one central seed",
    "theDeterminism": "two identical networks side by side against a dark background -- "
                      "the same pattern of threads and colored nodes twice, mirror twins "
                      "with every detail matching: one world unfolded twice from the same "
                      "seed, bit-identical, NOT two different worlds",
    "theLaws": "blue dots forming an intricate geometric pattern against a dark "
               "background -- a perfect regular lattice of glowing nodes connected by "
               "straight edges, the same pattern repeating everywhere: pure order, a "
               "rulebook made visible, NOT organic or random",
    "theTruth": "a series of blue spheres connected by golden lines to a textured "
                "grey surface below, against a dark background -- every sphere "
                "anchored to the bedrock by its own chain, nothing floating free: "
                "every fact reaching physics, NO unanchored objects",
    "theShip": "one elongated grey object against a starry black background, much "
               "longer than it is wide, with a bright blue glowing flare at one end "
               "trailing a faint blue plume behind it and a small warm yellow-orange "
               "light at the other end: a vessel under thrust, elongated NOT round, "
               "NOT a planet or moon",
    "theFlight": "a spaceship with a blue exhaust trail flying at the head of a long "
                 "curved line of glowing dots that arcs across a dark starfield -- "
                 "one vessel traveling along a visible curving path, motion made "
                 "visible, NOT a stationary object, NOT a planet",
    "theShipPower": "a bright glowing central sphere encircled by a prominent "
                    "glowing ring, with blue and red glowing lines and elements "
                    "around it, set against a dark starry background -- one "
                    "central source with lines of light routing outward from it "
                    "to the surrounding systems",
    "theShipCombat": "a bright red beam of light running horizontally from left to "
                     "right across a dark starry background, connecting a grey "
                     "elongated object with a glowing blue end on the left to a "
                     "large reddish round object on the right -- energy traveling "
                     "from one object to another",
    "theShields": "a celestial body surrounded by a glowing blue aura, against a "
                  "backdrop of numerous small white stars, with a red object "
                  "resembling a comet touching the aura at one side -- a body "
                  "enclosed in a shell of light with energy stopped at its edge",
    "theWarpDrive": "a dynamic pattern of concentric circles of blue and white dots "
                    "against a dark background, winding around an elongated object "
                    "at the center -- a vessel at the center of space folded into "
                    "a spiral around it",
    "theShipView": "a gray oval object and a bright white glowing dot connected by "
                   "green beams of light, against a dark background of numerous "
                   "small white stars -- the beams fan out from the dot and land "
                   "on the oval, one vantage looking at the vessel",
    "theSalvage": "an irregularly shaped object like an asteroid connected by a "
                  "trail of yellow light to a grey oval object, against a dark "
                  "starry background -- matter moving along the light from the "
                  "irregular object into the oval",
    "theDescent": "a series of concentric squares in various colors -- blue, green, "
                  "yellow -- against a starry black background, nested smaller "
                  "and smaller toward a warm glowing center: a tunnel of scales "
                  "with light at its end",
    "theStanding": "a glowing yellow figure standing upright on a large grey "
                   "textured surface against a dark background, the surface "
                   "beneath its feet lit by the contact -- a body standing on "
                   "real ground, witnessed by the light where it touches",
    "theBlackHole": "a cosmic scene with a black central object surrounded by an "
                    "orange ring and a white halo, set against a backdrop of "
                    "numerous small white dots representing stars in space -- "
                    "the center is total darkness, a hole that no light escapes",
    "theVerbs": "a pale stylized human figure with an outstretched arm on the "
                "left, facing a rising curved path of repeated pale round forms "
                "that brighten along the curve and end in one bright glowing "
                "circle, against a dark rough backdrop -- the same object shown "
                "at each station of its travel, an act of moving made visible",
    "thePlayer": "a single small warm glowing sphere of light held at the "
                 "center of a vast dark field scattered with faint distant "
                 "points -- one presence alone in the dark, before anything "
                 "acts",
    "theEVA": "a large grey panelled hull on the left and a white suited figure "
              "floating free of it in a starfield, connected by one thin golden "
              "tether line, with two faint blue jets behind the figure -- a "
              "spacewalk: nothing under the boots, held only by the tether",
    "theMelee": "two humanoid figures standing close together on dark ground, "
                "the pale one leaning forward with its arm extended, a glowing "
                "golden arc sweeping from behind it into a bright flash against "
                "the darker figure -- a strike landing at arm's reach",
    "theShoot": "a dark sphere on the left firing a bright orange beam across "
                "a dark field into a grey target on the right, with a golden "
                "burst blooming where the beam strikes -- a shot discharged, "
                "its whole flight and impact visible at once",
    "theNavigate": "a blue sphere surrounded by two pale concentric orbit rings "
                   "against stars, with a bright golden elliptical arc leaving "
                   "the inner ring and rising to touch the outer one, a glowing "
                   "craft at the arc's top and a small red target where the arc "
                   "meets the outer ring -- a transfer orbit reaching its target",
    "theScan": "a thin white beam of light striking a grey sphere on the left "
               "and fanning out into colored bands spreading to the right, "
               "red through violet, some bands bright and some dim -- light "
               "split into its colors, the object's composition read in the "
               "pattern of bright and dim",
    "theGrow": "a glowing green S-shaped curve rising from lower left to upper "
               "right over dark ground, with a row of green blades beneath it "
               "growing taller along the same curve -- life rising slowly, "
               "surging, then leveling off as the energy is spent",
    "theDig": "a wide dark earthy ground with a narrow trench cut into it and "
              "a mound of pale freshly-dug grains heaped beside the opening, a "
              "few loose grains scattered nearby -- the ground opened, its "
              "matter piled beside the hole",
    "theDensityClock": "a circular pattern of blue particles against a black background, "
                       "darker with a hint of red at the center -- a field of clocks "
                       "around a mass: time runs fast far out and slow near the middle, "
                       "the dark center is where time stops: time leaning with depth, "
                       "NOT the same everywhere",
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
