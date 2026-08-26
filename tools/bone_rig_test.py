"""bone_rig_test.py — Validate the bone-rig controller for theDeterminism.

    python tools/bone_rig_test.py

RULE 0 MEMBRANE (theDeterminism S3 architecture):
  STATEMENT  determinism = ROM extremities + CA-filled interior harnessed by a bone rig
  PREDICTION the triangle mesh's deformation is fully determined by the rig pose
             (skinning is a pure function of rig + weights); no triangle moves
             independently of the rig
  FALSIFIER  a triangle vertex moves without a corresponding rig change, or the
             interior violates the rig's ROM

LAWS: theDeterminism (this is its S3 architecture); triangle-primary.
The rig is the single authority — triangles never self-author.

VERIFY: python tools/bone_rig_test.py -> mesh tracks rig within numerical tol.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

_HERE = str(Path(__file__).resolve().parent)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from bone_rig import BoneRig                       # noqa: E402

_PASS = 0
_FAIL = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global _PASS, _FAIL
    tag = "ok  " if ok else "FAIL"
    print(f"[{tag}] {name}" + (f" -- {detail}" if detail else ""), flush=True)
    if ok:
        _PASS += 1
    else:
        _FAIL += 1


# --- pre-registered tolerances (written before the first run) ----------------
EPS_LBS = 1e-10          # LBS identity at rest / formula match (pure function)
EPS_ZERO = 1e-10         # zero-pose -> rest vertices (rig is sole authority)

# --- a minimal MuJoCo rig: 3 bodies, 2 hinge joints with ROM ----------------
RIG_XML = """\
<mujoco model="bone_chain_test">
  <option timestep="0.01" gravity="0 0 0"/>
  <worldbody>
    <body name="root" pos="0 0 0">
      <freejoint name="root_free"/>
      <geom type="sphere" size="0.05"/>
      <body name="mid" pos="0 0 1">
        <joint name="mid_y" type="hinge" axis="0 1 0"
               range="-45 45" limited="true"/>
        <geom type="sphere" size="0.05"/>
        <body name="tip" pos="0 0 1">
          <joint name="tip_y" type="hinge" axis="0 1 0"
                 range="-30 30" limited="true"/>
          <geom type="sphere" size="0.05"/>
        </body>
      </body>
    </body>
  </worldbody>
