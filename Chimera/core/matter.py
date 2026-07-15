"""THE MATTER MODEL — rung 0-1: the brick, and adhesion that assembles a limb.

Full design: docs/THE_MATTER_MODEL.md. This file is the thinnest slice that proves the
load-bearing claim — "the LEGOs fit together the way the real world does" — in pure
Python, headless, BEFORE any UE5 bake, exactly the way core/terrarium.py proved
genome->body before touching the engine.

THE CLAIM, STATED SO IT CAN FAIL
--------------------------------
Give three brick types nothing but an ADHESION PROFILE (how strongly each sticks to each
other and to empty space) and start them SCRAMBLED — a random pepper of bone, muscle and
skin inside a blob. Differential adhesion alone must sort them into the correct limb
cross-section: bone in the CORE, skin on the SHELL, muscle BETWEEN. Nobody places a
single cell.

This is Steinberg's Differential Adhesion Hypothesis (1964), run as a Cellular Potts /
Glazier-Graner-Hogeweg model: the more cohesive tissue is engulfed by the less cohesive
one, exactly as immiscible liquids sort by surface tension. The surface tension of tissue
T against empty medium is gamma(T) ~ J(T,medium) - J(T,T)/2; the tissue with the highest
gamma rounds up and buries itself. So the ENTIRE specification of a limb's layering is
three numbers, and none of them is a position.

    I do not encode the anatomy. I encode the STICKINESS. The anatomy is the ANSWER.

THE PROOF IS A CONTRAST, NOT A PICTURE
--------------------------------------
A sorted blob on its own proves nothing — the machinery could be forcing it. So `main`
runs the SAME scrambled start twice: once with the differential profile (must sort) and
once with a UNIFORM profile where every brick sticks to everything equally (must NOT
sort). Differential adhesion is the independent variable; the sort is the effect; the
uniform control is the failure the test is able to show.

Imports NOTHING from the studio (a sealed generation primitive, like terrarium.py) — only
numpy, and PIL lazily for the witness render.

FACTS ONLY. What a "good" limb is lives in an objective, later — this file reports where
the bricks ended up, never whether that is beautiful.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np

# --- rung 0: the bricks -------------------------------------------------------
# Only the field THIS proof reads — the adhesion profile — is modelled. The full brick
# struct (physical/optical/behavior/granularity, docs/THE_MATTER_MODEL.md §2) lands as
# the pipeline grows; inventing it now would be encoding taste we cannot yet test.
MEDIUM, BONE, MUSCLE, SKIN = 0, 1, 2, 3
NAMES = {MEDIUM: "medium", BONE: "bone", MUSCLE: "muscle", SKIN: "skin"}
TISSUES = (BONE, MUSCLE, SKIN)

# Contact energy J[a][b]: the cost of a unit of a-b interface. LOWER = more adhesive.
# Symmetric. The whole design lives in these 16 numbers.
#
# Read the medium column as "how much this brick hates being exposed":
#   bone 16 (buries itself)  >  muscle 11  >  skin 5 (tolerates the surface).
# and the diagonal as self-cohesion (lower = sticks to its own kind harder):
#   bone 2 (most cohesive)   <  muscle 4   <  skin 6.
# => gamma(bone)=16-1=15  >  gamma(muscle)=11-2=9  >  gamma(skin)=5-3=2.
# Bone innermost, skin outermost. bone<->skin is made expensive (12) so muscle is
# forced to sit between them rather than bone and skin touching directly.
J_DIFFERENTIAL = np.array([
    #  MED  BONE  MUS  SKIN
    [   0,   16,  11,    5],   # MEDIUM
    [  16,    2,   6,   12],   # BONE
    [  11,    6,   4,    6],   # MUSCLE
    [   5,   12,   6,    6],   # SKIN
], dtype=np.float64)

# THE CONTROL. Every brick sticks to everything (and to medium) equally, so there is no
# energetic reason to sort. If THIS also sorts, the sort was an artifact of the machine,
# not of adhesion, and the whole claim is dead. It must come out mixed.
J_UNIFORM = np.full((4, 4), 8.0)
J_UNIFORM[MEDIUM, MEDIUM] = 0.0

# --- rung 1.5: 3D, an elongated limb, and a TYPED CONNECTOR (tendon) -----------
# A tendon is the first "typed interface": a connector brick that bonds specifically to
# muscle AND bone and to nothing else, so muscle anchors to bone the way real anatomy
# joins tissues through standardized interfaces (docs/THE_MATTER_MODEL.md §3) rather than
# by mere proximity. The assembly PLACES it at the muscle-end/bone junction; differential
# adhesion then PINS it there — it must not wander to skin or the surface, and in the
# uniform control (nothing makes it belong) it must fail to stay put.
TENDON = 4
NAMES[TENDON] = "tendon"

# 5x5 differential profile: the 4x4 above plus the tendon row/col. Tendon is strong to
# muscle and bone (3), hostile to skin (12) and medium (15) so it stays at the junction.
J_DIFFERENTIAL_3D = np.array([
    #  MED  BONE  MUS  SKIN  TEN
    [   0,   16,  11,    5,  15],   # MEDIUM
    [  16,    2,   6,   12,    3],  # BONE
    [  11,    6,   4,    6,    3],  # MUSCLE
    [   5,   12,   6,    6,   12],  # SKIN
    [  15,    3,   3,   12,    3],  # TENDON
], dtype=np.float64)
J_UNIFORM_3D = np.full((5, 5), 8.0)
J_UNIFORM_3D[MEDIUM, MEDIUM] = 0.0

# 8-neighbourhood (Moore) — 4-connectivity gives blocky, axis-aligned interfaces that
# fake-sort along the grid; 8 rounds them.
_OFFS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def init_blob(size: int = 72, radius: float = 30.0,
              fractions=(0.22, 0.46, 0.32), seed: int = 0):
    """A SCRAMBLED disk: a random pepper of bone/muscle/skin, medium outside. Padded with
    a one-cell medium border so the Metropolis loop never needs a bounds check.

    Returns (grid, targets) where targets[t] is the brick count to conserve — the sort
    must REARRANGE the tissues, not let the cohesive ones eat the rest."""
    rng = np.random.RandomState(seed)
    g = np.full((size + 2, size + 2), MEDIUM, dtype=np.int8)
    c = (size + 2) / 2.0
    yy, xx = np.mgrid[0:size + 2, 0:size + 2]
    disk = (yy - c) ** 2 + (xx - c) ** 2 <= radius ** 2
    n = int(disk.sum())
    # assign each disk cell a tissue at random, in the requested proportions
    labels = rng.choice(TISSUES, size=n, p=np.asarray(fractions) / sum(fractions))
    g[disk] = labels.astype(np.int8)
    targets = {t: int((g == t).sum()) for t in TISSUES}
    return g, targets


def assemble(grid, targets, J, sweeps: int = 160, temp: float = 12.0,
             lam: float = 0.9, seed: int = 0):
    """Cellular Potts / Metropolis: minimise total interface energy under an area
    constraint, so bricks REARRANGE by adhesion without any tissue vanishing.

    A copy attempt: pick an interior site, pick a random neighbour, propose copying the
    neighbour's type into the site. Accept if it lowers energy, else with the Boltzmann
    probability exp(-dH/temp). This is the ONLY rule; the layering is emergent."""
    rng = np.random.RandomState(seed + 101)
    g = grid.copy()
    size = g.shape[0] - 2
    area = {t: int((g == t).sum()) for t in TISSUES}
    attempts = sweeps * size * size

    ys = rng.randint(1, size + 1, size=attempts)
    xs = rng.randint(1, size + 1, size=attempts)
    ks = rng.randint(0, 8, size=attempts)
    us = rng.random_sample(size=attempts)

    for i in range(attempts):
        y, x = int(ys[i]), int(xs[i])
        old = g[y, x]
        dy, dx = _OFFS[ks[i]]
        new = g[y + dy, x + dx]
        if new == old:
            continue

        # adhesion: sum over the 8 neighbours of the change in interface energy
        dH = 0.0
        for oy, ox in _OFFS:
            nb = g[y + oy, x + ox]
            dH += J[new, nb] - J[old, nb]

        # area conservation (medium is an unconstrained reservoir: lam=0 for it)
        if old != MEDIUM:
            a = area[old]
            dH += lam * ((a - 1 - targets[old]) ** 2 - (a - targets[old]) ** 2)
        if new != MEDIUM:
            a = area[new]
            dH += lam * ((a + 1 - targets[new]) ** 2 - (a - targets[new]) ** 2)

        if dH <= 0.0 or us[i] < np.exp(-dH / temp):
            g[y, x] = new
            if old != MEDIUM:
                area[old] -= 1
            if new != MEDIUM:
                area[new] += 1
    return g


def metrics(grid) -> dict:
    """WHERE DID THE BRICKS END UP? Mean radius of each tissue from the blob centroid
    (core tissue -> small radius), and each tissue's exposure to medium (shell tissue ->
    high exposure). Deterministic facts; no opinion about them."""
    tissue = grid != MEDIUM
    ys, xs = np.nonzero(tissue)
    cy, cx = ys.mean(), xs.mean()
    out = {"radius": {}, "exposure": {}, "area": {}}
    for t in TISSUES:
        m = grid == t
        yy, xx = np.nonzero(m)
        out["area"][t] = int(m.sum())
        out["radius"][t] = float(np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2).mean())
        # fraction of this tissue's cells touching at least one medium cell
        exposed = 0
        for y, x in zip(yy, xx):
            if any(grid[y + oy, x + ox] == MEDIUM for oy, ox in _OFFS):
                exposed += 1
        out["exposure"][t] = exposed / max(len(yy), 1)
    return out


def is_sorted(m: dict, tol: float = 0.5) -> bool:
    """The layering is correct iff the radii are strictly ordered bone < muscle < skin
    by a real margin (not a tie), AND skin is more exposed to medium than bone."""
    r = m["radius"]
    ordered = (r[BONE] + tol < r[MUSCLE]) and (r[MUSCLE] + tol < r[SKIN])
    shelled = m["exposure"][SKIN] > m["exposure"][BONE] + 0.1
    return bool(ordered and shelled)


_COLORS = {MEDIUM: (24, 26, 32), BONE: (238, 231, 210),
           MUSCLE: (176, 58, 62), SKIN: (206, 160, 120),
           TENDON: (120, 205, 205)}


def render(panels, path: Path, scale: int = 6, gap: int = 8):
    """A witness strip: (label, grid) panels side by side, nearest-neighbour upscaled so
    individual bricks are visible. A number is not proof (H-14) — you must SEE the sort
    emerge from the noise."""
    from PIL import Image, ImageDraw

    imgs = []
    for _, g in panels:
        h, w = g.shape
        rgb = np.zeros((h, w, 3), dtype=np.uint8)
        for t, col in _COLORS.items():
            rgb[g == t] = col
        imgs.append(Image.fromarray(rgb, "RGB").resize(
            (w * scale, h * scale), Image.NEAREST))
    W = sum(im.width for im in imgs) + gap * (len(imgs) - 1)
    H = imgs[0].height + 22
    strip = Image.new("RGB", (W, H), (12, 12, 14))
    d = ImageDraw.Draw(strip)
    x = 0
    for (label, _), im in zip(panels, imgs):
        strip.paste(im, (x, 22))
        d.text((x + 4, 6), label, fill=(220, 220, 220))
        x += im.width + gap
    path.parent.mkdir(parents=True, exist_ok=True)
    strip.save(path)
    return path


# --- rung 1.5: the same rule on a 3D lattice ----------------------------------
# The CPM below is dimension-agnostic: it works on a FLAT (raveled) padded lattice with
# precomputed flat neighbour offsets, so the identical Metropolis rule that sorted the 2D
# cross-section now grows a 3D limb. Kept separate from the 2D path above so the proven
# rung-1 artifact is never disturbed.

def _nd_offsets(strides, connectivity: int):
    """Flat-index neighbour deltas for a padded N-D lattice, built from the +-1 combos per
    axis. 3D: 6 = faces, 18 = faces+edges, 26 = full Moore."""
    import itertools
    ndim = len(strides)
    out = []
    for combo in itertools.product((-1, 0, 1), repeat=ndim):
        nz = sum(1 for c in combo if c)
        if nz == 0:
            continue
        if ndim == 3 and connectivity == 6 and nz != 1:
            continue
        if ndim == 3 and connectivity == 18 and nz == 3:
            continue
        out.append(int(sum(c * s for c, s in zip(combo, strides))))
    return out


def init_limb_3d(length=60, radius=13, cap=5, fractions=(0.20, 0.50, 0.30), seed=0):
    """A SCRAMBLED elongated limb: a capsule domain (long axis = z) peppered at random with
    bone/muscle/skin, plus TENDON plugs seeded at each end in the annulus where muscle
    meets bone. Padded by one cell. Returns (grid, padded_shape, targets)."""
    rng = np.random.RandomState(seed)
    D = (length + 2 * cap + 2, 2 * radius + 3, 2 * radius + 3)   # z, y, x (padded)
    g = np.full(D, MEDIUM, dtype=np.int16)
    cz0, cz1 = cap + 1, cap + 1 + length
    cy = cx = radius + 1
    zz, yy, xx = np.mgrid[0:D[0], 0:D[1], 0:D[2]]
    rad2 = (yy - cy) ** 2 + (xx - cx) ** 2
    body = (rad2 <= radius ** 2) & (zz >= cz0) & (zz < cz1)
    n = int(body.sum())
    g[body] = rng.choice((BONE, MUSCLE, SKIN), size=n,
                         p=np.asarray(fractions) / sum(fractions)).astype(np.int16)
    # TENDON plugs: at each end cap, a ring at mid-radius — where the bone core meets the
    # muscle. This is the assembly placing the connector; adhesion must keep it there.
    for zc in (cz0 + 1, cz1 - 2):
        plug = body & (np.abs(zz - zc) <= 1) \
            & (rad2 <= (radius * 0.60) ** 2) & (rad2 >= (radius * 0.25) ** 2)
        g[plug] = TENDON
    targets = {t: int((g == t).sum()) for t in (BONE, MUSCLE, SKIN, TENDON)}
    return g, D, targets


def assemble_3d(grid, shape, targets, J, connectivity=18, sweeps=90, temp=12.0,
                lam=0.9, seed=0, frozen_type=None):
    """The 2D Metropolis rule, verbatim, on a flat 3D lattice. One copy attempt: pick an
    interior site, propose a random neighbour's type, accept by the Boltzmann rule.

    frozen_type (optional): a brick type that is a SCAFFOLD — its cells are never chosen
    to change and are never created, so they stay exactly as placed. This is how the
    L-system skeleton pins the bone axis (see core/limb.py): adhesion sorts the flesh
    around a bone it can neither move nor grow, which is precisely what a thin cohesive
    rod cannot do for itself (rung 1.5's Rayleigh-Plateau segmentation)."""
    strides = (shape[1] * shape[2], shape[2], 1)
    off = _nd_offsets(strides, connectivity)
    L = grid.ravel().astype(np.int16).tolist()          # a Python list is faster to poke
    Jl = J.tolist()
    area = {t: int((grid == t).sum()) for t in targets}
    frz = frozen_type if frozen_type is not None else -999

    idx = np.arange(len(L)).reshape(shape)
    interior = idx[1:-1, 1:-1, 1:-1].ravel()
    if frozen_type is not None:                         # never pick a scaffold cell to change
        interior = interior[grid.ravel()[interior] != frozen_type]
    rng = np.random.RandomState(seed + 101)
    attempts = sweeps * len(interior)
    sites = interior[rng.randint(0, len(interior), size=attempts)]
    ks = rng.randint(0, len(off), size=attempts)
    us = rng.random_sample(size=attempts)

    for i in range(attempts):
        s = int(sites[i])
        old = L[s]
        new = L[s + off[ks[i]]]
        if new == old or new == frz:                    # scaffold neither moves nor grows
            continue
        Jn, Jo = Jl[new], Jl[old]
        dH = 0.0
        for d in off:
            nb = L[s + d]
            dH += Jn[nb] - Jo[nb]
        if old != MEDIUM:
            a = area[old]
            dH += lam * ((a - 1 - targets[old]) ** 2 - (a - targets[old]) ** 2)
        if new != MEDIUM:
            a = area[new]
            dH += lam * ((a + 1 - targets[new]) ** 2 - (a - targets[new]) ** 2)
        if dH <= 0.0 or us[i] < math.exp(-dH / temp):
            L[s] = new
            if old != MEDIUM:
                area[old] -= 1
            if new != MEDIUM:
                area[new] += 1
    return np.array(L, dtype=np.int16).reshape(shape)


def metrics_3d(grid, shape) -> dict:
    """Facts about a 3D limb. Cylindrical radius per tissue about the long (z) axis, the
    limb's aspect ratio, and — for the typed connector — how the tendon sits: what
    fraction of its neighbours are bone-or-muscle (it should be bonded to both), and its
    exposure to skin-or-medium (it should avoid them)."""
    strides = (shape[1] * shape[2], shape[2], 1)
    off = _nd_offsets(strides, 6)
    L = grid.ravel()
    tissue = grid != MEDIUM
    zz, yy, xx = np.nonzero(tissue)
    cy, cx = yy.mean(), xx.mean()
    out = {"radius": {}, "area": {},
           "z_len": float(zz.max() - zz.min() + 1), "cyl_r": 0.0}
    for t in (BONE, MUSCLE, SKIN):
        m = np.nonzero(grid == t)
        out["radius"][t] = float(np.sqrt((m[1] - cy) ** 2 + (m[2] - cx) ** 2).mean())
        out["area"][t] = int((grid == t).sum())
    out["cyl_r"] = float(np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2).mean())

    ten = np.nonzero(grid.ravel() == TENDON)[0]
    good = bad = total = 0
    for s in ten:
        for d in off:
            nb = L[s + d]
            if nb == MEDIUM:
                continue
            total += 1
            if nb in (BONE, MUSCLE):
                good += 1
            elif nb == SKIN:
                bad += 1
    med = 0
    for s in ten:
        for d in off:
            if L[s + d] == MEDIUM:
                med += 1
    denom = max(len(ten) * len(off), 1)
    out["tendon_bond"] = good / max(total, 1)          # frac of tissue-neighbours that are bone|muscle
    out["tendon_skin_medium"] = (bad + med) / denom     # exposure to the wrong things
    out["tendon_area"] = int(len(ten))
    # z-localisation: tendon should stay clustered at the two ends, not disperse
    if len(ten):
        tz = ten // strides[0]
        out["tendon_z_std"] = float(np.std(tz))
    else:
        out["tendon_z_std"] = 0.0
    return out


