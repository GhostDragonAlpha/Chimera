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

Transport: OpenAI-compatible /v1/chat/completions with a base64 image_url, through core.lm_gateway's
queue + resident-model adoption (never pin, never gate on vision flags -- the operator owns what is
loaded; if it can't see, that is a FAIL, which is the honest outcome).
"""
from __future__ import annotations

import base64
import json
import re
import sys
import urllib.request
from pathlib import Path

_CHIMERA = Path(__file__).resolve().parent.parent / "Chimera"
if str(_CHIMERA) not in sys.path:
    sys.path.insert(0, str(_CHIMERA))

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
    "theGarden": "a lush green garden or forest full of vegetation, with a prominent tree",
}

_SEE_PROMPT = ("Look at this image and describe what you actually see in one or two short sentences: "
               "the main colors, the shapes, and what it appears to depict. Describe ONLY what is "
               "visually present. Do NOT mention numbers, temperatures, kelvin, or measurements.")


def _post(payload: dict, timeout: int):
    """POST an OpenAI-compatible chat request through the gateway (queue + adopt resident model).
    Raises on no-model (resolve_model) or transport error -- callers turn that into a FAIL."""
    from core.lm_gateway import lm_urlopen, resolve_model, LM_BASE
    payload["model"] = resolve_model()                      # adopt whatever is loaded; raises if none
    req = urllib.request.Request(f"{LM_BASE}/v1/chat/completions",
                                 data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with lm_urlopen(req, timeout=timeout, agent="human_messenger") as r:
        return json.load(r)["choices"][0]["message"]["content"]


def see(png: str, timeout: int = 300) -> str | None:
    """The human messenger: a vision LLM reads the render BLIND (no physics context) -> a term.
    Returns None if the eye is dark (no model) or errors -- the caller treats None as a FAIL."""
    try:
        with open(png, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        payload = {"messages": [{"role": "user", "content": [
            {"type": "text", "text": _SEE_PROMPT},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}]}],
            "temperature": 0.2, "max_tokens": 4096}    # reasoning models THINK first (H-3); models here hold >=120k ctx
        return (_post(payload, timeout) or "").strip() or None
    except Exception as e:
        print(f"[human_messenger] vision read FAILED: {e}")
        return None


def _parse_alignment(text: str):
    for tok in re.findall(r"\d+(?:\.\d+)?", text or ""):
        v = float(tok)
        if 0.0 <= v <= 1.0:
            return v
    return None


def align(expected: str, observed: str, timeout: int = 240):
    """The cross-reference: score how well the human's observed reading matches the physics's expected
    reading, 0.0 (no alignment) -> 1.0 (perfect). Neither makes the number nor the term -- it is only
    the needle where they land. Returns None on model/parse failure (-> FAIL)."""
    prompt = (f"A physics model predicts an image should show:\n  \"{expected}\"\n\n"
              f"An independent viewer, who did NOT see that prediction, described the same image as:\n"
              f"  \"{observed}\"\n\n"
              f"Rate how well the viewer's description ALIGNS with the physics prediction, as a single "
              f"number from 0.0 (no alignment) to 1.0 (perfect alignment). Output ONLY the number.")
    try:
        return _parse_alignment(_post({"messages": [{"role": "user", "content": prompt}],
                                       "temperature": 0.1, "max_tokens": 4096}, timeout))  # reasoning model: think, THEN the number
    except Exception as e:
        print(f"[human_messenger] cross-reference FAILED: {e}")
        return None


def _notify_operator(term: str, png: str, reason: str) -> None:
    """Guarantee the HUMAN's presence at the decision. When the vision proxy is dark, a silent FAIL
    would let the proof stall unwitnessed -- so PUSH the reason to the operator channel (CAPCOM). A
    human is summoned: they load a model so the proxy can read, or they judge the render themselves.
    Either way a mind is present at the critical decision, which is the whole point of the human side."""
    msg = (f"dyadAnalysis BLOCKED for `{term}`: {reason} The HUMAN is required at this decision -- load "
           f"a vision-capable model in LM Studio so the proxy can read the render ({png}), or interpret "
           f"it yourself. No proof completes until a human (proxy or you) judges it.")
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
        source = "vision proxy (LM Studio)"
        observed = see(png)
        if not observed:
            _notify_operator(term, png, "no vision model is resident (the eye is dark).")
            return {"verdict": "FAIL_NO_HUMAN", "pass": False, "term": term, "expected": expected,
                    "detail": "the human eye is DARK (no vision model in LM Studio). Per the rule this is "
                              "a FAIL, not a skip -- the operator has been SUMMONED via CAPCOM. Load a "
                              "vision model and re-run, or override with your own reading (human_override)."}
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
