"""rung 1.75 — THE FOUNDATION: the skeleton is the axis, adhesion is the flesh.

rung 1.5 proved that neither half makes a limb alone. Differential adhesion segments a
thin bone core (a highly cohesive rod is Rayleigh-Plateau unstable and pinches into
blobs); a skeleton on its own is bare bone with no tissue. THIS FUSES THEM:

    the evolution engine's L-system SKELETON  ->  a continuous bone AXIS (voxelized, frozen)
    core.matter's differential ADHESION        ->  muscle and skin sorted radially around it

The bone cannot pinch, because the skeleton holds the axis. The flesh organizes itself,
because adhesion does what a skeleton cannot. Together they make the FIRST CONTINUOUS
LIMB — the foundation everything in docs/THE_MATTER_MODEL.md §12 (the player character,
and a world) stands on.

    THE SKELETON PROVIDES THE AXIS. ADHESION PROVIDES THE RADIAL TISSUE. Neither alone.

This is the INTEGRATION module. It imports both core.terrarium (the grower) and
core.matter (the adhesion), which each remain sealed primitives; the fusion lives here at
the seam, not inside either half. The Bone objects below are exactly what terrarium.grow()
returns, so a fully grown skeleton drops in unchanged — this limb is hand-built only so the
bend is controlled and the win is unmistakable.

FACTS ONLY. Whether the limb is GOOD lives in an objective, later.
"""

from __future__ import annotations

import argparse
import collections
from pathlib import Path

import numpy as np

from core import matter
from core.matter import BONE, MEDIUM, MUSCLE, SKIN
from core.terrarium import Bone


def bent_limb():
    """A limb skeleton as a chain of terrarium.Bone with a deliberate S-bend. Adhesion
    could NEVER hold a bent rod together — so if the fleshed bone comes out continuous and
    curved, the skeleton is unmistakably what did it. These are the exact objects
    terrarium.grow() yields; a grown skeleton substitutes directly."""
    return [
        Bone(parent=-1, p0=(0.00, 0, 0.00), p1=(0.07, 0, 0.34), r0=0.10, r1=0.09, depth=0),
        Bone(parent=0,  p0=(0.07, 0, 0.34), p1=(0.00, 0, 0.68), r0=0.09, r1=0.09, depth=1),
        Bone(parent=1,  p0=(0.00, 0, 0.68), p1=(-0.06, 0, 1.02), r0=0.09, r1=0.08, depth=2),
    ]


def voxelize(bones, target_len=64, flesh_scale=2.7, fractions=(0.55, 0.45),
             seed=0, pad=3):
    """Skeleton -> a 3D lattice. Cells within the bone radius of the skeletal polyline are
    BONE (the frozen scaffold); the sheath out to flesh_scale x that radius is a SCRAMBLED
    pepper of muscle and skin; the rest is medium. The flesh follows the bent axis, so
    adhesion sorts it into an inner muscle sheath and an outer skin shell around a bone it
    cannot move."""
    rng = np.random.RandomState(seed)
    segs = [(np.asarray(b.p0, float), np.asarray(b.p1, float)) for b in bones]
    pts = np.array([q for s in segs for q in s])
    lo, hi = pts.min(0), pts.max(0)
    scale = target_len / max((hi - lo).max(), 1e-6)
    br = float(np.mean([b.r0 for b in bones])) * scale     # bone radius, in cells
    fr = br * flesh_scale                                   # flesh sheath radius

    # segments in lattice coordinates, with a margin so the sheath never touches the border
    margin = fr + pad
    A = [((a - lo) * scale + margin) for a, _ in segs]
    B = [((b - lo) * scale + margin) for _, b in segs]
    D = np.ceil((hi - lo) * scale + 2 * margin).astype(int) + 1
    D = tuple(int(d) for d in D)                            # (z, y, x) padded

    zz, yy, xx = np.mgrid[0:D[0], 0:D[1], 0:D[2]]
    P = np.stack([zz, yy, xx], axis=-1).reshape(-1, 3).astype(np.float32)
    dmin = np.full(len(P), np.inf, dtype=np.float32)
    for a, b in zip(A, B):                                  # min distance to the polyline
        ab = b - a
        t = np.clip((P - a) @ ab / (ab @ ab + 1e-9), 0.0, 1.0)
        d = np.linalg.norm(P - (a + t[:, None] * ab), axis=1)
        dmin = np.minimum(dmin, d)

    g = np.full(len(P), MEDIUM, dtype=np.int16)
    flesh = (dmin > br) & (dmin <= fr)
    g[flesh] = rng.choice((MUSCLE, SKIN), size=int(flesh.sum()),
                          p=np.asarray(fractions) / sum(fractions)).astype(np.int16)
    g[dmin <= br] = BONE
    g = g.reshape(D)
    targets = {t: int((g == t).sum()) for t in (BONE, MUSCLE, SKIN)}
    return g, D, targets


