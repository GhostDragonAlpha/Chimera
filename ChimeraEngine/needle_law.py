"""needle_law.py -- the million-needle law: a groove IS a closed form.

Shared by `million_needles.py` (the standalone experiment) and the deck's
`story/needles` membrane (the live viewer).  Everything here is deterministic:
positions are a function of the pass clock, and a SWITCH solves for the target
rail's phase at the throw instant so the needle continues from where it is onto
the new rail -- a real railroad join, not a teleport.

Groove columns (N, 10) float32:
  0  type           T_ORBIT / T_STREAM / T_PLANE / T_SHELL
  1  radius / amp   orbit radius, stream wobble amp, plane radius, shell radius
  2  angular speed  radians per pass
  3  phase / lat0   phi0 (orbit/stream/plane), latitude offset (shell)
  4  tilt           orbit tilt, plane z-ripple amp, shell unused
  5  offset         stream along-axis offset, plane radial offset
  6  v              stream speed, plane spiral rate, shell lat drift
  7  center x
  8  center y
  9  center z

THE CONNECT: for a switch at pass k, choose the MEMBER OF THE TARGET RAIL
FAMILY that passes through the needle's current position -- solve the free
family parameters (radius, tilt, phase, offsets) from the point.  A switch is
a JOIN, not a teleport, and any needle can join any rail.
"""
from __future__ import annotations

import numpy as np

T_ORBIT, T_STREAM, T_PLANE, T_SHELL = 0.0, 1.0, 2.0, 3.0

COLOR = {
    T_ORBIT: (0.35, 0.60, 1.00),
    T_STREAM: (0.10, 0.90, 0.90),
    T_PLANE: (1.00, 0.30, 0.90),
    T_SHELL: (0.60, 1.00, 0.40),
}


def make_grooves(n: int = 1_000_000, seed: int = 7) -> np.ndarray:
    rng = np.random.default_rng(seed)
    g = np.zeros((n, 10), np.float32)
    g[:, 0] = rng.choice([T_ORBIT, T_STREAM, T_PLANE, T_SHELL], n)
    g[:, 1] = rng.uniform(4.0, 14.0, n)
    g[:, 2] = rng.uniform(0.01, 0.08, n)
    g[:, 3] = rng.uniform(0.0, 6.2832, n)
    g[:, 4] = rng.uniform(-1.2, 1.2, n)
    g[:, 6] = rng.uniform(-0.05, 0.05, n)
    g[:, 7] = rng.normal(0.0, 0.3, n)
    g[:, 8] = rng.normal(0.0, 0.3, n)
    g[:, 9] = rng.normal(0.0, 0.3, n)
    return g


def positions(g: np.ndarray, k: float) -> np.ndarray:
    """Closed-form needle positions at pass clock k (the groove IS the law)."""
    th = g[:, 2] * k + g[:, 3]
    ct = np.cos(th)
    st = np.sin(th)
    pos = np.zeros((g.shape[0], 3), np.float32)

    m0 = g[:, 0] == T_ORBIT
    if m0.any():
        pos[m0, 0] = g[m0, 1] * ct[m0] + g[m0, 7]
        pos[m0, 1] = g[m0, 1] * st[m0] * np.cos(g[m0, 4]) + g[m0, 8]
        pos[m0, 2] = g[m0, 1] * st[m0] * np.sin(g[m0, 4]) + g[m0, 9]

    m1 = g[:, 0] == T_STREAM
    if m1.any():
        pos[m1, 0] = g[m1, 6] * th[m1] + g[m1, 5] + g[m1, 7]
        pos[m1, 1] = g[m1, 1] * st[m1] + g[m1, 8]
        pos[m1, 2] = g[m1, 1] * ct[m1] + g[m1, 9]

    m2 = g[:, 0] == T_PLANE
    if m2.any():
        u = 0.3 + g[m2, 5] + g[m2, 6] * th[m2]
        pos[m2, 0] = g[m2, 1] * u * ct[m2] + g[m2, 7]
        pos[m2, 1] = g[m2, 1] * u * st[m2] + g[m2, 8]
        pos[m2, 2] = g[m2, 4] * np.sin(3.0 * th[m2]) + g[m2, 9]

    m3 = g[:, 0] == T_SHELL
    if m3.any():
        th3 = g[m3, 2] * k + g[m3, 5]        # shell lon phase rides in col5
        lat = g[m3, 3] + g[m3, 6] * th3
        lon = th3
        pos[m3, 0] = g[m3, 1] * np.cos(lat) * np.cos(lon) + g[m3, 7]
        pos[m3, 1] = g[m3, 1] * np.cos(lat) * np.sin(lon) + g[m3, 8]
        pos[m3, 2] = g[m3, 1] * np.sin(lat) + g[m3, 9]

    return pos


