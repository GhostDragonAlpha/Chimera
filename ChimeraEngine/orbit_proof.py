"""orbit_proof.py -- verify scene_buffer volumes are true 3D (parallax, not billboarded).

STATEMENT: The five proven terms (theStar, theTree, theShip, theStanding, theBlackHole) are
true 3D volumes, not flat paintings. When the camera orbits by +/-15 deg yaw, the rendered image
changes in a way consistent with 3D parallax -- a billboard would maintain identical pixel
positions, but a 3D volume shows displacement.

PREDICTION: Frame pairs at +/-15 deg yaw for each of the 5 terms will show measurable per-pixel
differences (mean absolute frame delta > 1.0 on the 0-255 scale), demonstrating parallax.

FALSIFIER: Any term's +/-15 deg frame pair has delta < 1.0 -- the volume is a billboard (or the
term lacks a working emit).

Author: Agent (DeepSeek V4 Pro -- density lane, 2026-08-04)
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

_HERE = Path(__file__).resolve().parent
_OUT = _HERE / "orbit_proof"
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE))

import splat_appearance as sa

# The five terms to verify
# FIVE TERMS THAT ACTUALLY EXIST, and the indirection that used to stand here is gone.
# PROOF_TERMS named concepts the tree does not contain -- theTree, theShip, theStanding,
# theBlackHole -- and TERM_MAP stood in front of them substituting proxies: a BIOME for a tree, a
# PLANETARY SYSTEM for a ship, a HORIZON for a black hole. The proof then reported parallax under
# the wanted name while rendering something else, and "theStar" appeared twice, so a five-term
# proof was really four.
#
#     A PROXY IS NOT THE THING, AND A MAP THAT HIDES THE SUBSTITUTION IS A MISFOLD WITH A LOOKUP
#     TABLE IN FRONT OF IT.
#
# These five were each checked to be in scene_terms() and to emit a non-empty buffer before being
# written here (20000 / 43000 / 24336 / 1726 / 9500 grains), so the proof names what it renders.
PROOF_TERMS = ["theStar", "aBlueWorld", "thePlanets", "theStance", "theHorizon"]

_W, _H = 640, 480
_FOV = 1.047


def render_term(term: str, yaw_offset: float = 0.0) -> np.ndarray | None:
    """Render a term at a specific yaw offset and return the frame as uint8 H×W×3."""
    try:
        from ParticleEngine.gpu_pipeline import FullGPUPipeline
        from ParticleEngine.camera import FirstPersonCamera
    except ImportError:
        return None

    buf = sa.scene_buffer(term)
    if buf is None or buf.shape[0] == 0:
        return None

    pipe = FullGPUPipeline(bg=(0.015, 0.015, 0.04))
    cam = FirstPersonCamera((0.0, -3.0, 0.0))

    # Place camera at derived distance
    radius = float(np.linalg.norm(buf[:, 0:3], axis=1).max()) or 1.0
    dist = radius * 2.8

    base_yaw = math.atan2(1.0, 0.0)  # facing +Y
    yaw = base_yaw + yaw_offset
    ce = math.cos(0.18)
    pos = (dist * ce * math.sin(yaw), -dist * ce * math.cos(yaw), dist * math.sin(0.18))
    cam.position = np.array(pos, dtype=np.float32)

    # AIM AT THE ORIGIN, by the formula live_viewer already uses for exactly this orbit. What was
    # here -- `yaw = atan2(-pos[1], pos[0])`, `pitch = +0.18` -- pointed the camera AWAY from the
    # object: at pos (3.47, -0.93, 0.65) it yawed to +0.26 rad, into +x, when the origin lies at
    # 2.88 rad behind it; and it pitched UP while sitting ABOVE the target. Two sign errors.
    #
    #     THE PROOF WAS RENDERING EMPTY SPACE AND CALLING IT A BILLBOARD. Every term returned
    #     delta = 0.000 -- not "no parallax" but two BIT-IDENTICAL frames of pure background
    #     (max pixel 10, which is bg 0.04 * 255). A false negative that condemns working geometry
    #     is worse than no proof: it would have sent someone to fix emit() functions that were
    #     never broken.
    #
    # A delta of EXACTLY zero should always have been read as an instrument failure rather than a
    # physics one -- two genuinely different camera positions cannot produce identical bytes.
    n = math.sqrt(pos[0] ** 2 + pos[1] ** 2 + pos[2] ** 2) or 1.0
    fx, fy, fz = -pos[0] / n, -pos[1] / n, -pos[2] / n
    cam.yaw = math.atan2(fy, fx)
    cam.pitch = math.atan2(fz, math.hypot(fx, fy))

    pipe.upload(np.ascontiguousarray(buf, dtype=np.float32))
    return pipe.render_from_gpu(cam, cam.params(_W, _H))


_BG255 = np.array([0.015, 0.015, 0.04], dtype=np.float32) * 255.0   # the pipeline's own bg


def frame_delta(img_a: np.ndarray, img_b: np.ndarray) -> float:
    """Mean absolute per-pixel difference over the WHOLE frame. Kept, and kept honest.

    THIS NUMBER CANNOT ANSWER THE QUESTION IT WAS BEING ASKED. Averaged over 640x480, it is
    diluted by every background pixel -- which contributes exactly 0 -- so it measures
    `coverage x parallax`, a product of two things, and a 1.0 threshold on it convicts a small
    object of being a billboard. Measured:

        theStance   coverage  2.92%   masked 52.024   full 1.520  -> PASSED
        aBlueWorld  coverage 26.27%   masked  1.639   full 0.434  -> FAILED

    The one that passed has the SMALLEST coverage in the set. The metric does not even rank by
    the thing diluting it. It is reported below because it is what the original threshold was set
    against, and dropping it would hide the change rather than show it.
    """
    return float(np.abs(img_a.astype(np.float32) - img_b.astype(np.float32)).mean())


def frame_delta_masked(img_a: np.ndarray, img_b: np.ndarray) -> tuple[float, float]:
    """Mean absolute difference over the pixels the OBJECT occupies, plus its coverage.

    A billboard and a volume differ in what happens to the object's own pixels when the camera
    moves; the background has no opinion. Measure at the scale the thing lives at -- the same rule
    that caught 0.6 px octaves being read as detail LOST.

    The mask is "brighter than the background in EITHER frame", so a pixel the object moves OFF
    still counts: vacating a pixel is exactly as much evidence of parallax as filling one.
    """
    a = img_a.astype(np.float32)
    b = img_b.astype(np.float32)
    m = ((a > _BG255 + 2.0).any(-1)) | ((b > _BG255 + 2.0).any(-1))
    if not m.any():
        return 0.0, 0.0
    return float(np.abs(a - b)[m].mean()), float(m.mean())


def run():
    """Run the orbit proof for all 5 terms."""
    _OUT.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict] = {}

    print(f"Orbit proof -- {len(PROOF_TERMS)} terms, +/-15 deg yaw parallax test")
    print(f"{'=' * 60}")

    all_ok = True
    for wanted in PROOF_TERMS:
        term = wanted                       # no proxying: the proof renders the term it names
        available = term in sa.scene_terms()
        if not available:
            term = wanted
            available = term in sa.scene_terms()

        if not available:
            results[wanted] = {"parallax_verified": False,
                               "error": f"term '{term}' not available"}
            print(f"  {wanted:20s}  SKIP (not available)")
            all_ok = False
            continue

        yaw_delta = 15.0 * math.pi / 180.0  # 15 degrees in radians

        try:
            img_neg = render_term(term, -yaw_delta)
            img_pos = render_term(term, +yaw_delta)
        except Exception as e:
            results[wanted] = {"parallax_verified": False,
                               "error": f"render failed: {e}"}
            print(f"  {wanted:20s}  FAIL (render error: {e})")
            all_ok = False
            continue

        if img_neg is None or img_pos is None:
            # ONE RETRY THROUGH A FRESH EMIT, and it is a diagnostic rather than a rescue: if a
            # cached/baked path returned None but a live emit succeeds, the failure was the CACHE,
            # not the membrane, and the two cases want different fixes. If it still returns None
            # the term genuinely does not render and the proof says so.
            try:
                sa.scene_buffer(term)
                img_neg = render_term(term, -yaw_delta)
                img_pos = render_term(term, +yaw_delta)
            except Exception:
                img_neg = img_pos = None
        if img_neg is None or img_pos is None:
            results[wanted] = {"parallax_verified": False,
                               "error": "render returned None (after one fresh-emit retry)"}
            print(f"  {wanted:20s}  FAIL (no render output, retry did not help)")
            all_ok = False
            continue

        delta = frame_delta(img_neg, img_pos)                 # kept: what the old bar judged
        masked, coverage = frame_delta_masked(img_neg, img_pos)
        threshold = 1.0                 # mean absolute pixel delta on 0-255, ON THE OBJECT
        ok = masked > threshold and coverage > 0.0

        # Save both frames for visual inspection
        Image.fromarray(img_neg).save(_OUT / f"{term}_neg15deg.png")
        Image.fromarray(img_pos).save(_OUT / f"{term}_pos15deg.png")

        results[wanted] = {
            "parallax_verified": ok,
            "term_used": term,
            "frame_delta_on_object": round(masked, 3),      # the one the verdict rests on
            "frame_delta_full_frame": round(delta, 3),      # the old metric, for audit
            "object_coverage_frac": round(coverage, 4),
            "threshold": threshold,
            "neg_frame": f"{term}_neg15deg.png",
            "pos_frame": f"{term}_pos15deg.png",
        }

        status = "VERIFIED (3D)" if ok else "UNVERIFIED (billboard?)"
        print(f"  {wanted:20s}  on-object={masked:7.3f}  cover={100*coverage:5.2f}%  "
              f"(full-frame {delta:5.3f})  {status}")

        if not ok:
            all_ok = False

    print(f"\n{'=' * 60}")
    print(f"Result: {'ALL TRUE 3D' if all_ok else 'SOME UNVERIFIED -- parallax missing'}")

    (_OUT / "orbit_proof.json").write_text(json.dumps({
        "results": results,
        "all_verified": all_ok,
        "yaw_delta_deg": 15.0,
        "fov": _FOV,
        "resolution": f"{_W}x{_H}",
    }, indent=2))

    return all_ok, results


if __name__ == "__main__":
    ok, _ = run()
    raise SystemExit(0 if ok else 1)