def grow_limb(bones, sweeps=70, seed=0, gpu=True, **kw):
    """Voxelize the skeleton, then wrap it in flesh by differential adhesion with the bone
    FROZEN. Returns (scaffold_grid, fleshed_grid, shape, targets).

    gpu=True (tb-0199) runs THE SHAKER in Warp (core.matter_gpu, 6.3B site-updates/sec
    on the 4090 vs a single CPU core) — same J matrix, same lambda volume constraint,
    same frozen scaffold, 18-connectivity via the safe 8-color decomposition. Falls
    back to the CPU model (byte-for-byte the rung-1 witness) if Warp is unavailable."""
    grid, shape, targets = voxelize(bones, seed=seed, **kw)
    if gpu:
        try:
            from core.matter_gpu import assemble_3d_gpu
            fleshed = assemble_3d_gpu(grid, shape, targets, matter.J_DIFFERENTIAL_3D,
                                      sweeps=sweeps, seed=seed, frozen_type=BONE)
            return grid, fleshed, shape, targets
        except Exception as e:                          # Warp missing / OOM -> CPU
            print(f"[limb] GPU shaker unavailable ({type(e).__name__}: {e}); CPU fallback")
    fleshed = matter.assemble_3d(grid, shape, targets, matter.J_DIFFERENTIAL_3D,
                                 sweeps=sweeps, seed=seed, frozen_type=BONE)
    return grid, fleshed, shape, targets


def _components(grid, kind, strides):
    """Number and sizes of 6-connected blobs of `kind`. A continuous bone is ONE blob; the
    free bone in rung 1.5 pinched into two. This is the metric that names the whole rung."""
    off = matter._nd_offsets(strides, 6)
    L = grid.ravel()
    members = set(np.nonzero(L == kind)[0].tolist())
    sizes = []
    while members:
        seed_cell = next(iter(members))
        members.discard(seed_cell)
        q = collections.deque([seed_cell])
        n = 0
        while q:
            s = q.popleft()
            n += 1
            for d in off:
                nb = s + d
                if nb in members:
                    members.discard(nb)
                    q.append(nb)
        sizes.append(n)
    return sorted(sizes, reverse=True)


def limb_metrics(grid, shape) -> dict:
    strides = (shape[1] * shape[2], shape[2], 1)
    off = matter._nd_offsets(strides, 6)
    L = grid.ravel()
    tissue = grid != MEDIUM
    _, yy, xx = np.nonzero(tissue)
    cy, cx = yy.mean(), xx.mean()
    out = {"radius": {}, "bone_blobs": _components(grid, BONE, strides)}
    for t in (BONE, MUSCLE, SKIN):
        m = np.nonzero(grid == t)
        out["radius"][t] = float(np.sqrt((m[1] - cy) ** 2 + (m[2] - cx) ** 2).mean())
    # does muscle WRAP the bone? of bone's tissue-neighbours, what fraction is muscle?
    bone = np.nonzero(L == BONE)[0]
    mus = skn = tot = 0
    for s in bone:
        for d in off:
            nb = L[s + d]
            if nb == MUSCLE:
                mus += 1; tot += 1
            elif nb == SKIN:
                skn += 1; tot += 1
    out["muscle_wraps_bone"] = mus / max(tot, 1)
    # skin exposure to medium (it should be the shell)
    skin = np.nonzero(L == SKIN)[0]
    exp = sum(1 for s in skin for d in off if L[s + d] == MEDIUM)
    out["skin_exposure"] = exp / max(len(skin) * len(off), 1)
    return out


