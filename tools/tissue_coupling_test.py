"""tissue_coupling_test.py -- HEADLESS PROOF THAT TISSUE = SEPARATE TRIANGLE SYSTEMS.

Rule 0, at membrane granularity:
  STATEMENT   skin/muscle/bone are separate triangle systems coupling at shared interface
              nodes (THE_WOLFRAM_FRAME section 3), not one blob.
  PREDICTION  under a prescribed boundary motion of the rigid frame, all three systems
              satisfy displacement continuity at the interfaces within tolerance: after
              each coupling pass |pos_skin - pos_muscle| < tol and |pos_muscle - pos_bone|
              < tol at every shared node; no system diverges.
  FALSIFIER   interface separation exceeds tolerance, or a system diverges (non-finite
              positions, displacement from rest beyond the derived bound, unbounded
              constraint demand).

Every bound below is DERIVED from the prescribed trajectory before the run -- nothing is
chosen to make the test pass. The per-tissue relaxation alphas are scaffold placeholders;
the in-between gets TRAINED later (frame section 5), this only proves the coupling holds.

    python tools/tissue_coupling_test.py     # PASS + continuity report, exit 0
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ChimeraEngine"))

from tissue_systems import RigidSystem, TissueCoupling, build_limb_segment, rot_y  # noqa: E402

K, L, R_NECK = 8, 1.0, 0.2
BELLY = {"bone": 0.3 * L, "muscle": 0.45 * L, "skin": 0.6 * L}
THETA_MAX = np.deg2rad(60.0)
T_DRIVE, T_HOLD = 120, 40
TOL_CONT = 1e-9
SKIN_SOFTNESS = 0.5


def theta_schedule(n: int) -> np.ndarray:
    u = np.clip(np.arange(n) / T_DRIVE, 0.0, 1.0)
    return THETA_MAX * (3.0 * u ** 2 - 2.0 * u ** 3)


def main() -> int:
    systems = build_limb_segment(K=K, L=L, r_neck=R_NECK, belly=BELLY)
    bone, muscle, skin = systems["bone"], systems["muscle"], systems["skin"]
    coupling = TissueCoupling([bone, muscle, skin])

    skin.alpha *= SKIN_SOFTNESS

    print("TISSUE COUPLING -- one limb segment, three SEPARATE triangle systems")
    for s in (bone, muscle, skin):
        a = f"relax alpha={s.alpha:.4g}" if not isinstance(s, RigidSystem) else "kinematic"
        print(f"  {s.name:8} vertices={s.n_vertices:<4} faces={s.n_faces:<4} "
              f"interface nodes={len(s.interface_idx)}  {a}")
    print(f"  shared interface set: {coupling.n_nodes} nodes "
          f"(2 neck rings x {K}), positionally corresponding across systems")

    n = T_DRIVE + T_HOLD
    th = theta_schedule(n)
    poses = [rot_y(t) for t in th]
    bone_rest_far = bone.rest[bone.interface_idx[K:]]
    far_traj = np.stack([bone_rest_far @ R.T for R in poses])
    db_max = float(np.linalg.norm(np.diff(far_traj, axis=0), axis=1).max())
    max_bone_disp = 0.0
    for R in poses:
        max_bone_disp = max(max_bone_disp,
                            float(np.abs(bone.rest @ R.T - bone.rest).max()))
    b_div = max_bone_disp + 2.0 * BELLY["skin"]
    g_bound = 2.0 * db_max

    print(f"\nMOTION: distal end swung 0 -> {np.rad2deg(THETA_MAX):.1f} deg about the proximal "
          f"axis, {T_DRIVE} drive + {T_HOLD} coast steps")
    print("derived bounds (from the prescribed trajectory, before the run):")
    print(f"  max per-step bone displacement at interfaces   db_max = {db_max:.6g}")
    print(f"  divergence bound                               B_div  = {b_div:.6g}")
    print(f"  demand bound                                   G      = {g_bound:.6g}")

    pre_gaps, post_gaps = [], []
    max_disp = {s.name: float(np.abs(s.pos - s.rest).max()) for s in (bone, muscle, skin)}
    finite = True
    coast_start_gap = None
    for t in range(n):
        bone.set_pose(poses[t])
        muscle.spring_relax()
        skin.spring_relax()
        pre, post, _ = coupling.enforce()
        pre_gaps.append(pre)
        post_gaps.append(post)
        if t == T_DRIVE:
            coast_start_gap = pre
        for s in (bone, muscle, skin):
            d = np.abs(s.pos - s.rest)
            if not np.isfinite(d).all():
                finite = False
            max_disp[s.name] = max(max_disp[s.name], float(d.max()))

    bone_exact_far = bone.rest[bone.interface_idx[K:]] @ poses[-1].T
    final_lag = {s.name: float(np.abs(
        s.pos[s.interface_idx[K:]] - bone_exact_far).max())
        for s in (muscle, skin)}
    track_tol = coast_start_gap * (2.0 / 3.0) ** T_HOLD

    c1 = max(post_gaps) < TOL_CONT and finite
    c2 = finite and all(v <= b_div for v in max_disp.values())
    c3 = max(pre_gaps) <= g_bound
    c4 = all(v < track_tol for v in final_lag.values())

    print("\nCONTINUITY REPORT")
    print(f"  C1 interface continuity after enforcement   "
          f"max post-gap {max(post_gaps):.3e}  (tol {TOL_CONT:.0e})   "
          f"{'PASS' if c1 else 'FAIL'}")
    for s in (bone, muscle, skin):
        print(f"       max |pos - rest| {s.name:8} = {max_disp[s.name]:.6g}")
    print(f"  C2 no divergence                              "
          f"(bound B_div = {b_div:.6g}, all finite={finite})   {'PASS' if c2 else 'FAIL'}")
    print(f"  C3 bounded constraint demand                  "
          f"max pre-gap {max(pre_gaps):.6g}  (bound G = {g_bound:.6g})   "
          f"{'PASS' if c3 else 'FAIL'}")
    for s in (muscle, skin):
        print(f"       final distal-ring lag {s.name:8} = {final_lag[s.name]:.3e}")
    print(f"  C4 motion transmitted through all systems     "
          f"(track tol {track_tol:.3e})   {'PASS' if c4 else 'FAIL'}")

    ok = c1 and c2 and c3 and c4
    print("\n" + ("PASS -- three separate triangle systems hold displacement continuity at the "
                  "shared interfaces under prescribed boundary motion."
                  if ok else
                  "FAIL -- falsifier fired: interface separation or divergence beyond bound."))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
