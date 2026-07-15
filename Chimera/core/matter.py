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
           MUSCLE: (176, 58, 62), SKIN: (206, 160, 120)}


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


def _row(tag, m):
    r, e = m["radius"], m["exposure"]
    return (f"  {tag:<26} bone {r[BONE]:5.1f}  muscle {r[MUSCLE]:5.1f}  "
            f"skin {r[SKIN]:5.1f}   | skin-exposure {e[SKIN]:.2f} vs bone {e[BONE]:.2f}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--sweeps", type=int, default=160)
    ap.add_argument("--png", default=None)
    a = ap.parse_args()

    g0, targets = init_blob(seed=a.seed)
    diff = assemble(g0, targets, J_DIFFERENTIAL, sweeps=a.sweeps, seed=a.seed)
    ctrl = assemble(g0, targets, J_UNIFORM, sweeps=a.sweeps, seed=a.seed)

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


if __name__ == "__main__":
    raise SystemExit(main())
