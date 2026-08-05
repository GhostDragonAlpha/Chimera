"""test_render_pipeline.py -- the whole path, once per term: emit -> LOD -> upload -> render.

WHY IT EXISTS. Every defect this lane found in two batches was in the SEAM between two working
components, and none of them was visible from either side:

    the camera aimed away from the object      (orbit_proof, then demo -- both rendered background)
    body_radius in local units vs a distance in metres  (LOD collapsed every body to one splat)
    a fixed mip top rung                        (a 16x pop on the one term big enough to show it)
    xfrc_applied acting at the centre of mass   (a tip load half a segment short)

Each was found by a person looking at one thing. Nothing walked the whole path for every term and
asked the only question that catches a seam: DID A PICTURE COME OUT.

A PASS WITHOUT A BASELINE ONLY PROVES A PICTURE CAME OUT. `max_pixel > background` is satisfied by
a frame at 20 as easily as one at 255, so a change that made every membrane ten times darker, or
silently dropped four fifths of a buffer's grains, walked through this test untouched. The baseline
turns "did it draw" into "did it draw WHAT IT DREW LAST TIME".

    python ChimeraEngine/test_render_pipeline.py             # all terms, compared against baseline
    python ChimeraEngine/test_render_pipeline.py --quick     # first 8
    python ChimeraEngine/test_render_pipeline.py --baseline  # RE-RECORD the baseline (see below)
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE))

import splat_appearance as sa
import lod as LOD

W, H = 960, 540           # half res: this walks 42 terms and the question is "did it draw", not speed
FOV = 1.047
_BG = np.array([0.015, 0.015, 0.04], dtype=np.float32) * 255.0
_BG_MAX = float(_BG.max())          # 10.2 -- anything at or below this is bare background
_BASELINE = _HERE / "test_render_baseline.json"

# ── THE REGRESSION BANDS, AND WHY THEY ARE THE WIDTHS THEY ARE ──────────────────────────────────
# These are not round numbers picked for looking reasonable. Each is set above the noise that the
# SAME code produces on the SAME machine across runs, because a band tighter than the instrument's
# own repeatability reports the instrument.
#
#   max_pixel   a uint8 channel maximum on a deterministic buffer with a deterministic camera is
#               REPRODUCIBLE -- it is the same arithmetic every run. 50% is therefore enormously
#               loose for it, and deliberately so: this is a REGRESSION alarm, not a precision
#               check, and the failure it exists to catch (a term that renders "much darker") is a
#               multiple, not a percentage.
#   n_grains    LOD selection depends on `body_radius`, which is data, so this moves only when a
#               membrane's emit changes. 20% catches a dropped subsample; it does not fire on a
#               membrane that gained a few grains.
#
# Frame TIME is deliberately NOT in the baseline. Measured on this box, the identical frame varies
# by +-13% run to run because the 4090 is shared with LM Studio -- a timing baseline here would
# fire on what another process was doing, which is the definition of an alarm nobody reads.
_MAX_PIXEL_DROP = 0.50     # flag if max_pixel falls below 50% of baseline
_GRAIN_DROP = 0.20         # flag if grain count falls more than 20% below baseline


def _aim(cam, dist):
    """Aim at the origin. NOT `atan2(-pos[1], pos[0])`, which is the bug this test exists to catch."""
    pos = (0.0, -dist, 0.0)
    cam.position = np.array(pos, dtype=np.float32)
    n = math.sqrt(sum(p * p for p in pos)) or 1.0
    fx, fy, fz = -pos[0] / n, -pos[1] / n, -pos[2] / n
    cam.yaw = math.atan2(fy, fx)
    cam.pitch = math.atan2(fz, math.hypot(fx, fy))


def _load_baseline() -> dict:
    if not _BASELINE.exists():
        return {}
    try:
        return json.loads(_BASELINE.read_text(encoding="utf8")).get("terms", {})
    except Exception:
        return {}


def _check_regression(term: str, base: dict, n_grains: int, n_lod: int,
                      max_pixel: float, drew: bool) -> list[str]:
    """Compare one term against its recorded baseline. Returns the reasons it REGRESSED.

    THE MISSING-TERM CASE IS NOT A FAILURE. A term absent from the baseline is new, and a new
    membrane failing a test because nobody had measured it yet would make adding one an act of
    breaking the build. It is reported as `new` and recorded on the next `--baseline`.
    """
    b = base.get(term)
    if not b:
        return []
    why = []
    if b.get("drew") and not drew:
        why.append("PREVIOUSLY RENDERED, NOW RENDERS NOTHING (emit or the render path broke)")
    b_mx = float(b.get("max_pixel", 0.0))
    if b_mx > 0 and max_pixel < b_mx * _MAX_PIXEL_DROP:
        why.append(f"max_pixel {max_pixel:.0f} < {100*_MAX_PIXEL_DROP:.0f}% of baseline {b_mx:.0f}")
    b_n = int(b.get("n_grains", 0))
    if b_n > 0 and n_grains < b_n * (1.0 - _GRAIN_DROP):
        why.append(f"n_grains {n_grains} < {100*(1-_GRAIN_DROP):.0f}% of baseline {b_n}")
    return why


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    from ParticleEngine.gpu_pipeline import FullGPUPipeline
    from ParticleEngine.camera import FirstPersonCamera

    record = "--baseline" in argv
    base = {} if record else _load_baseline()
    terms = sa.scene_terms()
    if "--quick" in argv:
        terms = terms[:8]
    pipe = FullGPUPipeline(bg=(0.015, 0.015, 0.04))
    cam = FirstPersonCamera((0.0, -3.0, 0.0))

    print(f"RENDER PIPELINE TEST -- {len(terms)} terms, emit -> LOD -> upload -> render")
    print(f"background max is {_BG_MAX:.1f}; a frame at or below it drew NOTHING")
    print("=" * 100)
    print(f"  {'term':<22s} {'n_base':>8s} {'n_lod':>8s} {'save':>6s} {'maxpx':>6s} "
          f"{'cover':>7s}  result")
    print("-" * 100)

    fails, rows = [], []
    for t in terms:
        buf = sa.scene_buffer(t)
        if buf is None or buf.ndim != 2 or buf.shape[0] == 0:
            print(f"  {t:<22s} {'-':>8s} {'-':>8s} {'-':>6s} {'-':>6s} {'-':>7s}  "
                  f"FAIL: scene_buffer returned {'None' if buf is None else 'empty'}")
            fails.append((t, "no buffer")); continue
        if buf.shape[1] != 28:
            print(f"  {t:<22s}  FAIL: shape {buf.shape}, expected (N,28)")
            fails.append((t, f"shape {buf.shape}")); continue

        R = LOD.body_radius(buf)
        dist = 2.8 * max(R, 1e-6)
        draw = buf
        if LOD.should_lod(buf):
            draw = LOD.lod_switch(buf, dist, H, FOV)
        _aim(cam, dist)
        pipe.upload(np.ascontiguousarray(draw, dtype=np.float32), term=t)
        img = pipe.render_from_gpu(cam, cam.params(W, H))
        mx = float(img.max())
        cov = float(((img.astype(np.float32) > _BG + 2.0).any(-1)).mean())
        save = 100.0 * (1.0 - draw.shape[0] / max(buf.shape[0], 1))

        why = []
        # THE ONE CHECK THAT CATCHES A SEAM: did a picture come out.
        if mx <= _BG_MAX:
            why.append("rendered NOTHING (max pixel == background)")
        # LOD may only ever REDUCE. A level with more grains than the base is a pyramid built wrong.
        if draw.shape[0] > buf.shape[0]:
            why.append(f"LOD grew the buffer {buf.shape[0]} -> {draw.shape[0]}")
        # A ZERO-EXTENT BODY IS EXEMPT FROM THE PICTURE CHECK, and saying so is not a loosened
        # bar -- theZero is r = 0, a point, and "a point projects to nothing" is the correct
        # answer rather than a failure. It is reported so the exemption is visible.
        if R <= 1e-9 and why:
            why = [w for w in why if "NOTHING" not in w] + ["zero-extent body (r=0) -- exempt"]

        # ── THE BASELINE COMPARISON, which is the check the picture test cannot make ────────────
        # `mx > _BG_MAX` answers "did anything draw". It cannot answer "did the SAME thing draw",
        # and every regression worth catching lives in the gap: a term that dims from 255 to 20
        # still passes the first question and fails the second.
        drew_now = mx > _BG_MAX
        regressions = _check_regression(t, base, int(buf.shape[0]), int(draw.shape[0]),
                                        mx, drew_now)
        why += [f"REGRESSION: {r}" for r in regressions]
        status = "" if base.get(t) or record else " [new]"

        ok = not [w for w in why if "exempt" not in w]
        rows.append({"term": t, "n_grains": int(buf.shape[0]), "n_lod": int(draw.shape[0]),
                     "max_pixel": round(mx, 1), "coverage": round(cov, 6),
                     "drew": bool(drew_now), "save": save, "ok": ok})
        print(f"  {t:<22s} {buf.shape[0]:>8d} {draw.shape[0]:>8d} {save:>5.1f}% {mx:>6.0f} "
              f"{100*cov:>6.2f}%  {'ok' + status if ok else 'FAIL: ' + '; '.join(why)}")
        if not ok:
            fails.append((t, "; ".join(why)))

    print("=" * 100)
    drew = sum(1 for r in rows if r["ok"])
    lodded = sum(1 for r in rows if r["save"] > 0.5)
    print(f"  {drew}/{len(terms)} terms rendered a picture | {lodded} took a coarser LOD level "
          f"at default framing")

    if record:
        # THE BASELINE IS WRITTEN ONLY WHEN ASKED FOR, NEVER AS A SIDE EFFECT OF A PASS. A test
        # that re-records its own expectations every run cannot fail: it would rewrite the
        # baseline to whatever it just measured, and the regression it was built to catch would
        # be silently adopted as the new correct answer. This is exactly the falsifier the task
        # named -- "the baseline is identical to the current run, so the test always passes" --
        # and the separation of `--baseline` from the default path is what refuses it.
        payload = {
            "note": ("Recorded by test_render_pipeline.py --baseline. Regenerate ONLY when a "
                     "change to emit/LOD/render is intended; a diff here is the point of the "
                     "file. Frame time is not recorded: it varies +-13% run to run on this box "
                     "because the GPU is shared."),
            "resolution": [W, H], "fov": FOV,
            "bands": {"max_pixel_drop": _MAX_PIXEL_DROP, "grain_drop": _GRAIN_DROP},
            "terms": {r["term"]: {"n_grains": r["n_grains"], "n_lod": r["n_lod"],
                                  "max_pixel": r["max_pixel"], "coverage": r["coverage"],
                                  "drew": r["drew"]} for r in rows},
        }
        _BASELINE.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf8")
        print(f"  BASELINE RECORDED: {_BASELINE.name} ({len(rows)} terms)")
        print("  This run cannot fail a comparison -- it IS the comparison. Run again without")
        print("  --baseline to get a real check.")
    elif not base:
        print("  NO BASELINE FOUND. Run with --baseline once to record one; until then this test")
        print("  only asks 'did a picture come out', which a 90% regression would pass.")
    else:
        missing = [t for t in base if t not in {r['term'] for r in rows}]
        new = [r["term"] for r in rows if r["term"] not in base]
        print(f"  compared against baseline of {len(base)} terms"
              + (f" | {len(new)} NEW (not yet baselined)" if new else "")
              + (f" | {len(missing)} baselined term(s) MISSING from this run: "
                 f"{', '.join(missing[:5])}" if missing else ""))

    if fails:
        print(f"  {len(fails)} FAILURES:")
        for t, w in fails:
            print(f"    {t}: {w}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
