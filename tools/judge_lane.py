"""judge_lane.py -- the bake-off judge: one splat in, one alignment score out.

Every lane of the genbear3 bake-off faces the SAME gate so the numbers compare:
  1. tools/http_shots.js screenshots 6 angles (front/right/back/left/top/bottom)
     through the culling-free HTTP viewer (the trusted instrument).
  2. senses.watch (Ollama qwen3.8, local -- the operator's trust condition) reads the
     6 stills BLIND as an ordered sequence.
  3. senses.align scores that reading against the physics's expected reading -- the
     same claim theSeed was proven on: one solid bear, every side present.

Usage:  .venv-gs/Scripts/python.exe tools/judge_lane.py <splat-name-in-viewer-dir> [label]
Exit:   prints a JSON verdict line {label, observed, alignment, pass} and appends it to
        capture/genbear3/bakeoff_results.jsonl (the bake-off ledger -- append-only).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "ChimeraEngine"))
import senses  # noqa: E402

EXPECTED = ("a soft fluffy tan-brown teddy bear against a dark background, seen from EVERY side "
            "-- front, back, left, right, top, bottom -- staying one solid stuffed bear (head, "
            "ears, body, four limbs) at every angle, with no hollow, flat, or missing side")

PHOTO_EXPECTED = ("a photograph of a REAL teddy bear: photographic detail in every view -- "
                  "individual fur strands, lifelike eyes and nose, natural fabric texture, "
                  "believable light and shadow; NOT smooth plastic, NOT a flat-colored blob, "
                  "NOT an obvious 3D render or point cloud")

PHOTO_PROMPT = ("These images show the same 3D object rendered from six controlled angles: "
                "front, right side, back, left side, directly above, directly below. Judge ONLY "
                "this: does it look like a PHOTOGRAPH of a real physical teddy bear? Consider "
                "fur detail, eyes, surface texture, and lighting realism. Say plainly what "
                "betrays it as artificial, if anything. Be concrete and brief. End your answer "
                "with a final line that is EXACTLY 'Verdict: YES' (it passes as a photograph) "
                "or 'Verdict: NO' (it is visibly a render).")


def _photo_verdict(text: str) -> bool | None:
    """The photoreal gate is decided by the eye's OWN verdict line, never by fuzzy alignment --
    the aligner matched 'Verdict: No' answers against PHOTO_EXPECTED at 1.0 (2026-08-19 bug,
    caught on d2_sd15_p2_s0). The eye's words are the terminal; the number was not."""
    if not text:
        return None
    for line in reversed(text.strip().splitlines()):
        low = line.strip().lower()
        if low.startswith("verdict:"):
            return "yes" in low
    return None

WATCH_PROMPT = ("These images show the same 3D object rendered from six controlled angles, in "
                "order: front, right side, back, left side, directly above, directly below. "
                "Describe the object and whether it looks like the SAME solid object from every "
                "angle. Note any side that is hollow, flat, missing, or inconsistent with the "
                "others. Be concrete and brief.")


def main() -> None:
    splat = sys.argv[1]
    label = sys.argv[2] if len(sys.argv) > 2 else Path(splat).stem
    # orient="1" for splats written by cb.save_splat (mesh_to_splat lane): save_splat
    # pre-applies the SPLAT_ORIENT inverse, so the viewer's DEFAULT orientation (which
    # applies SPLAT_ORIENT) shows them upright. DiffSplat/direct conversions use "0".
    orient = sys.argv[3] if len(sys.argv) > 3 else "0"
    out = _ROOT / ".tmp" / f"judge_{label}"
    out.mkdir(parents=True, exist_ok=True)

    shots = subprocess.run(["node", str(_ROOT / "tools" / "http_shots.js"), splat, str(out),
                            "1.9", orient],
                           capture_output=True, text=True, cwd=_ROOT)
    if shots.returncode != 0:
        print(json.dumps({"label": label, "error": f"http_shots failed: {shots.stderr[-300:]}"}))
        sys.exit(1)
    frames = [str(out / f"{v}.png") for v in ("front", "right", "back", "left", "top", "bottom")]

    observed = senses.watch(frames, WATCH_PROMPT)
    if not observed:
        print(json.dumps({"label": label, "error": "the eye is dark (Ollama/qwen3.8 unreachable)"}))
        sys.exit(1)
    alignment = senses.align(EXPECTED, observed)

    # Second gate (the operator's bar, 2026-08-19): PHOTOREALISM, judged separately so the
    # structure score stays comparable across lanes. Same frames, different question.
    photo_observed = senses.watch(frames, PHOTO_PROMPT)
    photo_alignment = senses.align(PHOTO_EXPECTED, photo_observed) if photo_observed else None
    photo_verdict = _photo_verdict(photo_observed)

    verdict = {"label": label, "splat": splat, "observed": observed,
               "alignment": alignment, "pass": (alignment or 0.0) >= 0.6,
               "photo_observed": photo_observed, "photo_alignment": photo_alignment,
               "photo_verdict": photo_verdict,
               "photoreal": bool(photo_verdict)}
    with open(_ROOT / "capture" / "genbear3" / "bakeoff_results.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(verdict) + "\n")
    print(json.dumps(verdict))


if __name__ == "__main__":
    main()
