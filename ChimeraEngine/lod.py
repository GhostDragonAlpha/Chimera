"""Trained Level-of-Detail for splat bodies -- the pixel-budget law, learned not hand-tuned.

THE LAW (scale-invariant screen-space density): a body whose projected radius is r_px pixels is rendered
with  N = rho * r_px^2  grains -> grains-per-pixel and per-pixel OVERDRAW are constant at every scale, so
one colour gain holds everywhere (no white blow-out when a planet shrinks in the solar-system view) and the
total grain work is bounded by screen area (the operator's "square-footage" budget -> framerate stops
depending on zoom).

Coarse levels are a MIP PYRAMID with spatially-AVERAGED colours: a 1px planet is the average of the whole
surface (not one arbitrary grain), a 4px planet is a handful of regional averages, etc. -- exactly a texture
mipmap, on the sphere. Built ONCE per body; runtime LOD is a cheap level lookup.

`rho` (density) and `beta` (grain overlap) are TRAINED by lod_train.py; loaded from lod.trained.json.
"""
from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np

_TRAINED = Path(__file__).resolve().parent / "lod.trained.json"
_DEFAULT = {"rho": 0.45, "beta": 2.5, "n_min": 1}
_SIZE_COL = 20            # matches ParticleEngine.gpu_pipeline.SIZE / splat_appearance.SIZE


def params() -> dict:
    try:
        d = json.loads(_TRAINED.read_text())
        return {"rho": float(d["rho"]), "beta": float(d["beta"]), "n_min": int(d.get("n_min", 1)),
                "color_gain": [float(x) for x in d.get("color_gain", [1.0, 1.0, 1.0])]}
    except Exception:
        return dict(_DEFAULT, color_gain=[1.0, 1.0, 1.0])


def lod_count(r_px: float, n_base: int, p: dict | None = None) -> int:
    """Grains for a body of projected radius r_px (clamped to [n_min, n_base]). N = rho * r_px^2."""
    p = p or params()
    return max(p["n_min"], min(n_base, int(round(p["rho"] * r_px * r_px))))


def body_radius(buf: np.ndarray) -> float:
    return float(np.linalg.norm(buf[:, 0:3], axis=1).max()) if buf.shape[0] else 1.0


def should_lod(buf) -> bool:
    """Is this body something LOD can reason about at all?

    TWO REFUSALS, and the second was found by running the demo. A body needs enough grains to have
    mip levels (below ~64 the pyramid is the base), and it needs EXTENT -- because every quantity
    in the law is a projected SIZE, and a body of zero radius projects to zero pixels no matter
    where the camera is.

        theZero  n=4000  body_radius=0

    theZero is the seed: r = 0, a point. Feeding it to the law is not wrong so much as
    meaningless -- r_px comes out 0, lod_count returns its n_min floor, and a 4,000-grain membrane
    is drawn with ONE splat. The law answered a question that has no answer, and it answered
    plausibly, which is the dangerous kind. A zero-extent body is refused here rather than
    silently reduced to its floor.
    """
    try:
        return buf is not None and buf.shape[0] > 64 and body_radius(buf) > 1e-9
    except Exception:
        return False


def projected_radius_px(radius_world: float, cam_distance: float, height_px: int, fov: float) -> float:
    focal = height_px / (2.0 * math.tan(fov / 2.0))
    return radius_world * focal / max(1e-6, cam_distance)


# ── the mip pyramid ────────────────────────────────────────────────────────────────────────────────────
_MIP_LEVELS = [1, 4, 16, 64, 256, 1024, 4096, 16384]     # + the base itself as the finest level


def _mip_levels_for(n_base: int) -> list[int]:
    """The ladder, EXTENDED to reach this body. A fixed top rung is a pop waiting for a big body.

    THE POP FALSIFIER FIRED HERE, and only on the largest membrane. `_MIP_LEVELS` stopped at a
    hard-coded 16,384, so the gap between the top mip and the base was whatever the base happened
    to be:

        theStar         20,000 / 16,384 =  1.22x    fine
        theRockyPlanet  41,974 / 16,384 =  2.56x    fine
        aBlueWorld      43,000 / 16,384 =  2.62x    fine
        aTerrain       262,144 / 16,384 = 16.00x    POP -- twice the 8x bar

    Every rung of the ladder is a factor of 4, so the LAST step should be too. It was 16x for
    aTerrain because the ladder simply ran out below it, and the defect was invisible on every
    other term precisely because their bases happen to sit near 16,384. A constant chosen when the
    biggest body was small becomes a discontinuity when a bigger one arrives.

    Extending by 4 until the ladder covers the base keeps the worst step at 4x for ANY size, and
    costs one extra mip level only for bodies that need it.
    """
    out = list(_MIP_LEVELS)
    while out[-1] * 4 < n_base:
        out.append(out[-1] * 4)
    return out


