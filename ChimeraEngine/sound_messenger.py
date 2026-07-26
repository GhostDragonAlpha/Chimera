"""sound_messenger.py -- THE EAR SIDE of a sound dyadAnalysis (a TERM, from listening).

The twin of human_messenger, for PRESSURE instead of light. `sonify(term)` makes the sound from the term's
physics; the EAR reads it BLIND -> a term; a cross-reference scores the alignment to what the physics
predicts (PHYSICS_HEARING). Two systems: the law turned into a sound, and the sound turned back into words,
neither seeing the other -- they align only if the sonification truly carries the physics.

THE EAR IS HYBRID (the operator's finding, 2026-07-25): there is no reliable audio-recognition model, but
the Omni model (via `senses`, on llama-server) hears at ADVISORY quality. So the AI ear ADVISES; the
OPERATOR is the authoritative ear, always -- sound verification is HUMAN-terminal. A dark ear (senses
server down) is a FAIL and summons the operator, exactly as a dark eye is. The operator's `human_override`
is the terminal, and it needs no model.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (_HERE, _HERE.parent / "Chimera"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import senses                                                  # the unified Omni perception (the ear)
import sonify                                                  # the matter -> pressure generator

_HEAR_PROMPT = ("Listen to this audio clip and describe what you actually hear in one or two short "
                "sentences -- the character and overall pitch of the sound. Describe ONLY what you hear; "
                "do not guess at a source or add details that are not there.")


def hear(wav: str, timeout: int = 300) -> str | None:
    """The AI EAR (advisory): the Omni model listens to the sonification -> a term. None if the ear is dark."""
    return senses.hear(wav, _HEAR_PROMPT, timeout)


def _notify_operator(term: str, wav: str, reason: str) -> None:
    msg = (f"sound dyad BLOCKED for `{term}`: {reason} You are the authoritative EAR -- start the senses "
           f"server (ChimeraEngine/serve_senses) so the advisory ear can listen ({wav}), or judge the sound "
           f"yourself. Sound verification is HUMAN-terminal: no sound proof completes without your ear.")
    try:
        from core.capcom import post_safe
        post_safe("human", msg, level="warn", source="soundDyad")
        print(f"[sound_messenger] operator SUMMONED via CAPCOM -- `{term}` needs your ear.")
    except Exception as e:
        print(f"[sound_messenger] CAPCOM unreachable; surfacing here: {e}\n  {msg}")


def dyad(term: str, out_dir, threshold: float = 0.5, human_override: dict | None = None) -> dict:
    """Sonify `term`, let the EAR read it, cross-reference to the physics. Verdicts:
      PASS            -- the OPERATOR (human_override) heard it and it matches: authoritative.
      PASS_ADVISORY   -- the AI ear agrees (>= threshold), but it is ADVISORY -- the operator confirms.
      FAIL_RESTART    -- what was heard does NOT match the physics: redo the sonification (fix the synthesis).
      FAIL_NO_EAR     -- the ear is dark (senses server down): a FAIL, the operator is SUMMONED.

    The AI ear is advisory because llama.cpp audio is experimental; the operator is the terminal ear. Pass
    human_override={"reading": "<what you hear>", "aligns": True|False | 0-1} to rule authoritatively."""
    expected = sonify.PHYSICS_HEARING.get(term)
    wav = sonify.sonify(term, out_dir)
    if not expected or not wav:
        return {"verdict": "FAIL", "pass": False, "term": term,
                "detail": f"`{term}` has no soundscape / PHYSICS_HEARING yet -- author it before hearing."}

    if human_override is not None:                             # the operator IS the authoritative ear
        observed = str(human_override.get("reading", "")).strip()
        aligns = human_override.get("aligns", True)
        a = (1.0 if aligns else 0.0) if isinstance(aligns, bool) else max(0.0, min(1.0, float(aligns)))
        source, advisory = "operator (authoritative ear)", False
    else:                                                      # the AI ear reads BLIND (advisory)
        source, advisory = "AI ear (advisory -- omni)", True
        observed = hear(wav)
        if not observed:
            _notify_operator(term, wav, "the senses server is not running (the ear is dark).")
            return {"verdict": "FAIL_NO_EAR", "pass": False, "term": term, "expected": expected, "wav": wav,
                    "detail": "the ear is DARK (senses server down). A FAIL, not a skip -- operator SUMMONED. "
                              "Start serve_senses and re-run, or judge the sound yourself (human_override)."}
        a = senses.align(expected, observed)
        if a is None:
            _notify_operator(term, wav, "the cross-reference could not score.")
            return {"verdict": "FAIL_NO_EAR", "pass": False, "term": term, "expected": expected,
                    "observed": observed, "wav": wav, "detail": "cross-reference could not score -- FAIL. Operator SUMMONED."}

    out = {"term": term, "expected": expected, "observed": observed, "wav": wav, "alignment": round(a, 3),
           "threshold": threshold, "source": source, "advisory": advisory}
    if a >= threshold:
        out["pass"] = True
        out["verdict"] = "PASS_ADVISORY" if advisory else "PASS"
        out["detail"] = (f"[{source}] heard \"{observed}\"; alignment {a:.3f} >= {threshold}"
                         + (" -- ADVISORY; the operator confirms (human_override) to make it authoritative."
                            if advisory else " -- the sound dyad holds."))
    else:
        out["pass"] = False
        out["verdict"] = "FAIL_RESTART"
        out["detail"] = (f"[{source}] heard \"{observed}\", which does NOT match the physics; alignment "
                         f"{a:.3f} < {threshold}. Redo the sonification for `{term}` (fix the synthesis), "
                         f"or judge it yourself (human_override).")
    return out


if __name__ == "__main__":
    term = sys.argv[1] if len(sys.argv) > 1 else "theStar"
    print(json.dumps(dyad(term, Path(__file__).parent / "output"), indent=2))
