"""M04 rigid-covariance: INDEPENDENT hand-derived expectations (exact arithmetic).

Derivation path 1 (closed form, derived by hand in prereg.md):
  For a RIGHT tetrahedron with apex p and orthogonal legs a = (a1, a2, a3)
  along the coordinate axes, uniform density, mass m:
      C_klm = (m/80) * a_k * a_l * (4*delta_kl - 1)
  where C = integral over the solid of (x - c)(x - c)^T dm and c = p + a/4.
  (Unit right tetra: C_xx = 3m/80, C_xy = -m/80 by direct integration;
  anisotropic scaling diag(a) then gives the general form.)

Derivation path 2 (raw monomial moments over a simplex, fully independent
algebraic route to the same numbers):
  For a tetrahedron with vertices p0..p3, edge matrix E = [p1-p0, p2-p0, p3-p0]
  and volume V, the reference-simplex monomial integrals
  int_{T0} u^i v^j w^k dV = i! j! k! / (i+j+k+3)!  give
      int x x^T dV = (V/20) * E * (I3 + J3) * E^T,   J3 = all-ones,
      int x dm = m * (p0+p1+p2+p3)/4,
      C = int x x^T dm - m * c c^T.

Body assembly (textbook):
  COM = sum_k m_k c_k / M,
  I_about_body_COM = sum_k [ tr(C_k) Id - C_k
                             + m_k (|d_k|^2 Id - d_k d_k^T) ],  d_k = c_k - COM.

Both paths use exact rational arithmetic (fractions.Fraction) on integer
geometry and rational densities; no exporter code is imported or called.

Covariance laws under x -> R x + t (R proper):
  volume, mass invariant; c -> R c + t; COM -> R COM + t;
  legs a -> R a  =>  C_k -> R C_k R^T;  d_k -> R d_k  =>  I -> R I R^T
  (fixed/domain basis).  With the co-moving authored frame
  {rotation R, origin t}:  com_body = R^T(R COM + t - t) = COM,
  inertia_body = R^T (R I R^T) R = I  (rotated basis: unchanged).
  Translation alone (R = Id): I invariant, COM -> COM + t.
"""
from __future__ import annotations

import json
import math
from fractions import Fraction
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "prereg_expectations.json"

# ---------------------------------------------------------------- fixture spec
# Three right tetrahedra sharing the apex O=(0,0,0), one per octant
# (+,+,+), (-,+,+), (-,-,+): interiors disjoint, conforming at the shared
# vertex.  Legs chosen distinct per cell; densities distinct.
CELLS = [
    {"cell_id": "cell-x", "legs": (2, 3, 5), "signs": (+1, +1, +1),
     "density": Fraction(1000), "order": (0, 1, 2, 3),
     "apex": (0, 0, 0)},
    {"cell_id": "cell-y", "legs": (4, 2, 3), "signs": (-1, +1, +1),
     "density": Fraction(800), "order": (0, 1, 3, 2),
     "apex": (-20, 0, 0)},
    {"cell_id": "cell-z", "legs": (3, 2, 4), "signs": (-1, -1, +1),
     "density": Fraction(1200), "order": (0, 1, 2, 3),
     "apex": (0, -20, 0)},
]

# ---------------------------------------------------------------- frozen motion
AXIS = (1.0, 1.0, 2.0)          # non-axis-aligned direction
ANGLE_DEG = 37.0                # non-special angle
T_TRANSLATION = (13.0, -7.0, 4.5)


def rodrigues(axis, angle_deg: float) -> np.ndarray:
    u = np.asarray(axis, dtype=np.float64)
    u = u / np.linalg.norm(u)
    th = math.radians(angle_deg)
    K = np.array([[0.0, -u[2], u[1]], [u[2], 0.0, -u[0]], [-u[1], u[0], 0.0]])
    return np.eye(3) + math.sin(th) * K + (1.0 - math.cos(th)) * (K @ K)


def tetra_closed_form(legs, signs, density: Fraction, apex=(0, 0, 0)):
    """Path 1: closed-form right-tetrahedron covariance about its centroid."""
    a = [Fraction(signs[i]) * Fraction(legs[i]) for i in range(3)]
    volume = abs(a[0] * a[1] * a[2]) / 6  # geometric volume is positive
    mass = density * volume
    apex = [Fraction(v) for v in apex]
    centroid = [apex[i] + a[i] / 4 for i in range(3)]
    C = [[mass / 80 * a[i] * a[j] * (4 - 1 if i == j else -1)
          for j in range(3)] for i in range(3)]
    return volume, mass, centroid, C