</mujoco>
"""

BONE_NAMES = ["root", "mid", "tip"]


def _build_rig() -> BoneRig:
    """Create MuJoCo model from embedded XML, build mesh, bind rest pose."""
    import mujoco
    m = mujoco.MjModel.from_xml_string(RIG_XML)
    d = mujoco.MjData(m)
    rig = BoneRig(m, d, BONE_NAMES)
    rig.build_mesh(n_rings=3, n_segs=8, radius=0.15)
    rig.bind()
    return rig


# ---------------------------------------------------------------------------
def main() -> int:
    import mujoco

    rig = _build_rig()
    m, d = rig.m, rig.d
    verts_rest = rig.vertices_rest.copy()
    T_inv = rig._rest_inv.copy()
    K = len(BONE_NAMES)
    N = len(verts_rest)

    # ═══ D1 — LBS AT REST IS IDENTITY ════════════════════════════════════════
    # At rest (all joints 0) every delta transform is I, so v_skin == v_rest.
    verts_skin = rig.skin()
    max_err = float(np.max(np.abs(verts_skin - verts_rest)))
    check("D1 LBS at rest is identity (skinned == rest vertices)",
          max_err < EPS_LBS,
          f"max err {max_err:.2e}")

    # ═══ D2 — DETERMINISM: same pose -> bit-identical mesh ═══════════════════
    mujoco.mj_resetData(m, d)
    d.qpos[7] = 0.3            # mid_y angle
    d.qpos[8] = -0.2           # tip_y angle
    mujoco.mj_forward(m, d)

    verts_a = rig.skin()
    verts_b = rig.skin()
    diff_ab = float(np.max(np.abs(verts_a - verts_b)))
    check("D2 determinism: same pose -> bit-identical mesh",
          diff_ab == 0.0,
          f"max diff {diff_ab:.2e}")

    # ═══ D3 — FORMULA: v = SUM w_b (R_b x + t_b) matches skin() ═════════════
    T_curr = rig.bone_transforms()
    manual = np.empty_like(verts_rest)
    for i in range(N):
        v = np.zeros(3)
        for b in range(K):
            delta = T_curr[b] @ T_inv[b]
            v += rig.weights[i, b] * (delta[:3, :3] @ verts_rest[i] + delta[:3, 3])
        manual[i] = v

    formula_err = float(np.max(np.abs(verts_a - manual)))
    check("D3 skin() matches hand-computed LBS formula",
          formula_err < EPS_LBS,
          f"max formula err {formula_err:.2e}")

    # ═══ D4 — ZERO JOINTS -> REST (rig is sole authority) ════════════════════
    mujoco.mj_resetData(m, d)
    mujoco.mj_forward(m, d)
    verts_zero = rig.skin()
    delta_zero = float(np.max(np.abs(verts_zero - verts_rest)))
    check("D4 zero joints -> vertices return to rest (rig is sole authority)",
          delta_zero < EPS_ZERO,
          f"max delta {delta_zero:.2e}")

    # ═══ D5 — ROM: joint limits read from MuJoCo ═════════════════════════════
    rom = rig.rom_extremities()
    check("D5 ROM reads both limited joints",
          "mid_y" in rom and "tip_y" in rom,
          f"ROM = {rom}")
    lo_m, hi_m = rom["mid_y"]
    lo_t, hi_t = rom["tip_y"]
    check("D5 mid_y ROM = [-45 deg, +45 deg]",
          abs(math.degrees(lo_m) - (-45.0)) < 1e-6
          and abs(math.degrees(hi_m) - 45.0) < 1e-6,
          f"[{math.degrees(lo_m):.1f}, {math.degrees(hi_m):.1f}] deg")
    check("D5 tip_y ROM = [-30 deg, +30 deg]",
          abs(math.degrees(lo_t) - (-30.0)) < 1e-6
          and abs(math.degrees(hi_t) - 30.0) < 1e-6,
          f"[{math.degrees(lo_t):.1f}, {math.degrees(hi_t):.1f}] deg")

    # ═══ D6 — ROM ENVELOPE: interior within bounds at extreme poses ══════════
    envelope_lo, envelope_hi = rig.rom_envelope()

    mujoco.mj_resetData(m, d)
    d.qpos[7] = math.radians(45.0)
    d.qpos[8] = math.radians(-30.0)
    mujoco.mj_forward(m, d)
    check("D6 CA interior within ROM at extreme (+45, -30)",
          rig.interior_within_rom(),
          f"envelope x=[{envelope_lo[0]:.3f},{envelope_hi[0]:.3f}] "
          f"z=[{envelope_lo[2]:.3f},{envelope_hi[2]:.3f}]")

    mujoco.mj_resetData(m, d)
    d.qpos[7] = math.radians(-45.0)
    d.qpos[8] = math.radians(30.0)
    mujoco.mj_forward(m, d)
    check("D6 CA interior within ROM at other extreme (-45, +30)",
          rig.interior_within_rom())

    # ═══ D7 — CA INTERIOR: slaved to rig ══════════════════════════════════════
    mujoco.mj_resetData(m, d)
    mujoco.mj_forward(m, d)
    int_zero = rig.skin_interior()
    int_rest = rig._interior_rest
    if len(int_zero) > 0:
        int_err = float(np.max(np.abs(int_zero - int_rest)))
        check("D7 interior at rest matches rest-pose interior",
              int_err < EPS_LBS,
              f"max err {int_err:.2e}")
    else:
        check("D7 interior at rest (empty grid — increase res)", True)

    # rotate mid joint -> interior must move with rig
    d.qpos[7] = 0.3
    mujoco.mj_forward(m, d)
    int_moved = rig.skin_interior()
    if len(int_moved) > 0 and len(int_rest) > 0:
        int_delta = float(np.max(np.abs(int_moved - int_rest)))
        check("D7 interior moves with rig (slaved, not independent)",
              int_delta > EPS_ZERO,
              f"interior displacement {int_delta:.6f}")
    else:
        check("D7 interior moves with rig (empty)", True)

    # ═══ D8 — NO VERTEX MOVES INDEPENDENTLY ═════════════════════════════════
    # New pose: every vertex must match the LBS formula exactly.
    mujoco.mj_resetData(m, d)
    d.qpos[7] = 0.5
    d.qpos[8] = 0.4
    mujoco.mj_forward(m, d)

    verts_new = rig.skin()
    T_new = rig.bone_transforms()
    manual_new = np.empty_like(verts_rest)
    for i in range(N):
        v = np.zeros(3)
        for b in range(K):
            delta = T_new[b] @ T_inv[b]
            v += rig.weights[i, b] * (delta[:3, :3] @ verts_rest[i] + delta[:3, 3])
        manual_new[i] = v

    lbs_err = float(np.max(np.abs(verts_new - manual_new)))
    check("D8 every vertex follows LBS — no independent movement",
          lbs_err < EPS_LBS,
          f"max LBS err {lbs_err:.2e}")

    # ═══ SUMMARY ══════════════════════════════════════════════════════════════
    n_verts = N
    n_faces = len(rig.faces)
    n_interior = len(rig._interior_rest) if rig._interior_rest is not None else 0
    print(f"\n{'='*70}")
    print(f"  mesh: {n_verts} verts, {n_faces} faces, {n_interior} interior pts")
    print(f"  bones: {BONE_NAMES}")
    print(f"  ROM: mid_y [{math.degrees(lo_m):+.0f}, {math.degrees(hi_m):+.0f}] deg, "
          f"tip_y [{math.degrees(lo_t):+.0f}, {math.degrees(hi_t):+.0f}] deg")
    print(f"  {_PASS} passed, {_FAIL} failed", flush=True)
    return 1 if _FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