def render_limb(scaffold, fleshed, shape, path: Path, scale=7, gap=8):
    """A correctly-labelled witness: a true CROSS-SECTION perpendicular to the limb's long
    axis (the annular bone/muscle/skin layering) and a LONGITUDINAL slice down the bend
    (the continuous bone the skeleton holds, before and after adhesion). The long axis is
    found from the shape, so the labels never lie about which way we are looking."""
    from PIL import Image, ImageDraw

    long = int(np.argmax(shape))
    shorts = [i for i in range(3) if i != long]
    thin = shorts[0] if shape[shorts[0]] <= shape[shorts[1]] else shorts[1]

    def cross(arr):
        return np.take(arr, shape[long] // 2, axis=long)          # perpendicular to length

    def length(arr):
        return np.take(arr, shape[thin] // 2, axis=thin)          # down the bend plane

    def colorize(plane):
        h, w = plane.shape
        rgb = np.zeros((h, w, 3), dtype=np.uint8)
        for t, col in matter._COLORS.items():
            rgb[plane == t] = col
        return Image.fromarray(rgb, "RGB").resize((w * scale, h * scale), Image.NEAREST)

    panels = [
        ("cross-section (mid-limb)", colorize(cross(fleshed))),
        ("length: scrambled start", colorize(length(scaffold))),
        ("length: skeleton + adhesion", colorize(length(fleshed))),
    ]
    W = sum(im.width for _, im in panels) + gap * (len(panels) - 1)
    H = max(im.height for _, im in panels) + 22
    strip = Image.new("RGB", (W, H), (12, 12, 14))
    d = ImageDraw.Draw(strip)
    x = 0
    for label, im in panels:
        strip.paste(im, (x, 22))
        d.text((x + 4, 6), label, fill=(220, 220, 220))
        x += im.width + gap
    path.parent.mkdir(parents=True, exist_ok=True)
    strip.save(path)
    return path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--sweeps", type=int, default=70)
    ap.add_argument("--png", default=None)
    a = ap.parse_args()

    bones = bent_limb()
    scaffold, fleshed, shape, targets = grow_limb(bones, sweeps=a.sweeps, seed=a.seed)
    m = limb_metrics(fleshed, shape)
    r = m["radius"]

    print(f"\nFOUNDATION — a {len(bones)}-segment skeleton (bent), wrapped in flesh by adhesion:")
    print(f"  bone is CONTINUOUS?   {len(m['bone_blobs'])} connected blob(s)  "
          f"sizes {m['bone_blobs'][:4]}   (rung 1.5's free bone pinched into 2+)")
    print(f"  radial layering       bone {r[BONE]:.1f}  <  muscle {r[MUSCLE]:.1f}  "
          f"<  skin {r[SKIN]:.1f}")
    print(f"  muscle WRAPS bone     {m['muscle_wraps_bone']:.2f}  "
          f"(fraction of bone's tissue neighbours that are muscle, not skin)")
    print(f"  skin is the shell     exposure {m['skin_exposure']:.2f}")

    continuous = len(m["bone_blobs"]) == 1
    layered = r[BONE] < r[MUSCLE] < r[SKIN]
    wrapped = m["muscle_wraps_bone"] > 0.8

    print()
    if continuous and layered and wrapped:
        print("  FOUNDATION LAID. The skeleton held the bone as ONE continuous, bent axis")
        print("  where adhesion alone had pinched it in two, and adhesion wrapped it in an")
        print("  inner muscle sheath and an outer skin shell — unattended. The two halves")
        print("  of the whole system are one pipeline now. rung 1.75 stands.")
        verdict = 0
    else:
        print(f"  NOT YET: continuous={continuous}  layered={layered}  wrapped={wrapped}")
        verdict = 1

    if a.png:
        print(f"\n  -> {render_limb(scaffold, fleshed, shape, Path(a.png))}")
    return verdict


if __name__ == "__main__":
    raise SystemExit(main())