def connect_phase(pos: np.ndarray, k: float, target: np.ndarray) -> np.ndarray:
    """Choose the member of the target rail family through ``pos`` at pass ``k``.

    Returns an (n, 10) param block.  Each family has enough free parameters
    (radius, tilt, phase, offsets) to pass through ANY point -- the join solves
    them from the point's coordinates, so a switch is exact for every needle.
    """
    pos = np.ascontiguousarray(pos, dtype=np.float64)
    target = np.asarray(target, dtype=np.float64)
    n = pos.shape[0]
    block = np.tile(target, (n, 1))
    om, v = target[2], target[6]
    cx, cy, cz = target[7], target[8], target[9]
    dx = pos[:, 0] - cx
    dy = pos[:, 1] - cy
    dz = pos[:, 2] - cz

    if target[0] == T_ORBIT:
        # (x, y, z) = (R cos t, R sin t cos(phi), R sin t sin(phi))
        r = np.sqrt(dy * dy + dz * dz)
        block[:, 1] = np.sqrt(dx * dx + r * r)
        th = np.arctan2(r, dx)
        block[:, 3] = th - om * k
        block[:, 4] = np.where(r > 1e-9, np.arctan2(dz, dy), 0.0)

    elif target[0] == T_STREAM:
        # (x, y, z) = (v t + xoff, R sin t, R cos t)
        block[:, 1] = np.sqrt(dy * dy + dz * dz)
        th = np.arctan2(dy, dz)
        block[:, 3] = th - om * k
        block[:, 5] = dx - v * th

    elif target[0] == T_PLANE:
        # (x, y, z) = (R u cos t, R u sin t, tilt sin 3t), u = 0.3 + rho + v t
        dist = np.sqrt(dx * dx + dy * dy)
        th = np.arctan2(dy, dx)
        block[:, 3] = th - om * k
        block[:, 5] = np.where(dist > 1e-9, dist / target[1] - 0.3 - v * th, 0.0)
        block[:, 9] = pos[:, 2] - target[4] * np.sin(3.0 * th)

    elif target[0] == T_SHELL:
        # lat = lat0 + v*lon ; lon = om*k + phi0 (phase in col5)
        block[:, 1] = np.sqrt(dx * dx + dy * dy + dz * dz)
        lat = np.arcsin(np.clip(dz / np.maximum(block[:, 1], 1e-9), -1.0, 1.0))
        th = np.arctan2(dy, dx)
        block[:, 5] = th - om * k
        block[:, 3] = lat - v * th
        block[:, 6] = v

    return block.astype(np.float32)


def apply_switch(grooves: np.ndarray, ev: dict, k: float,
                 snapshots: dict | None = None) -> float:
    """Apply one switch event, connecting rails.  Returns mean connect error."""
    lo, n = ev["lo"], ev["n"]
    if lo + n > grooves.shape[0]:
        return 0.0
    sl = slice(lo, lo + n)
    if snapshots is not None:
        snapshots[k] = grooves[sl].copy()
    pos_now = positions(grooves[sl], k)
    block = connect_phase(pos_now, k, np.asarray(ev["target"], np.float32))
    grooves[sl] = block
    err = float(np.abs(positions(block, k) - pos_now).max())
    return err


def groove_counts(g: np.ndarray) -> list[int]:
    return [int((g[:, 0] == t).sum()) for t in (T_ORBIT, T_STREAM, T_PLANE, T_SHELL)]