def tetra_raw_monomial(p0, p1, p2, p3, density: Fraction):
    """Path 2: raw moments via reference-simplex monomial integrals."""
    E = [[Fraction(p1[i] - p0[i]), Fraction(p2[i] - p0[i]),
          Fraction(p3[i] - p0[i])] for i in range(3)]
    det = (E[0][0] * (E[1][1] * E[2][2] - E[1][2] * E[2][1])
           - E[0][1] * (E[1][0] * E[2][2] - E[1][2] * E[2][0])
           + E[0][2] * (E[1][0] * E[2][1] - E[1][1] * E[2][0]))
    volume = abs(det) / 6  # orientation-independent; file order asserts det > 0
    mass = density * volume
    # x = p0 + E q over reference simplex T0 = {q >= 0, sum q <= 1}; the map
    # has constant Jacobian det(E) = 6 V, so physical integrals get 6V:
    #   int_{T0} q dV    = (1/24) * (1,1,1)   -> int x dV  = V r / 4
    #   int_{T0} q q^T dV = (1/120) (I3 + J3) -> int x x^T dV =
    #       V p0 p0^T + p0 (V r/4)^T + (V r/4) p0^T + (V/20)(E E^T + r r^T)
    # with r = E (1,1,1)^T.
    p0 = [Fraction(v) for v in p0]
    r = [sum(E[i][k] for k in range(3)) for i in range(3)]
    sr = [volume * v / 4 for v in r]
    Mxx = [[volume * p0[i] * p0[j] + p0[i] * sr[j] + sr[i] * p0[j]
            + (volume / 20) * (E[i][0] * E[j][0] + E[i][1] * E[j][1]
                               + E[i][2] * E[j][2] + r[i] * r[j])
            for j in range(3)] for i in range(3)]
    centroid = [(Fraction(p0[i]) + Fraction(p1[i]) + Fraction(p2[i])
                 + Fraction(p3[i])) / 4 for i in range(3)]
    # C = int (x-c)(x-c)^T dm = density * int x x^T dV - m c c^T
    C = [[density * Mxx[i][j] - mass * centroid[i] * centroid[j]
          for j in range(3)] for i in range(3)]
    return mass, centroid, C


def inertia_from_cov(C, mass, d):
    """I = tr(C)*Id - C + m(|d|^2 Id - d d^T)  (parallel-axis theorem).

    Amendment 2 fix: the trace term must be tr(C)*delta_ij, NOT tr(C) added to
    every entry.  The original code added tr(C) to the off-diagonals too,
    inflating each off-diagonal by tr(C_k) of every cell (sum 15825 kg m^2
    here) — caught by the whole-body Monte Carlo cross-check siding with the
    exporter while diagonals matched to machine precision.
    """
    tr = C[0][0] + C[1][1] + C[2][2]
    d2 = d[0] * d[0] + d[1] * d[1] + d[2] * d[2]
    I = [[tr * (1 if i == j else 0) - C[i][j]
          + mass * (d2 * (1 if i == j else 0) - d[i] * d[j])
          for j in range(3)] for i in range(3)]
    return I


