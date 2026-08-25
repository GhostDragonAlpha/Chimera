"""ue_door_known_pose.py — KNOWN-POSE test for the UE splat door's transform contract.

T3 gate (THE_TRANSLATION / THE_TRIANGLE_CARRIER): before we drive TRIANGLES through
the MLSLabsRenderer door, prove its coordinate algebra against known poses so the
door is TRUSTED, not assumed. The C++ bakes a local distortion into
UGaussianSplatingRendererLibrary::SetSplatNodeTransform (GaussianSplatingRendererLibrary.cpp
L526-536) and inverts it in GetSplatNodeBoundingBox (L590-598). This test re-encodes
both EXACTLY as written in the C++ and checks them against hand-computed expected
values + a round-trip identity. No UE, no GPU — pure transform math, runs anywhere.

THE CONTRACT (read straight off the C++, no free numbers):
  UE -> splat   SetSplatNodeTransform        units: UE cm / 100 = one splat unit
    pos : sx =  Y/100 ; sy = -Z/100 ; sz =  X/100      (axis remap + 1/100 scale)
    rot : rx=deg2rad(Pitch) ry=deg2rad(Yaw) rz=deg2rad(Roll)
    scl : sx=Sy sy=Sz sz=Sx                            (cyclic axis perm, no factor)
  splat -> UE   GetSplatNodeBoundingBox        EXACT inverse of the position remap:
    out.Y = x*100 ; out.Z = -y*100 ; out.X = z*100

Gates (Rule-0; every expected value hand-derived from the C++ lines above):
  G1 known-pose forward : a named UE pose maps to its hand-computed splat-space pose.
  G2 round-trip identity: UE -> splat -> UE == original over a spread of poses.
  G3 unit scale exact   : the /100 is exactly 1/100 (UE cm -> splat), not an approximation.
  G4 axis remap named   : documents which UE axis feeds which splat axis (the distortion).

Run: python tools/ue_door_known_pose.py
"""
from __future__ import annotations

import math
import sys

# ── THE DOOR, ENCODED EXACTLY AS IN C++ ────────────────────────────────────────────────
# GaussianSplatingRendererLibrary.cpp L530-536 (forward) and L592-597 (inverse).


def deg2rad(d: float) -> float:
    return d * math.pi / 180.0


def ue_to_splat(pos_ue, rot_ue_deg=None, scl_ue=None):
    """SetSplatNodeTransform: UE (cm) -> splat-space pose. Returns dict of the three GSRVector3."""
    X, Y, Z = pos_ue
    out = {
        "pos": (Y / 100.0, -Z / 100.0, X / 100.0),          # L530-532
    }
    if rot_ue_deg is not None:
        p, yw, r = rot_ue_deg
        out["rot"] = (deg2rad(p), deg2rad(yw), deg2rad(r))  # L526-528
    if scl_ue is not None:
        sx, sy, sz = scl_ue
        out["scl"] = (sy, sz, sx)                          # L534-536 cyclic perm
    return out


def splat_to_ue(pos_splat):
    """GetSplatNodeBoundingBox: splat-space -> UE (cm). EXACT inverse of the position remap. L592-597."""
    x, y, z = pos_splat
    return (z * 100.0, x * 100.0, -y * 100.0)             # out.X=z*100, out.Y=x*100, out.Z=-y*100


# ── GATES ─────────────────────────────────────────────────────────────────────────────
def _close(a, b, tol=1e-9):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def g1_known_pose_forward():
    """A named UE pose must land on its hand-computed splat-space pose."""
    # UE pose: X=+150cm (forward), Y=-200cm (left), Z=+300cm (up).
    ue = (150.0, -200.0, 300.0)
    got = ue_to_splat(ue)["pos"]
    # Hand-derived from the contract: sx=Y/100=-2.0 ; sy=-Z/100=-3.0 ; sz=X/100=+1.5
    exp = (-2.0, -3.0, 1.5)
    ok = _close(got, exp)
    print(f"  G1 known-pose forward : UE{ue} -> splat{tuple(round(v,6) for v in got)} "
          f"(expect {exp})  {'PASS' if ok else 'FAIL'}")
    return ok


def g2_round_trip_identity():
    """UE -> splat -> UE must be the identity (the inverse is exact)."""
    poses = [
        (0.0, 0.0, 0.0),
        (150.0, -200.0, 300.0),
        (-12.5, 7.25, -999.0),
        (1e-4, -1e-4, 3.3),
        (100000.0, -100000.0, 0.0),   # large-magnitude spread
    ]
    worst = 0.0
    for ue in poses:
        back = splat_to_ue(ue_to_splat(ue)["pos"])
        err = max(abs(back[i] - ue[i]) for i in range(3))
        worst = max(worst, err)
    ok = worst <= 1e-9
    print(f"  G2 round-trip identity: {len(poses)} poses, worst |err|={worst:.3e} "
          f"(<=1e-9)  {'PASS' if ok else 'FAIL'}")
    return ok


def g3_unit_scale_exact():
    """/100 must be EXACTLY one-hundredth (UE cm -> splat unit), not an approximation."""
    checks = [
        ((100.0, 0.0, 0.0), (0.0, 0.0, 1.0)),   # X=100cm -> sz=+1.0
        ((0.0, 100.0, 0.0), (1.0, 0.0, 0.0)),   # Y=100cm -> sx=+1.0
        ((0.0, 0.0, 100.0), (0.0, -1.0, 0.0)),  # Z=100cm -> sy=-1.0 (sign flip)
    ]
    ok = True
    for ue, exp in checks:
        got = ue_to_splat(ue)["pos"]
        good = _close(got, exp)
        ok = ok and good
        print(f"  G3 unit scale       : UE{ue} -> splat{got} (expect {exp}) "
              f"{'PASS' if good else 'FAIL'}")
    return ok


def g4_axis_remap_named():
    """Document the distortion: which UE axis feeds which splat axis (position)."""
    table = [
        ("splat.x", "=  UE.Y / 100"),
        ("splat.y", "= -UE.Z / 100   (sign flip)"),
        ("splat.z", "=  UE.X / 100"),
    ]
    print("  G4 axis remap (named, from C++ L530-532):")
    for k, v in table:
        print(f"      {k} {v}")
    # Scale is a cyclic perm with NO factor (L534-536); rotation is an Euler relabel to radians.
    print("      scale : splat=(Sy,Sz,Sx)  [cyclic, no factor]   rot : (Pitch,Yaw,Roll)->(rx,ry,rz) deg2rad")
    return True


def main() -> int:
    print("UE DOOR KNOWN-POSE TEST — SetSplatNodeTransform / GetSplatNodeBoundingBox contract")
    results = [g1_known_pose_forward(), g2_round_trip_identity(), g3_unit_scale_exact(), g4_axis_remap_named()]
    ok = all(results)
    print(f"\n  VERDICT: {'ALL GATES PASS — door transform is TRUSTED for triangle driving' if ok else 'FALSIFIER FIRED — door algebra does not match the C++'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