def build_mips(base: np.ndarray, radius_world: float, p: dict | None = None) -> list[np.ndarray]:
    """Precompute LOD levels for a body. Coarse levels use SPATIALLY-AVERAGED colours (nearest-representative
    clustering on the sphere); finer levels (> ~a few k) just subsample -- their detail is already sub-pixel
    when they're chosen. Each level's grain SIZE is set by the law (beta * 2R/sqrt(N)) so it tiles. Returns
    levels coarse->fine; the last is the base."""
    p = p or params()
    n_base = base.shape[0]
    dirs = base[:, 0:3] / (np.linalg.norm(base[:, 0:3], axis=1, keepdims=True) + 1e-9)
    levels = []
    for N in _mip_levels_for(n_base):
        if N >= n_base:
            break
        idx = np.linspace(0, n_base - 1, N).astype(np.int64)
        lvl = base[idx].copy()
        if N <= 1024:                                     # spatial colour average (mipmap): assign each base grain to
            reps = dirs[idx]                              # its nearest representative, average the colours per cell
            nearest = np.argmax(dirs @ reps.T, axis=1)    # (n_base,) -> which representative
            for c in (16, 17, 18):                        # CR, CG, CB
                sums = np.bincount(nearest, weights=base[:, c], minlength=N)
                cnts = np.bincount(nearest, minlength=N).clip(min=1)
                lvl[:, c] = (sums / cnts).astype(np.float32)
        lvl[:, _SIZE_COL] = p["beta"] * 2.0 * radius_world / math.sqrt(max(1, N))
        levels.append(lvl)
    base_lvl = base.copy()
    base_lvl[:, _SIZE_COL] = p["beta"] * 2.0 * radius_world / math.sqrt(max(1, n_base))
    levels.append(base_lvl)
    cg = p.get("color_gain", [1.0, 1.0, 1.0])            # re-expose for the law's overdraw (calibrated once)
    if cg != [1.0, 1.0, 1.0]:
        for lvl in levels:
            for i, c in enumerate((16, 17, 18)):
                lvl[:, c] = np.clip(lvl[:, c] * cg[i], 0.0, 1.0)
    return levels


def select(levels: list[np.ndarray], r_px: float, p: dict | None = None) -> np.ndarray:
    """Pick the coarsest mip level with at least lod_count(r_px) grains -> the fewest grains that suffice."""
    p = p or params()
    want = lod_count(r_px, levels[-1].shape[0], p)
    for lvl in levels:
        if lvl.shape[0] >= want:
            return lvl
    return levels[-1]


# ── LOD SWITCHING (near/far, Task 2) ──────────────────────────────────────────────────────────────

# Judgment distance: 720p, the standard for "can you read the detail at normal viewing distance"
_JUDGMENT_H = 720
_JUDGMENT_FOV = 1.047  # 60 degrees in radians — the viewer's default


def lod_switch(buf: np.ndarray, cam_distance: float, height_px: int = _JUDGMENT_H,
               fov: float = _JUDGMENT_FOV, p: dict | None = None) -> np.ndarray:
    """THE LOD SWITCH — near/far density switching keyed to screen-space size.

    STATEMENT: A body whose projected radius selects a coarse mip level already looks correct at that
    level — the mip was built by SPATIALLY-AVERAGING the base. Switching to it saves grains with no
    visible pop because the coarse level's grain size is set by the law (β * 2R/√N) so it tiles the
    same coverage. The transition IS the mip boundary.

    PREDICTION: Frame budget holds (perf-guard) at max density near, min far — no visible pop in a
    recorded orbit because mip levels are built from the same base and grain size is continuous.

    FALSIFIER: LOD switch visible as a pop in a recorded orbit — the coarse level's grain size
    differs from the fine level's by more than one pixel at the switch distance.

    Returns the LOD-selected buffer. If no mips were precomputed, returns the buffer unchanged.
    """
    radius = body_radius(buf)
    r_px = projected_radius_px(radius, cam_distance, height_px, fov)
    p = p or params()
    levels = build_mips(buf, radius, p)
    if len(levels) <= 1:
        return buf  # no mips to switch between
    return select(levels, r_px, p)


