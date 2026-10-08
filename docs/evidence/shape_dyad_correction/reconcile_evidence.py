"""Reconciliation evidence — one blind read, aligned against BOTH candidate expected readings.

Context: two agents converged on the same presentation fix (sigma_frac ~0.35) for theShape's
FAIL_RESTART; the sibling also rewrote the expected reading. This script produces the
decision data: does the legible render satisfy the ORIGINAL reading (voxels/cubes), and/or
the REVISED one (grain texture)? One image call, then text-only align calls. All archived.
"""
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_CE = _HERE.parents[1]
sys.path.insert(0, str(_CE))

import senses

EVIDENCE = _CE.parent / "docs" / "evidence" / "shape_dyad_correction"
IMG = _HERE / "v2_s35_m0_384.png"          # sigma_frac=0.35, tight crop, 384px eye format

OBSERVE_PROMPT = ("Describe what you see in this image: the object, its surface character, "
                  "how it sits on the ground, and the background. Do not guess what it is "
                  "made of beyond what is visible. 2-4 sentences.")

EXPECTED_ORIGINAL = ("a BLOCKY, voxel-built teddy bear -- the same bear as the smooth cloud, "
                     "but made of visible cubes like a 3D cross-stitch -- ROTATING on the spot "
                     "like a turntable inspection over a dim dark ground that stays STILL: one "
                     "solid voxel animal (head, ears, body, limbs) at every angle, front and "
                     "back, NOT hollow, NOT flat, NOT a different object")
EXPECTED_REVISED = ("a brown teddy bear shape built from many small overlapping brown grains "
                    "or soft blobs, forming the same bear as the smooth cloud but with a "
                    "visible grain texture -- ROTATING on the spot like a turntable inspection "
                    "over a dim dark ground that stays STILL: one solid animal (head, ears, "
                    "body, limbs) at every angle, front and back, NOT hollow, NOT flat, NOT a "
                    "different object")


def main():
    print("== reconciliation evidence ==", flush=True)
    obs = senses.see(str(IMG), OBSERVE_PROMPT)
    print("observed:", repr(obs), flush=True)
    rec = {"image": str(IMG), "observe_prompt": OBSERVE_PROMPT, "observed": obs,
           "served_model": senses._last_served_model()}
    if obs:
        a_orig = senses.align(EXPECTED_ORIGINAL, obs)
        a_rev = senses.align(EXPECTED_REVISED, obs)
        rec["align_original_reading"] = a_orig
        rec["align_revised_reading"] = a_rev
        print(f"align vs ORIGINAL (voxel/cubes) reading: {a_orig}", flush=True)
        print(f"align vs REVISED (grain texture) reading: {a_rev}", flush=True)
    (EVIDENCE / "reconciliation_evidence.json").write_text(
        json.dumps(rec, indent=1), encoding="utf8")
    print("archived.", flush=True)


if __name__ == "__main__":
    main()