def main() -> int:
    # ---- exact base properties, two independent derivations asserted equal
    cells_exact = []
    for spec in CELLS:
        legs, signs, rho = spec["legs"], spec["signs"], spec["density"]
        apex = spec["apex"]
        volume, mass, centroid, C_closed = tetra_closed_form(legs, signs, rho,
                                                             apex)
        s = signs
        axis_verts = [tuple(apex),
                      (apex[0] + s[0] * legs[0], apex[1], apex[2]),
                      (apex[0], apex[1] + s[1] * legs[1], apex[2]),
                      (apex[0], apex[1], apex[2] + s[2] * legs[2])]
        # file order must be positively oriented: det[v1-v0, v2-v0, v3-v0] > 0
        verts = [axis_verts[k] for k in spec["order"]]
        e1 = [verts[1][i] - verts[0][i] for i in range(3)]
        e2 = [verts[2][i] - verts[0][i] for i in range(3)]
        e3 = [verts[3][i] - verts[0][i] for i in range(3)]
        det6 = (e1[0] * (e2[1] * e3[2] - e2[2] * e3[1])
                - e1[1] * (e2[0] * e3[2] - e2[2] * e3[0])
                + e1[2] * (e2[0] * e3[1] - e2[1] * e3[0]))
        assert det6 > 0, (spec["cell_id"], det6)
        mass2, centroid2, C_raw = tetra_raw_monomial(
            verts[0], verts[1], verts[2], verts[3], rho)
        assert mass == mass2 and centroid == centroid2, spec["cell_id"]
        assert C_closed == C_raw, f"derivation paths disagree for {spec['cell_id']}"
        cells_exact.append({"cell_id": spec["cell_id"], "legs": legs,
                            "signs": signs, "density": rho, "vertices": verts,
                            "volume": volume, "mass": mass,
                            "centroid": centroid, "C": C_closed})

    total_mass = sum((c["mass"] for c in cells_exact), Fraction(0))
    com = [sum((c["mass"] * c["centroid"][i] for c in cells_exact), Fraction(0))
           / total_mass for i in range(3)]
    I0 = [[Fraction(0)] * 3 for _ in range(3)]
    for c in cells_exact:
        d = [c["centroid"][i] - com[i] for i in range(3)]
        Ik = inertia_from_cov(c["C"], c["mass"], d)
        for i in range(3):
            for j in range(3):
                I0[i][j] += Ik[i][j]
    volume_total = sum((c["volume"] for c in cells_exact), Fraction(0))

    # ---- design assertions (fixture design, frozen BEFORE any exporter run)
    offdiag = [I0[0][1], I0[0][2], I0[1][2]]
    assert all(v != 0 for v in offdiag), f"base off-diagonals not all nonzero: {offdiag}"
    assert all(v != 0 for v in com), f"base COM has a zero component: {com}"
    # compiler constraints learned in iteration 1/1b: manifold vertex links and
    # pairwise-distinct vertex positions -> cells must be disjoint, positions unique
    all_pos = [tuple(map(float, v)) for c in cells_exact for v in c["vertices"]]
    assert len(set(all_pos)) == len(all_pos), "duplicate vertex positions"
    for a in range(len(cells_exact)):
        for b in range(a + 1, len(cells_exact)):
            va = {tuple(map(float, v)) for v in cells_exact[a]["vertices"]}
            vb = {tuple(map(float, v)) for v in cells_exact[b]["vertices"]}
            assert not (va & vb), "cells must not share vertices"

    R = rodrigues(AXIS, ANGLE_DEG)
    ortho_dev = float(np.max(np.abs(R.T @ R - np.eye(3))))
    det_dev = abs(float(np.linalg.det(R)) - 1.0)
    assert ortho_dev < 1e-10 and det_dev < 1e-10, (ortho_dev, det_dev)  # exporter gate
    assert np.all(np.abs(R) > 1e-6), "R must be fully populated (mixing guarantee)"

    # ---- per-run expectations
    I0_f = np.array([[float(I0[i][j]) for j in range(3)] for i in range(3)])
    com_f = np.array([float(v) for v in com])
    RIRt = R @ I0_f @ R.T
    assert np.all(np.abs(RIRt) > 0.0), "rotated tensor must be fully populated"
    t = np.asarray(T_TRANSLATION, dtype=np.float64)

    def mat_f(M):
        arr = np.asarray(M, dtype=np.float64)
        return [[float(x) for x in row] for row in arr] if arr.ndim == 2 \
            else [float(x) for x in arr]

    runs = {
        "run_A0_identity": {"motion": "identity", "frame": {"rotation": np.eye(3).tolist(),
                                                            "origin_m": [0.0, 0.0, 0.0]},
                            "com": mat_f(com_f), "inertia": mat_f(I0_f)},
        "run_A1_translation": {"motion": "v + t", "frame": {"rotation": np.eye(3).tolist(),
                                                            "origin_m": [0.0, 0.0, 0.0]},
                               "com": mat_f(com_f + t), "inertia": mat_f(I0_f)},
        "run_A2_rotation": {"motion": "R v", "frame": {"rotation": np.eye(3).tolist(),
                                                       "origin_m": [0.0, 0.0, 0.0]},
                            "com": mat_f(R @ com_f), "inertia": mat_f(RIRt)},
        "run_A3_rot_then_trans": {"motion": "R v + t", "frame": {"rotation": np.eye(3).tolist(),
                                                                 "origin_m": [0.0, 0.0, 0.0]},
                                  "com": mat_f(R @ com_f + t), "inertia": mat_f(RIRt)},
        "run_B1_translation_comoving": {"motion": "v + t",
                                        "frame": {"rotation": np.eye(3).tolist(),
                                                  "origin_m": T_TRANSLATION},
                                        "com": mat_f(com_f), "inertia": mat_f(I0_f)},
        "run_B2_rotation_comoving": {"motion": "R v",
                                     "frame": {"rotation": R.tolist(),
                                               "origin_m": [0.0, 0.0, 0.0]},
                                     "com": mat_f(com_f), "inertia": mat_f(I0_f)},
        "run_B3_rot_then_trans_comoving": {"motion": "R v + t",
                                           "frame": {"rotation": R.tolist(),
                                                     "origin_m": T_TRANSLATION},
                                           "com": mat_f(com_f), "inertia": mat_f(I0_f)},
    }

    def frac(v):
        return {"num": str(v.numerator), "den": str(v.denominator)}

    document = {
        "prereg_version": "M04-rigid-covariance-prereg-v1",
        "fixture": {
            "cells": [{"cell_id": c["cell_id"], "legs": list(c["legs"]),
                       "signs": list(c["signs"]),
                       "density_kg_m3": float(c["density"]),
                       "apex": list(map(float, c["vertices"][0])),
                       "vertices": [list(map(float, v)) for v in c["vertices"]]}
                      for c in cells_exact],
            "mass_kg": float(total_mass), "volume_m3": float(volume_total),
        },
        "motion": {"axis_non_normalized": list(AXIS), "angle_deg": ANGLE_DEG,
                   "R": R.tolist(), "R_ortho_max_dev": ortho_dev,
                   "R_det_dev": det_dev,
                   "t_translation_m": list(T_TRANSLATION)},
        "exact_base": {
            "mass_kg": frac(total_mass), "volume_m3": frac(volume_total),
            "com_m": [frac(v) for v in com],
            "inertia_com_kg_m2": [[frac(I0[i][j]) for j in range(3)]
                                  for i in range(3)],
            "cells": [{"cell_id": c["cell_id"], "mass_kg": frac(c["mass"]),
                       "volume_m3": frac(c["volume"]),
                       "centroid_m": [frac(v) for v in c["centroid"]],
                       "covariance_centroid_kg_m2": [[frac(v) for v in row]
                                                     for row in c["C"]]}
                      for c in cells_exact],
        },
        "expectations": {
            "mass_kg": float(total_mass), "volume_m3": float(volume_total),
            "runs": runs,
        },
        "tolerance": {
            "kind": "relative",
            "limit": 1e-9,
            "per_quantity_pass_requires": [
                "dev_max = max|got-want| <= 1e-9 * max|want| (entry-wise vs tensor max)",
                "frobenius_ratio = ||got-want||_F / ||want||_F <= 1e-9",
            ],
            "applies_to": ["center_of_mass (3)", "inertia_tensor_about_com (9)",
                           "mass (frame-invariant)", "volume (frame-invariant)"],
        },
        "falsifier": ("Any quantity of any preregistered run outside the frozen "
                      "tolerance REFUTES rigid-motion covariance of the exported "
                      "mass properties. Exporter refusal, non-complete "
                      "export_status, or non-exported group on schema-valid "
                      "fixtures likewise falsifies."),
        "stop_rule": ("Stop when every preregistered run (7) is verdicted for "
                      "every quantity (COM 3, inertia 9, mass, volume). No new "
                      "runs, no tolerance changes, no expectation edits after "
                      "the first exporter invocation."),
        "derivation_paths_agree": True,
    }
    OUT.write_text(json.dumps(document, indent=2, sort_keys=False) + "\n",
                   encoding="utf-8")

    # ---- human-readable summary for prereg.md
    print("== exact base (derivation paths 1 and 2 agree on every cell) ==")
    print(f"mass = {total_mass} kg = {float(total_mass)!r}")
    print(f"volume = {volume_total} m^3 = {float(volume_total)!r}")
    print("COM  =", [str(v) for v in com])
    print("COM f=", [float(v) for v in com])
    print("I0 (exact Fractions):")
    for i in range(3):
        print("  ", [str(I0[i][j]) for j in range(3)])
    print("I0 (float64):")
    for i in range(3):
        print("  ", [repr(float(I0[i][j])) for j in range(3)])
    print("R (frozen float64):")
    for row in R.tolist():
        print("  ", [repr(x) for x in row])
    print(f"R ortho dev {ortho_dev:.3e}, det dev {det_dev:.3e}")
    print("R I R^T (float64):")
    for row in RIRt.tolist():
        print("  ", [repr(x) for x in row])
    print("per-cell:")
    for c in cells_exact:
        print(f"  {c['cell_id']}: m={float(c['mass'])!r} V={float(c['volume'])!r} "
              f"centroid={[float(v) for v in c['centroid']]!r}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
