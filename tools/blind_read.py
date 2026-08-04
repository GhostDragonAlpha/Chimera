"""The blind read of the second recorded session, as a DRIVER.

Membrane: docs/THE_RECORDED_SESSION_2.md -- "THE BLIND READ, AS A DRIVER". Every piece of
evidence the eye must judge is already on disk in its two native shapes:

    SEE    -- the master sheet and the ten beat sheets (single composite images)
    WATCH  -- stand_on_camera / stand_in_world numbered frame sequences (the movie)

The eye reads everything BLIND through ChimeraEngine/human_messenger (prompts forbid numbers;
the exact prompts are logged so the blind condition is auditable), each reading is
cross-referenced with align() against the recorder's ground truth, and everything is written
verbatim to ChimeraEngine/output/blind_read/<timestamp>/. The signature stays with THE HUMAN:
this driver records readings, it never declares PASS.

Falsifier clause 1: the eye is dark -> exit LOUD, write nothing. A driver that silently passes
with no eye is the instrument defect this project keeps paying for.

Run:  python tools/blind_read.py            # the re-recorded session + both stand sequences
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ChimeraEngine"))

import senses  # noqa: E402  (the unified Omni perception layer; needs ChimeraEngine on sys.path)
import human_messenger  # noqa: E402

SESSION = ROOT / "ChimeraEngine" / "output" / "slice_session_20260804_040936"
STAND_ON_CAMERA = ROOT / "ChimeraEngine" / "output" / "ports" / "stand_on_camera"
STAND_IN_WORLD = ROOT / "ChimeraEngine" / "output" / "ports" / "stand_in_world"
OUT_ROOT = ROOT / "ChimeraEngine" / "output" / "blind_read"

# The PHYSICS side of the dyad: what the recorder's ground truth says each beat shows, phrased
# as a visual term for align(). The eye never sees these -- they are the cross-reference only.
EXPECTED = {
    "sheet_master": "a blocky humanoid figure standing on green ground near a grey rock, "
                    "a small gravel pile, and a patch of grass",
    "beat00": "a blocky figure standing still on green ground",
    "beat01": "a figure walking across green ground toward a grey rock",
    "beat02": "a figure at a grey rock, picking it up",
    "beat03": "a figure walking while carrying a grey rock",
    "beat04": "a figure dropping a grey rock onto the ground",
    "beat05": "a figure walking toward a small pile of gravel",
    "beat06": "a figure walking through a small pile of gravel, grains scattering",
    "beat07": "a figure standing in a patch of grass tufts",
    "beat08": "a figure walking and jumping on green ground",
    "beat09": "a figure on green ground, looking back at a dropped rock and a gravel pile",
    "stand_on_camera": "a humanoid figure standing upright and still, then folding forward "
                       "and collapsing",
    "stand_in_world": "a humanoid figure standing upright on green terrain with a rock nearby, "
                      "then folding forward and collapsing",
}

# Falsifier clause 2: the outgoing prompts must not leak the answer. These words appearing in a
# prompt means the read was not blind.
LEAK_RE = re.compile(r"\d|stone|rock|grass|pile|tuft|beat0|pelvis|slump", re.IGNORECASE)


def _frames(d: Path) -> list[str]:
    return [str(p) for p in sorted(d.glob("frame_*.jpg"))]


def main() -> int:
    if not senses.available():
        # FALSIFIER CLAUSE 1 -- loud, and nothing is written. The human is summoned: load the
        # Omni model (ChimeraEngine/serve_senses) and re-run, or read the sheets yourself.
        print("BLIND READ REFUSED: the senses eye is dark "
              f"({senses.SENSES_URL}). Load the Omni model and re-run; "
              "no verdict is written without a reader.")
        return 2

    out = OUT_ROOT / time.strftime("%Y%m%d_%H%M%S")
    out.mkdir(parents=True)

    items = [("sheet_master", "see", [str(SESSION / "sheet_master.jpg")])]
    for sheet in sorted(SESSION.glob("sheet_beat*.jpg")):
        items.append((sheet.stem.replace("sheet_", ""), "see", [str(sheet)]))
    items.append(("stand_on_camera", "watch", _frames(STAND_ON_CAMERA)))
    items.append(("stand_in_world", "watch", _frames(STAND_IN_WORLD)))

    readings = []
    for key, mode, frames in items:
        prompt = human_messenger._SEE_PROMPT if mode == "see" else human_messenger._WATCH_PROMPT
        leak = LEAK_RE.search(prompt)
        if leak:
            print(f"BLIND READ REFUSED: the {mode} prompt leaks '{leak.group(0)}' -- "
                  "the read would not be blind. Fix the prompt, not the log.")
            return 3
        reading = human_messenger.see(frames[0]) if mode == "see" else human_messenger.watch(frames)
        score = None
        if reading is not None and key in EXPECTED:
            score = human_messenger.align(EXPECTED[key], reading)
        readings.append({"item": key, "mode": mode, "n_frames": len(frames),
                         "expected": EXPECTED.get(key), "reading": reading,
                         "align": score, "prompt": prompt})
        print(f"[{key:16s}] align={score}  {reading}")

    (out / "readings.json").write_text(json.dumps(readings, indent=2), encoding="utf8")
    lines = ["# THE BLIND READ -- second recorded session", "",
             "Every reading verbatim, the recorder's ground truth beside it, the align score.",
             "The signature is THE HUMAN's -- this file records, it does not declare.", ""]
    for r in readings:
        lines += [f"## {r['item']} ({r['mode']}, {r['n_frames']} frame(s))",
                  f"- expected: {r['expected']}",
                  f"- reading:  {r['reading']}",
                  f"- align:    {r['align']}", ""]
    (out / "verdict.md").write_text("\n".join(lines), encoding="utf8")
    print(f"\nreadings -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
