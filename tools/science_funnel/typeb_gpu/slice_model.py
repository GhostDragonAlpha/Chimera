"""slice_model.py — single source of truth for the TypeB-P2 probe equations.

BOTH the CPU float64 reference and the Warp GPU kernel take every constant
from this module so the two backends cannot drift. Every value derives from
repo source (see PREREG.md for the chain); nothing is tuned.

Geometry (stability-derived, PREREG.md):
  3 membranes, each a 3x3-vertex skin sheet (side 2s), chained along +x with
  glue gaps. Springs on structural edges only. Ground plane y=0, gravity -y.
"""
from __future__ import annotations

import numpy as np

# ── engine constants (membrane_tick.cpp) ────────────────────────────────────
G_EARTH = np.float32(9.81)          # membrane_tick.cpp:45
DT_F32 = np.float32(1.0 / 300.0)    # 300 Hz convention; tick ~3.34 ms
DT = float(DT_F32)                  # both backends use THIS identical dt
F_CAP_MULT = 50.0                   # membrane_tick.cpp:858 (floor, not launcher)

# ── sourced material constants (tools/matter_kernel/constants.py) ───────────
RHO_SKIN = 1100.0        # mat.skin density kg/m^3
E_SKIN = 15.0e6          # mat.skin Young's modulus Pa
E_GLUE = 2.0e9           # mat.wood_glue Young's modulus Pa

# ── geometry (derived from stability, PREREG.md) ────────────────────────────
S = 0.75                 # vertex spacing m  (omega*dt = 1.56 < 2)
T = 0.002                # skin thickness m
GAP = 0.002              # glue bond-line thickness m (bonded membranes touch;
                         # the glue layer IS the gap — see PREREG addendum)
SIDE = 2 * S             # membrane side 1.5 m
N_MEMBRANES = 3
GRID = 3                 # 3x3 vertices per membrane
VERTS_PER_MEM = GRID * GRID
NV = VERTS_PER_MEM * N_MEMBRANES

# ── derived masses (matter_kernel/definition.py:71) ─────────────────────────
M_MEMBRANE = SIDE * SIDE * T * RHO_SKIN      # 4.95 kg, area x thickness x density
M_VERT = M_MEMBRANE / VERTS_PER_MEM          # 0.55 kg

# ── derived stiffnesses ──────────────────────────────────────────────────────
K_MEM = E_SKIN * T                       # 30,000 N/m (continuum correspondence)
K_GLUE = E_GLUE * (T * S) / GAP          # 1.5e9 N/m (B2: bond is a third material;
                                         # PREREG addendum: prereg's 6e4 was arithmetic)

# ── ground contact (membrane_tick.cpp:842-860) ──────────────────────────────
K_GROUND = M_VERT * float(G_EARTH) / 0.01        # engine rest-sink: k*s = m*g
C_GROUND = 2.0 * np.sqrt(K_GROUND * M_VERT)      # critically damped, no restitution

# ── substep derivation (PREREG addendum): the bond stiffness is explicitly
# unintegrable at dt=1/300 (omega*dt ~ 174 >> 2); substep count derives from
# the same 1.557 stability margin as the membrane spacing. The frequency bound
# carries the factor 2 of FREE-FREE vibration (a bond connects two DYNAMIC
# vertices; the pair mode is sqrt(2k/m) — Gershgorin on the Laplacian gives
# eigenvalues up to 2x the diagonal sum). A first derivation without the
# factor 2 was falsified numerically pre-run (omega*h measured 2.198 > 2). ───
OMEGA_MAX = np.sqrt(2.0 * (K_GLUE + 2.0 * K_MEM + K_GROUND) / M_VERT)
DT_SUB = 1.557 / OMEGA_MAX
N_SUB = int(np.ceil(DT / DT_SUB))

# ── float32 twins (the GPU runs float32; BOTH backends use these values so
# the CPU reference judges float64-of-float32 arithmetic, not a different dt
# or a different constant) ────────────────────────────────────────────────────
G_EARTH_F32 = np.float32(G_EARTH)
F_CAP_MULT_F32 = np.float32(F_CAP_MULT)
M_VERT_F32 = np.float32(M_VERT)
INV_M_F32 = np.float32(1.0 / M_VERT)
K_GROUND_F32 = np.float32(K_GROUND)
C_GROUND_F32 = np.float32(C_GROUND)


def build_topology() -> dict:
    """Membrane vertices + structural edges + glue bonds. Identical arrays are
    handed to both backends; rest lengths follow the geometry above."""
    verts = []          # (NV, 3) rest layout, sheet in the x-z plane, y = up
    for m in range(N_MEMBRANES):
        x0 = m * (SIDE + GAP)
        for gy in range(GRID):
            for gx in range(GRID):
                verts.append((x0 + gx * S, 0.0, gy * S))
    verts = np.asarray(verts, dtype=np.float64)

    springs = []        # (i, j, rest_length, k)
    for m in range(N_MEMBRANES):
        b = m * VERTS_PER_MEM
        for gy in range(GRID):
            for gx in range(GRID):
                v = b + gy * GRID + gx
                if gx + 1 < GRID:
                    springs.append((v, v + 1, S, K_MEM))
                if gy + 1 < GRID:
                    springs.append((v, v + GRID, S, K_MEM))
    # glue bonds: facing-edge vertex pairs across each gap (gx = GRID-1 side)
    for m in range(N_MEMBRANES - 1):
        b0 = m * VERTS_PER_MEM
        b1 = (m + 1) * VERTS_PER_MEM
        for gy in range(GRID):
            springs.append((b0 + gy * GRID + (GRID - 1), b1 + gy * GRID, GAP, K_GLUE))

    sp = np.asarray(springs, dtype=np.float64)
    return {
        "rest_layout": verts,
        "spring_i": sp[:, 0].astype(np.int32),
        "spring_j": sp[:, 1].astype(np.int32),
        "spring_rest": sp[:, 2],
        "spring_k": sp[:, 3],
        "n_springs": len(springs),
    }


def initial_state(seed: int, height: float, perturb: float,
                  perturb_pos: bool = True) -> tuple[np.ndarray, np.ndarray]:
    """Matched init, QUANTIZED THROUGH float32: both backends start from the
    f64-of-f32 values, so a measured discrepancy is integrator noise, never a
    different starting point. (Pre-run finding: the raw layout differs across
    the f32 cast by ~1e-7 m, which at k_glue=1.5e9 N/m is a ~150 N phantom
    force — any state transfer across precisions must quantize.)"""
    rng = np.random.default_rng(seed)
    topo = build_topology()
    pos = topo["rest_layout"].copy()
    pos[:, 1] += height
    vel = np.zeros_like(pos)
    if perturb > 0.0:
        if perturb_pos:
            pos += rng.uniform(-perturb, perturb, size=pos.shape)
        vel += rng.uniform(-perturb, perturb, size=pos.shape)
    return pos.astype(np.float32).astype(np.float64),         vel.astype(np.float32).astype(np.float64)


def describe() -> dict:
    return {
        "g_earth": float(G_EARTH), "dt": DT,
        "side_m": SIDE, "spacing_m": S, "thickness_m": T, "glue_gap_m": GAP,
        "n_membranes": N_MEMBRANES, "verts": NV,
        "mass_total_kg": M_MEMBRANE * N_MEMBRANES, "mass_vertex_kg": M_VERT,
        "k_membrane_N_per_m": K_MEM, "k_glue_N_per_m": K_GLUE,
        "k_ground_N_per_m": float(K_GROUND), "c_ground_N_s_per_m": float(C_GROUND),
        "f_cap_mult": F_CAP_MULT,
    }