def near_far(buf: np.ndarray, cam_distance: float, height_px: int = _JUDGMENT_H,
             fov: float = _JUDGMENT_FOV, p: dict | None = None) -> tuple[np.ndarray, int]:
    """Return (buffer, n_grains) for the LOD level at this distance."""
    p = p or params()
    radius = body_radius(buf)
    r_px = projected_radius_px(radius, cam_distance, height_px, fov)
    levels = build_mips(buf, radius, p)
    if len(levels) <= 1:
        return buf, buf.shape[0]
    lvl = select(levels, r_px, p)
    return lvl, lvl.shape[0]


# ── THE POP PROBE (the falsifier lod_switch named and nobody had run) ──────────────────────────

def pop_probe(buf: np.ndarray, radius0: float, n: int = 180, height_px: int = 1080,
              fov: float = _JUDGMENT_FOV, p: dict | None = None) -> dict:
    """Sweep the camera through the viewer's whole zoom range and look for a POP.

    WHAT A 360 DEGREE ORBIT CANNOT TEST, and this is the first thing the probe had to settle:
    `select()` reads only `r_px`, and `r_px` reads only the DISTANCE. Azimuth does not enter it.
    So spinning the camera around a body at constant radius cannot change the level no matter how
    many frames it takes -- a 180-frame orbit would report one constant number and "no pop" would
    be true by construction rather than by measurement. That is a description, and a description
    survives any result.

        THE AXIS THAT MOVES LOD IS ZOOM, NOT YAW. So the sweep runs the RADIUS across exactly the
        band the viewer permits (`_radius0 * 0.45` to `_radius0 * 2.5`, its own clamps), which is
        the full set of distances a user can actually reach.

    The orbit is still run, as a CONTROL: the level must be perfectly flat across 360 degrees. If
    it is not, something depends on azimuth that should not.

    Returns the per-frame levels for both sweeps and the largest single-step ratio.
    """
    p = p or params()
    R = body_radius(buf)
    levels = build_mips(buf, R, p)
    if len(levels) <= 1:
        return {"levels": [buf.shape[0]], "orbit": [], "zoom": [], "max_step_ratio": 1.0,
                "note": "no mips -- nothing to switch between"}

    orbit = [select(levels, projected_radius_px(R, 2.8 * R, height_px, fov), p).shape[0]
             for _ in range(n)]                       # yaw does not enter r_px; this must be flat

    zoom, dists = [], []
    for i in range(n):
        f = 0.45 + (2.5 - 0.45) * i / (n - 1)         # the viewer's own zoom clamps
        d = 2.8 * R * f
        dists.append(d)
        zoom.append(select(levels, projected_radius_px(R, d, height_px, fov), p).shape[0])

    steps = [(i, zoom[i - 1], zoom[i], max(zoom[i - 1], zoom[i]) / max(min(zoom[i - 1], zoom[i]), 1))
             for i in range(1, n) if zoom[i] != zoom[i - 1]]
    worst = max((s[3] for s in steps), default=1.0)
    return {"levels": [l.shape[0] for l in levels], "orbit": orbit, "zoom": zoom,
            "dists": dists, "switches": steps, "max_step_ratio": worst,
            "orbit_flat": len(set(orbit)) == 1}


if __name__ == "__main__":
    import sys as _sys
    from pathlib import Path as _P
    _sys.path.insert(0, str(_P(__file__).resolve().parent))
    import splat_appearance as _sa

    term = _sys.argv[1] if len(_sys.argv) > 1 else "aBlueWorld"
    b = _sa.scene_buffer(term)
    if b is None:
        raise SystemExit(f"{term} does not emit")
    r = pop_probe(b, 2.8 * body_radius(b))
    print(f"LOD POP PROBE -- {term}, {b.shape[0]} grains")
    print(f"  mip levels      {r['levels']}")
    print(f"  360 orbit       flat={r['orbit_flat']}  (levels seen: {sorted(set(r['orbit']))})")
    print(f"  zoom sweep      0.45x .. 2.50x of default framing, 180 steps")
    print(f"  levels visited  {sorted(set(r['zoom']), reverse=True)}")
    print(f"  switches        {len(r['switches'])}")
    for i, a, c, ratio in r["switches"]:
        print(f"    frame {i:>4d}:  {a:>6d} -> {c:<6d}  ratio {ratio:.2f}x")
    ok = r["max_step_ratio"] <= 8.0 and r["orbit_flat"]
    print(f"  WORST STEP      {r['max_step_ratio']:.2f}x   "
          f"{'PASS (no pop: <= 8x)' if ok else 'FIRED'}")
    raise SystemExit(0 if ok else 1)
