"""terrain_witness.py -- put the human on the ground and see whether the ground holds it.

Every membrane above the human can be individually correct and the pair can still be wrong, because
the human and the terrain meet at an INTERFACE and nothing on either side owns it. The terrain
publishes a height field and a bearing capacity; the body publishes a foot pressure, a stride and a
repose angle it will not climb past. This exercises that seam, over the whole patch, and reports
facts.

WHAT IT CHECKS, and the failure each one is named after:

  THE FIELD          finite everywhere, and its relief matches what aTerrain says it carved. A
                     height field that extrapolates instead of interpolating returned 13,414 m on a
                     field whose true maximum is 451 -- and it did so ONLY at the patch edge,
                     because at the middle the bug cancelled exactly. Sampling the middle proves
                     nothing about a field.
  CONTINUITY         no cliff between adjacent samples that the grid does not contain. A stride is
                     ~0.6 m and the grid is ~94 m, so a foot must never find a step it cannot take.
  THE FOOT HOLDS     foot pressure against the ground's bearing capacity, at the body's own mass
                     and this planet's own gravity. If it loses, the person sinks.
  WALKABLE           what fraction of the patch is below the repose angle. If that is small the
                     human is trapped in a pit and the walk will look broken when the terrain is.
  THE WALK STAYS ON  drive the real Walker over long traverses and check its feet meet the field at
                     EVERY step -- not at the spawn. Floating and sinking are the same bug seen
                     from two sides, and both are invisible at one point.
  THE EYE            eye height above the ground it is standing on, against what theHuman derived.
  THE STRIDE FITS    the body's own stride against the terrain's grid and relief: a stride that
                     spans a whole grid cell is a body walking on an interpolation artefact.

RUN:  python tools/terrain_witness.py
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main() -> int:
    import numpy as np
    from ChimeraEngine import walker as W

    fails, notes = [], []
    w = W.Walker()
    patch = w.patch
    print(f"the human: {w.height_m:.3f} m, g = {w.g:.3f} m/s2, walk {w.walk:.3f} m/s, "
          f"eye {w.eye:.3f} m")
    print(f"the patch: {patch:.0f} m across, at {w.lat_deg:.2f} deg latitude")
    print()

    # ── THE FIELD, over the WHOLE patch and deliberately including its edges ──────────────────
    m = patch / 2.0 - 1.0
    gx, gy = np.meshgrid(np.linspace(-m, m, 240), np.linspace(-m, m, 240))
    Z = W.heights_at(gx, gy)
    finite = np.isfinite(Z).all()
    print(f"THE FIELD      relief {Z.min():8.2f} .. {Z.max():8.2f} m   "
          f"(range {Z.max()-Z.min():.2f} m)   finite: {finite}")
    if not finite:
        fails.append(f"{int((~np.isfinite(Z)).sum())} height samples are NaN or infinite")

    # the same field sampled ONLY near the middle -- what a spawn-point test would have seen
    q = patch / 8.0
    cx, cy = np.meshgrid(np.linspace(-q, q, 64), np.linspace(-q, q, 64))
    Zc = W.heights_at(cx, cy)
    print(f"               middle eighth only: {Zc.min():.2f} .. {Zc.max():.2f} m   "
          f"-- an edge fault would not appear here")

    # ── CONTINUITY. Adjacent samples 100 m apart must not differ by more than the terrain can. ──
    step = (2 * m) / 239.0
    dzx = np.abs(np.diff(Z, axis=1)).max()
    dzy = np.abs(np.diff(Z, axis=0)).max()
    worst = max(dzx, dzy)
    worst_grade = math.degrees(math.atan(worst / step))
    print(f"CONTINUITY     steepest sample-to-sample rise {worst:.2f} m over {step:.1f} m "
          f"= {worst_grade:.1f} deg")
    if worst_grade > 89.0:
        fails.append(f"a vertical or overhanging step of {worst:.1f} m -- the field is discontinuous")

    # ── WHAT THE GROUND CARRIES, against what the body puts on it ────────────────────────────
    nums = W._load()[1]
    h, ground = nums["human"], W._static()["ground"]
    press = h.get("foot_pressure_kPa")
    holds = h.get("ground_bearing_kPa")
    if press and holds:
        print(f"THE FOOT       {press:.1f} kPa on one foot against {holds:.1f} kPa the ground "
              f"carries -- {holds/press:.2f}x margin")
        if press >= holds:
            fails.append(f"the foot loads {press:.1f} kPa and the ground holds {holds:.1f} "
                         f"-- the person sinks")

    # ONLY ONE MEMBRANE MAY ANSWER THIS, and finding out which was worth the check.
    #
    # theGround used to publish `foot_pressure_kPa` and `holds_a_person` from a TYPED body --
    # BODY_MASS_KG = 82.04 on a 0.030 m2 foot -- while theHuman derived 94.50 kg on 0.02764 and got
    # a pressure 20% higher. Both cleared the soil's capacity comfortably, so nothing looked wrong.
    # But move the height at the top of the story and only one of them follows: that is the slider
    # test failing, and a parent had invented its child's body to answer a question about itself.
    #
    # theGround now states what soil can state -- the load above which it fails -- and names who
    # answers the rest. So this asserts the CLAIM IS SINGLE, which is stronger than checking that
    # two copies happen to agree.
    if ground.get("foot_pressure_kPa") is not None:
        fails.append("theGround publishes foot_pressure_kPa again -- a parent typing a body to "
                     "answer a question that belongs to theHuman")
    owner = ground.get("who_answers_holds_a_person")
    if owner:
        print(f"               theGround fails above {ground['fails_above_kPa']:.1f} kPa and defers "
              f"the person to {owner}")
    sink = ground.get("sinkage_mm")
    if sink is not None:
        print(f"               sinkage under a {ground.get('reference_load_kg', 0):.0f} kg "
              f"reference load: {sink:.3f} mm")
        if sink > 50.0:
            fails.append(f"the reference load sinks {sink:.0f} mm -- that is not ground, it is mud")

    # ── WALKABLE GROUND. Past the repose angle, loose material slides and so does a boot. ──────
    zx, zy = W.gradients_at(gx, gy)
    grade = np.degrees(np.arctan(np.hypot(zx, zy)))
    walkable = float((grade < w.repose_deg).mean())
    print(f"WALKABLE       {walkable*100:.1f}% of the patch is below the {w.repose_deg:.2f} deg "
          f"repose angle   (median slope {np.median(grade):.2f} deg, max {grade.max():.2f})")
    if walkable < 0.5:
        fails.append(f"only {walkable*100:.0f}% of the ground is walkable -- the body is fenced in "
                     f"and any walk test measures the fence")

    # ── THE WALK. Drive the real Walker, and check the feet at EVERY step, not at the spawn. ──
    print()
    print("THE WALK       eight traverses, 900 steps each at 1/60 s, checking contact every step")
    worst_gap = 0.0
    worst_where = None
    stuck = 0
    total_dist = 0.0
    for k in range(8):
        w = W.Walker()
        w.yaw = 2.0 * math.pi * k / 8.0
        d0 = w.dist
        for _ in range(900):
            w.move(1.0, 0.0, False, False, False, 1.0 / 60.0)
            if not w.on_ground:
                continue
            gz = W.height_at(w.x, w.y)
            gap = abs(w.z - gz)
            if gap > worst_gap:
                worst_gap, worst_where = gap, (w.x, w.y)
            if not (math.isfinite(w.x) and math.isfinite(w.y) and math.isfinite(w.z)):
                fails.append(f"the walker's position went non-finite at traverse {k}")
                break
        moved = w.dist - d0
        total_dist += moved
        if moved < 1.0:
            stuck += 1
        print(f"               heading {math.degrees(w.yaw):5.0f} deg -> travelled {moved:7.2f} m "
              f"to ({w.x:8.1f}, {w.y:8.1f}), ground {W.height_at(w.x, w.y):7.2f} m")
    print(f"               worst foot-to-ground gap over all 7,200 steps: {worst_gap*1000:.3f} mm"
          + (f" at ({worst_where[0]:.0f}, {worst_where[1]:.0f})" if worst_where else ""))
    if worst_gap > 0.01:
        fails.append(f"the body is {worst_gap*100:.1f} cm off the ground somewhere on a traverse "
                     f"-- floating or sinking")
    if stuck:
        notes.append(f"{stuck} of 8 headings travelled under a metre -- blocked by slope, which is "
                     f"the repose gate doing its job if the terrain really is that steep there")

    # ── THE EYE, and THE STRIDE against the grid ──────────────────────────────────────────────
    w = W.Walker()
    ep = w.eye_pos
    ep = ep() if callable(ep) else ep
    eye_above = ep[2] - W.height_at(w.x, w.y)
    print()
    print(f"THE EYE        {eye_above:.4f} m above the ground it stands on, against "
          f"{w.eye:.4f} m derived")
    if abs(eye_above - w.eye) > 0.02:
        fails.append(f"eye sits {eye_above:.3f} m up but theHuman derived {w.eye:.3f}")

    dx = W._load()[0][1]
    stride = h.get("stride_m", 0.0)
    print(f"THE STRIDE     {stride:.3f} m against a {dx:.1f} m grid cell -- "
          f"{dx/max(stride,1e-9):.0f} strides per cell")
    if stride > dx:
        fails.append(f"a stride ({stride:.2f} m) is longer than a grid cell ({dx:.1f} m) -- the "
                     f"body is walking on interpolation, not on terrain")

    print()
    for n in notes:
        print(f"  note: {n}")
    for f in fails:
        print(f"  REFUSED: {f}")
    print()
    print("THE GROUND HOLDS THE HUMAN" if not fails else f"REFUSED on {len(fails)} count(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
