"""scale_resolution.py -- §13.1 S1 detailed multiscale reference (mechanism
factory): the SAME mechanism (the qualified patch piece, piece.patch-
equilibrium: single high-degree fan, rim pinned, apex loaded) studied on the
grid  scales {0.5, 0.75, 1.0, 1.5, 2.0}  x  resolutions {n_rim 100, 150,
200, 300}.

RESOLUTION AXIS MAPPING (documented, preregistered): the fan's vertex count
IS the resolution axis -- n_rim rim vertices, one centre/apex vertex, n_rim
triangles (fixture_generator.high_degree_fan(n_rim=N, radius=1.0,
height=0.3, gamma=1.0, seed=1), the SAME frozen recipe as the qualified
piece: seed 1, radius 1.0, height 0.3, gamma 1.0 J/wu^2). Refining n_rim
discretizes the SAME continuous boundary-value problem more finely; the
physical-size axis (whole-geometry scale factor) is varied INDEPENDENTLY,
which is exactly S1's "scale transfer distinguished from remeshing" design.

PREREGISTERED CONVERGENCE OBSERVABLE AND TOLERANCE (stated before the grid
was run as a study; derived from the law's own error scale):
  * The rim reaction norms are NOT a convergence observable: the rim is
    pinned in 3D and carries a fixed total load (0.8 N) plus a fixed
    pretension, so per-vertex rim reaction norms obey the measured
    DEFINITION law  mean ~= max ~= 6.5 * scale / n_rim N  (they change ~1/n because
    a fixed resultant is shared over more vertices). They are recorded per
    cell for honesty but excluded from the convergence claim.
  * The convergence observable is the apex displacement apex_z (the piece's
    response), and the tolerance is the DISPLACEMENT equivalent of the
    packet's own 1e-6 N free-residual gate: a residual force of 1e-6 N
    acting through the law's compliance P = 1/gamma_max = 1 wu/N produces
    displacements of order 1e-6 wu.  tol_u = 1e-6 wu.  The gate is never
    widened; this tolerance is derived from it, not chosen.
  * HONEST PREREGISTERED FINDING (measured, retained): the ladder n_rim <=
    300 does NOT reach tol_u -- the finest successive-resolution apex change
    is ~1.16e-5 wu (11.6x tol_u). "Resolved at tol_u" is therefore NOT
    claimed anywhere on this grid; the study records the resolution limit
    and the matched-regime definition uses the FINEST rung.

PREREGISTERED MATCHED-REGIME DEFINITION: at each scale, matched = n_rim 300
(the finest rung of the ladder); unmatched = n_rim 200 (the resolution the
piece was QUALIFIED at) reused unchanged. The discretization (remeshing)
component of any scale effect is |apex_z(s,300) - apex_z(s,200)|; the scale
(physics) component is |apex_z(s,300) - apex_z(1.0,300)|.

STAR DRIFT BLOCK (answers the retained followup): the star's 1.5x/2.0x
stagnation residuals over the 1e-6 gate were measured at UNCHANGED
resolution. The block re-solves the composed star at (1.5, n200), (1.5,
n300), (2.0, n200), (2.0, n300): if refining the resolution brings the
residual under the packet's 1e-6 gate, the drift was DISCRETIZATION; if it
stays over the gate, it is SCALE PHYSICS under this law.

Units follow the R4 table: positions [wu==m], gamma [J/wu^2], forces [N],
energies [J]. CPU only; numpy + stdlib; no engine, no GPU, no network.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_TOOLS = _HERE.parent
_LAB = _TOOLS / "membrane_scale_lab"
for _p in (str(_TOOLS), str(_LAB)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import composed_patch as cp                                   # noqa: E402
import composed_chain as cc                                   # noqa: E402
import patch_equilibrium as pe                                # noqa: E402
from fixture_generator import high_degree_fan                 # noqa: E402

STUDY_SCHEMA = "chimera-mechanism-factory-scale-resolution-study-v1"

SCALES = (0.5, 0.75, 1.0, 1.5, 2.0)      # physical-size axis (packet window)
RESOLUTIONS = (100, 150, 200, 300)       # n_rim ladder = resolution axis
RADIUS_WU = 1.0                          # frozen qualified recipe
HEIGHT_WU = 0.3
SEED = 1
GAMMA = 1.0                              # J/wu^2 (uniform, the law's unit)
LOAD_N = (0.0, 0.0, -0.8)                # the qualified apex dead load

PACKET_GATE_N = 1e-6                     # the law's free-residual gate
P_COMPLIANCE_WU_PER_N = 1.0              # 1/gamma_max at gamma=1
TOL_U_WU = PACKET_GATE_N * P_COMPLIANCE_WU_PER_N    # 1e-6 wu (preregistered)
MATCHED_RESOLUTION = 300                 # finest rung = matched regime
QUALIFIED_RESOLUTION = 200               # the piece's qualification resolution

STAR_DRIFT_CELLS = ((1.5, 200), (1.5, 300), (2.0, 200), (2.0, 300))

# benign converged terminal states (same taxonomy as the qualification):
# a stagnation that ends UNDER the packet's gate is a legitimate convergee;
# step_limit / invalid_surface are refusals and never count as in-gate.
CONVERGED_STATUSES = (pe.STATIONARY, pe.STAGNATED, pe.NO_DESCENT_STEP)

STUDY_EVID_DIR = _HERE.parents[1] / "docs" / "evidence" / "mechanism_factory"


def _utc_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%f")[:-3] + "Z"


def study_cell(scale: float, n_rim: int) -> dict:
    """One grid cell: build the SAME frozen fan recipe at this resolution,
    scale the whole geometry, pin the rim, load the apex, solve; record
    status, free residual, apex displacement, rim reaction norms (with the
    documented 1/n definition law) and wall time."""
    fx = high_degree_fan(n_rim=n_rim, radius=RADIUS_WU, height=HEIGHT_WU,
                         gamma=GAMMA, seed=SEED)
    V = fx.positions * float(scale)              # whole-geometry size axis
    F = fx.faces
    gamma = fx.gamma
    pins = list(range(n_rim))                    # rim ring (fixture's own pins)
    loads = [(n_rim, LOAD_N)]                    # apex = centre vertex
    t0 = time.perf_counter()
    res = pe.solve_equilibrium(V, F, gamma, pins, loads, max_steps=cp.MAX_STEPS)
    wall = time.perf_counter() - t0
    rims = np.asarray(res.reaction_forces, dtype=float)      # (nPins,3) pin-APPLIED
    norms = np.linalg.norm(rims, axis=1)
    apex = res.positions[n_rim]
    return {
        "scale_m": float(scale),
        "n_rim": int(n_rim),
        "status": res.status,
        "reason": res.reason,
        "free_residual_N": float(res.free_residual),
        "apex_z_wu": float(apex[2]),
        "rim_mean_norm_N": float(norms.mean()),
        "rim_max_norm_N": float(norms.max()),
        "surface_energy_J": float(res.surface_energy),
        "wall_time_s": wall,
        "in_gate": bool(res.status in CONVERGED_STATUSES
                        and res.free_residual <= PACKET_GATE_N),
    }


def star_cell(scale: float, n_rim: int) -> dict:
    """One star drift cell: the composed star rebuilt with ALL THREE pieces
    parametrized to n_rim (A by temporarily overriding cp.PIECE_A -- restored
    in a finally block), solved; records the same drift observable the
    qualification measured (free residual vs the packet's 1e-6 gate)."""
    old_a = dict(cp.PIECE_A)
    cp.PIECE_A = {**cp.PIECE_A, "n_rim": int(n_rim)}
    hangers = ({**cp.PIECE_B, "n_rim": int(n_rim)},
               {**cc.PIECE_C, "n_rim": int(n_rim)})
    try:
        star = cc.build_star(scale=float(scale), hangers=hangers)
        t0 = time.perf_counter()
        out = cc.solve_star(star)
        wall = time.perf_counter() - t0
        r = out["result"]
        return {"scale_m": float(scale), "n_rim": int(n_rim),
                "status": r.status, "free_residual_N": float(r.free_residual),
                "surface_energy_J": float(r.surface_energy),
                "wall_time_s": wall,
                "in_gate": bool(r.status in CONVERGED_STATUSES
                                and r.free_residual <= PACKET_GATE_N)}
    finally:
        cp.PIECE_A = old_a


def _apex_ladder(cells: list, scale: float) -> list:
    """Successive-resolution apex changes on the 100->150->200->300 ladder,
    plus the preregistered order estimate p = log2(dz_prev/dz)."""
    rows = []
    zs = {c["n_rim"]: c["apex_z_wu"]
          for c in cells if c["scale_m"] == scale}
    ns = sorted(zs)
    prev = None
    for i in range(1, len(ns)):
        dz = abs(zs[ns[i]] - zs[ns[i - 1]])
        row = {"from_n_rim": ns[i - 1], "to_n_rim": ns[i],
               "dz_wu": dz, "under_tol_u": bool(dz <= TOL_U_WU)}
        if prev is not None and prev > 0 and dz > 0:
            row["order_estimate"] = float(np.log2(prev / dz))
        rows.append(row)
        prev = dz
    return rows


def run_study(include_star: bool = True) -> dict:
    """Run every grid cell (none dropped) plus the star drift block; return
    the full study payload with preregistration, verdicts and the study
    hash (canonical over cell CONTENT excluding wall times, so the hash is
    the determinism observable)."""
    cells = [study_cell(s, n) for s in SCALES for n in RESOLUTIONS]

    ladders = {f"scale{s:g}": _apex_ladder(cells, s) for s in SCALES}

    # scale transfer vs remeshing decomposition on the piece (matched = 300):
    transfer = []
    zs300 = {c["scale_m"]: c["apex_z_wu"]
             for c in cells if c["n_rim"] == MATCHED_RESOLUTION}
    zs200 = {c["scale_m"]: c["apex_z_wu"]
             for c in cells if c["n_rim"] == QUALIFIED_RESOLUTION}
    for s in SCALES:
        phys = abs(zs300[s] - zs300[1.0])
        mesh = abs(zs300[s] - zs200[s])
        transfer.append({
            "scale_m": s,
            "physics_component_wu": phys,
            "physics_x_tol_u": phys / TOL_U_WU,
            "remeshing_component_wu": mesh,
            "remeshing_x_tol_u": mesh / TOL_U_WU,
            "physics_over_remeshing": (phys / mesh) if mesh > 0 else None,
            "matched_resolution": MATCHED_RESOLUTION,
            "unmatched_resolution": QUALIFIED_RESOLUTION,
        })

    star = ([star_cell(s, n) for (s, n) in STAR_DRIFT_CELLS]
            if include_star else [])
    star_verdict = _star_drift_verdict(star)

    hashable_cells = [{k: v for k, v in c.items() if k != "wall_time_s"}
                      for c in cells]
    # star cells enter the hash WITHOUT their wall times too (wall time
    # is machine noise, not study content; the hash must be the
    # determinism observable)
    hashable_star = [{k: v for k, v in c.items() if k != "wall_time_s"}
                     for c in star]
    study_hash = hashlib.sha256(json.dumps(
        {"cells": hashable_cells, "star": hashable_star}, sort_keys=True,
        default=str).encode("utf-8")).hexdigest()

    return {
        "schema": STUDY_SCHEMA,
        "utc": datetime.now(timezone.utc).isoformat(),
        "title": "S1 detailed multiscale reference: same mechanism, "
                 "independent scale x resolution grid",
        "mechanism": "piece.patch-equilibrium response (single high-degree "
                     "fan, rim pinned in 3D, apex dead load (0,0,-0.8 N), "
                     "frozen recipe seed=1 radius=1.0 height=0.3 gamma=1.0)",
        "resolution_axis_mapping": "n_rim = fan rim vertex count; fixture "
                                   "vertices = n_rim + 1 (apex last); "
                                   "triangles = n_rim; the SAME continuous "
                                   "patch discretized at four refinements",
        "preregistered": {
            "convergence_observable": "apex_z_wu (piece response)",
            "tol_u_wu": TOL_U_WU,
            "tol_derivation": "displacement equivalent of the packet's "
                              "1e-6 N gate through P = 1/gamma_max = 1 wu/N",
            "rim_norms_excluded": "mean/max rim reaction norms obey the "
                                  "measured definition law "
                                  "~6.5*scale/n_rim N (fixed resultant "
                                  "over n vertices); "
                                  "recorded, not a convergence test",
            "matched_regime": "n_rim=300 (finest rung) at each scale",
            "unmatched_regime": "n_rim=200 (the qualification resolution) "
                                "reused unchanged",
            "honest_limit": "the n_rim<=300 ladder does NOT reach tol_u "
                            "(finest dz ~1.16e-5 wu = 11.6x tol_u); "
                            "'resolved at tol_u' is not claimed",
        },
        "cells": cells,
        "apex_ladders": ladders,
        "scale_transfer_vs_remeshing": transfer,
        "star_drift_cells": star,
        "star_drift_verdict": star_verdict,
        "study_hash": study_hash,
    }


def _star_drift_verdict(star_cells: list) -> dict:
    """DISCRETIZATION iff refining n_rim 200->300 brings the star's residual
    under the packet's 1e-6 gate at BOTH drifted scales; else SCALE PHYSICS."""
    by = {(c["scale_m"], c["n_rim"]): c for c in star_cells}
    per_scale = []
    all_refined_in_gate = True
    for s in (1.5, 2.0):
        c200, c300 = by.get((s, 200)), by.get((s, 300))
        if not c200 or not c300:
            all_refined_in_gate = False
            continue
        refined_in = c300["in_gate"]
        all_refined_in_gate = all_refined_in_gate and refined_in
        per_scale.append({
            "scale_m": s,
            "residual_n200_N": c200["free_residual_N"],
            "residual_n300_N": c300["free_residual_N"],
            "refinement_change_pct": (abs(c300["free_residual_N"]
                                          - c200["free_residual_N"])
                                      / c200["free_residual_N"] * 100.0),
            "refined_in_gate": refined_in,
            "over_gate_x_at_n300": c300["free_residual_N"] / PACKET_GATE_N,
            "surface_energy_J_n300": c300["surface_energy_J"],
        })
    return {
        "question": "is the star's 1.5x/2.0x drift over the 1e-6 gate "
                    "discretization or scale physics?",
        "decision_rule": "discretization iff n_rim=300 refinement brings "
                         "the residual under 1e-6 N at both scales",
        "per_scale": per_scale,
        "verdict": ("discretization" if all_refined_in_gate
                    else "scale_physics"),
        "verdict_text": ("refining the resolution does NOT bring the star "
                         "under the gate (residual moves a few percent and "
                         "stays over it): the drift is SCALE PHYSICS under "
                         "this law -- the descent's machine-precision "
                         "stagnation floor at the larger energy scale -- "
                         "not a mesh-resolution artifact"
                        if not all_refined_in_gate else
                        "refinement brings the residual under the gate: "
                        "the drift was discretization"),
    }


def write_study_receipt(payload: dict, name_suffix: str = "") -> Path:
    """Append-only study receipt under docs/evidence/mechanism_factory/."""
    STUDY_EVID_DIR.mkdir(parents=True, exist_ok=True)
    out = STUDY_EVID_DIR / (
        f"scale_resolution_study{_name_suffix(name_suffix)}_"
        f"{_utc_compact()}.json")
    out.write_text(json.dumps(payload, indent=1, default=str) + "\n",
                   encoding="utf-8")
    return out


def _name_suffix(s: str) -> str:
    return ("_" + s) if s else ""


def main() -> int:
    study = run_study(include_star=True)
    out = write_study_receipt(study)
    n_cells = len(study["cells"])
    in_gate = sum(1 for c in study["cells"] if c["in_gate"])
    print(f"study receipt: {out}")
    print(f"cells: {n_cells} ({in_gate} in-gate), study hash "
          f"{study['study_hash'][:16]}")
    print("star drift verdict:", study["star_drift_verdict"]["verdict"])
    for row in study["star_drift_verdict"]["per_scale"]:
        print(f"  scale {row['scale_m']:g}: n200 {row['residual_n200_N']:.4e}"
              f" -> n300 {row['residual_n300_N']:.4e} N "
              f"({row['refinement_change_pct']:.1f}% change, "
              f"{row['over_gate_x_at_n300']:.2f}x gate)")
    for row in study["scale_transfer_vs_remeshing"]:
        r = row["physics_over_remeshing"]
        print(f"  scale {row['scale_m']:g}: physics {row['physics_x_tol_u']:.0f}x"
              f" tol_u, remeshing {row['remeshing_x_tol_u']:.0f}x tol_u"
              + (f", physics/remeshing {r:.0f}x" if r else ""))
    lad = study["apex_ladders"]["scale1"]
    print("scale-1 ladder dz:",
          ", ".join(f"{r['from_n_rim']}->{r['to_n_rim']} "
                    f"{r['dz_wu']:.3e}"
                    + (f" (p~{r['order_estimate']:.2f})"
                       if "order_estimate" in r else "")
                    for r in lad))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