def render_3d(grid0, diff, shape, path: Path, scale=7, gap=8):
    """Witness slices: the mid-length CROSS-SECTION (start vs sorted — the tube forming)
    and the LONGITUDINAL slice of the sorted limb (elongation + the tendon plugs at the
    ends). A number is not proof (H-14)."""
    from PIL import Image, ImageDraw

    zc, yc = shape[0] // 2, shape[1] // 2

    def colorize(plane):
        h, w = plane.shape
        rgb = np.zeros((h, w, 3), dtype=np.uint8)
        for t, col in _COLORS.items():
            rgb[plane == t] = col
        return Image.fromarray(rgb, "RGB").resize((w * scale, h * scale), Image.NEAREST)

    panels = [
        ("start: cross-section", colorize(grid0[zc])),
        ("sorted: cross-section", colorize(diff[zc])),
        ("sorted: length (tendon = teal)", colorize(diff[:, yc, :])),
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


def _row(tag, m):
    r, e = m["radius"], m["exposure"]
    return (f"  {tag:<26} bone {r[BONE]:5.1f}  muscle {r[MUSCLE]:5.1f}  "
            f"skin {r[SKIN]:5.1f}   | skin-exposure {e[SKIN]:.2f} vs bone {e[BONE]:.2f}")


def _prove_cross2d(a) -> int:
    sweeps = a.sweeps or 160
    g0, targets = init_blob(seed=a.seed)
    diff = assemble(g0, targets, J_DIFFERENTIAL, sweeps=sweeps, seed=a.seed)
    ctrl = assemble(g0, targets, J_UNIFORM, sweeps=sweeps, seed=a.seed)

    m0, md, mc = metrics(g0), metrics(diff), metrics(ctrl)
    print("\nMEAN RADIUS per tissue (core = small, shell = large):")
    print(_row("scrambled start", m0))
    print(_row("DIFFERENTIAL adhesion", md))
    print(_row("UNIFORM control", mc))

    # areas must be conserved — the sort rearranges, it does not let bone eat the rest
    print("\nAREA conserved (target -> differential):")
    for t in TISSUES:
        print(f"  {NAMES[t]:<8} {targets[t]:>5} -> {md['area'][t]:>5}")

    ok_diff = is_sorted(md)
    ok_ctrl_stays_mixed = not is_sorted(mc)
    # the effect must be BIG relative to the control: the radial spread bone->skin
    spread = lambda m: m["radius"][SKIN] - m["radius"][BONE]
    print(f"\nradial spread bone->skin:  start {spread(m0):+.1f}   "
          f"differential {spread(md):+.1f}   control {spread(mc):+.1f}")

    print()
    if ok_diff and ok_ctrl_stays_mixed and spread(md) > spread(mc) + 3.0:
        print("  PROVEN. Differential adhesion sorted a random pepper of bricks into")
        print("  bone-core / muscle / skin-shell, unattended. The SAME machine with")
        print("  uniform adhesion did NOT sort. The stickiness was the cause; the")
        print("  anatomy was the answer. rung 1 stands.")
        verdict = 0
    elif not ok_diff:
        print("  FAILED: differential adhesion did not produce bone<muscle<skin. The")
        print("  profile is wrong or it needs more sweeps. Iterate J, not the artifact.")
        verdict = 1
    else:
        print("  FAILED: the UNIFORM control ALSO sorted — the machine is forcing it, so")
        print("  this proves nothing about adhesion. The test is void.")
        verdict = 1

    if a.png:
        print(f"\n  -> {render([('scrambled start', g0), ('differential', diff), ('uniform control', ctrl)], Path(a.png))}")
    return verdict


def _prove_limb3d(a) -> int:
    sweeps = a.sweeps or 90
    g0, shape, targets = init_limb_3d(seed=a.seed)
    diff = assemble_3d(g0, shape, targets, J_DIFFERENTIAL_3D, sweeps=sweeps, seed=a.seed)
    ctrl = assemble_3d(g0, shape, targets, J_UNIFORM_3D, sweeps=sweeps, seed=a.seed)
    m0, md, mc = (metrics_3d(g0, shape), metrics_3d(diff, shape), metrics_3d(ctrl, shape))

    def rr(tag, m):
        r = m["radius"]
        return (f"  {tag:<26} bone {r[BONE]:5.1f}  muscle {r[MUSCLE]:5.1f}  "
                f"skin {r[SKIN]:5.1f}   | limb {m['z_len']:.0f} long x {m['cyl_r']:.1f} radius")

    print("\n3D LIMB — cylindrical radius per tissue about the long axis (core small, shell large):")
    print(rr("scrambled start", m0))
    print(rr("DIFFERENTIAL adhesion", md))
    print(rr("UNIFORM control", mc))

    print("\nTYPED CONNECTOR (tendon) — bonded to muscle+bone, shunning skin/medium?")
    print(f"  DIFFERENTIAL  bond {md['tendon_bond']:.2f}   wrong-contact {md['tendon_skin_medium']:.2f}"
          f"   z-spread {md['tendon_z_std']:.1f}")
    print(f"  UNIFORM ctrl  bond {mc['tendon_bond']:.2f}   wrong-contact {mc['tendon_skin_medium']:.2f}"
          f"   z-spread {mc['tendon_z_std']:.1f}")

    layered = (md["radius"][BONE] + 0.5 < md["radius"][MUSCLE]
               and md["radius"][MUSCLE] + 0.5 < md["radius"][SKIN])
    ctrl_mixed = not (mc["radius"][BONE] + 0.5 < mc["radius"][MUSCLE]
                      and mc["radius"][MUSCLE] + 0.5 < mc["radius"][SKIN])
    elongated = md["z_len"] > 2.5 * md["cyl_r"]
    tendon_holds = (md["tendon_bond"] > 0.75
                    and md["tendon_skin_medium"] < mc["tendon_skin_medium"] - 0.03)

    print()
    if layered and ctrl_mixed and elongated and tendon_holds:
        print("  PROVEN. 3D differential adhesion grew concentric tubes — bone core, muscle,")
        print("  skin shell — in an elongated limb, and the TYPED TENDON stayed bonded to")
        print("  muscle+bone while shunning skin and surface, where the uniform control let")
        print("  it drift. Layering AND a rule-placed interface, unattended. rung 1.5 stands.")
        verdict = 0
    else:
        print(f"  NOT YET: layered={layered}  control_mixed={ctrl_mixed}  "
              f"elongated={elongated}  tendon_holds={tendon_holds}")
        print("  Iterate the profile or the sweeps — never the artifact.")
        verdict = 1

    if a.png:
        print(f"\n  -> {render_3d(g0, diff, shape, Path(a.png))}")
    return verdict


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--mode", choices=["cross2d", "limb3d"], default="cross2d",
                    help="cross2d = rung 1 (2D layering); limb3d = rung 1.5 (3D + tendon)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--sweeps", type=int, default=None)
    ap.add_argument("--png", default=None)
    a = ap.parse_args()
    return _prove_limb3d(a) if a.mode == "limb3d" else _prove_cross2d(a)


if __name__ == "__main__":
    raise SystemExit(main())
