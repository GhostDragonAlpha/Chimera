"""gpu_fixtures_generate.py — GLM-FREEZE: frozen GPU-comparison fixtures.

REGISTRATION (GLM-FREEZE, 2026-09-07; authorized by ASTRA; Big Pickle
unavailable). This generator runs ONCE against the published source at
astra/gait-capture commit cf2a0ae2c7bd68f1c64db630c4db5de32785580a (BP-A1)
and freezes its inputs/outputs as reproducible artifacts. It writes only
under docs/evidence/gpu_fixtures/ and tools/gpu_fixtures_recovered/, and
refuses to overwrite existing evidence.

STATEMENT  The published CPU reference `tools/surface_energy_reference.py`
           evaluated on exact binary32-uploaded geometry, with fixed-order
           CSR corner adjacency, is a reproducible numerical reference for
           the GPU surface-energy transcription, and the binary32 assembly
           rounding of corner forces into vertex forces is bounded per
           vertex by eta_(d-1) * sum_incident |corner force component| with
           u = 2^-24 and eta_n = n*u/(1-n*u).

PREDICTION (frozen here, tested by gpu_fixtures_verify.py, never retuned)
  R1  Reloading the frozen binary32 inputs and re-running the published
      reference reproduces every frozen float64 output BITWISE (same code,
      same inputs, same numpy).
  R2  gamma = 0 gives numerically zero energy and forces (signed zero ok).
  R3  gamma = 2 at identical geometry gives EXACTLY 2x the gamma = 1 energy
      and every force component (power-of-two exactness), and identical
      areas/normals bitwise.
  R4  Independent scatter assembly (np.add.at, face order) of the frozen
      float64 corner forces agrees with the frozen CSR-gathered vertex
      forces within d_v * eps64 * sum_incident |corner component| per
      vertex/component (sequential-summation bound; order difference only).
  R5  Centre force matches the ideal-geometry closed form within the
      preregistered binary32-quantization allowances below; centre force is
      vertical within the symmetry allowance; total area matches within the
      area allowance.
  R6  A corrupted corner-order control (corner slots permuted post hoc)
      FAILS verification.

PREREGISTERED ALLOWANCES (derived from binary32 coordinate quantization,
fixed by this file BEFORE any verification run; the verifier only reads
them from the manifests):
  u      = 2^-24; |V_up - V_ideal| <= u per coordinate for |coord| <= 1
           (conservative: true rounding error <= u/2 here). The centre
           (0, 0, 0.125) is EXACT in binary32; only rim vertices deviate.
  AREA   |dA/dp| = 0.5 * |opposite edge| exactly, so with |delta_p| <=
           sqrt(3)*u per moved corner and 3 corners per face:
           allow_A = sum_f 3 * 0.5 * maxedge_f * sqrt(3) * u  [J at gamma=1;
           scales exactly with gamma].
  FORCE_Z  B2: 1.0e-6 N [PROVISIONAL — preserved from the recovered
           membrane_fixture_b2.py C2 allowance; observed deviation ~1e-7].
           fan12: 2.0e-6 N [PROVISIONAL — scaled from B2's adopted
           provisional by face count 12/6; observed deviation expected
           ~2e-7]. These are fixture-specific, not error theorems.
  FORCE_XY (symmetry) 1.0e-6 N for both fixtures: the dihedral symmetry of
           the construction forces |F_c,x|, |F_c,y| -> 0; residual comes
           from sin(pi) = 1.22e-16-type rounding, orders of magnitude below.

ASSEMBLY BUDGET LAW (GLM-FREEZE; per vertex v, per force component j):
  B_vj = eta_(d_v - 1) * sum_incident |corner_force_component_j|,
  where corner forces are FIRST rounded to the GPU input dtype (binary32)
  and summed in binary64. d_v = incident corner count. eta_n = n*u/(1-n*u).
  These bound GPU binary32 sequential assembly ONLY (the assembly-isolation
  deliverable). The adopted B2 face-arithmetic budgets (corner 4.0e-6 N,
  complete force 2.5e-5 N, energy 1.1e-5 J, assembly-only 1.0e-6 N — the
  latter a fixture-level budget, NOT the per-vertex law) are RECORDED
  alongside and remain the gates for face evaluation; nothing here
  verifies face arithmetic. Degree-six bounds are NOT reused for the
  twelve-triangle fan: every budget is derived from the actual degree.

FIXTURES (force-evaluation fixtures — NOT optimizer or dynamics tests):
  b2    seven vertices, six triangles: rim r_k = (cos k*pi/3, sin k*pi/3, 0)
        (the recovered B2 angle formula, byte-matched to the recovered
        fixture), centre c = (0,0,0.125) m; faces (c, r_k, r_{k+1}) CCW;
        gamma in {0, 1, 2} J/m^2 at identical geometry. Vertex order:
        rim 0..5, centre 6.
  fan12 thirteen vertices, twelve triangles: rim r_k = (cos 2k*pi/12,
        sin 2k*pi/12, 0), centre (0,0,0.125) m, faces (c, r_k, r_{k+1})
        CCW; gamma in {0, 1, 2} J/m^2. Vertex order: rim 0..11, centre 12.
        This is a NEW fixture; the recovered 25-vertex/36-face disk demo
        (tools/gpu_fixtures_recovered/membrane_demo.py) remains its own
        fixture and is NOT relabeled here.

UPLOAD LAW  positions/gamma frozen ONCE as little-endian binary32; face
indices as uint32. The CPU reference evaluates those exact stored values
promoted to binary64. Input quantization and arithmetic error are kept
distinct: the frozen float64 outputs are the matched-input reference; the
asmref arrays are the exact binary64 sum of the binary32-ROUNDED corner
forces (the assembly-isolation reference a GPU gather compares against).

Artifacts per fixture directory (all .npy written with allow_pickle=False):
  geometry/positions_f32.npy (nV,3) <f4      the ONE binary32 upload
  geometry/indices_u32.npy   (nF,3) <u4      face indices
  geometry/gamma{0,1,2}_f32.npy (nF,) <f4    per-face gamma
  adjacency/csr_offsets_i64.npy (nV+1,) int64   fixed-order CSR (reference)
  adjacency/csr_corner_idx_i64.npy (3nF,) int64 corner rows, vertex-major
  adjacency/incident_counts_i64.npy (nV,) int64 per-vertex incident count
  case_gamma{0,1,2}/areas_f64.npy (nF,) <f8
  case_gamma{0,1,2}/normals_f64.npy (nF,3) <f8
  case_gamma{0,1,2}/corner_forces_f64.npy (nF,3,3) <f8  face-major corners
  case_gamma{0,1,2}/vertex_forces_f64.npy (nV,3) <f8    CSR-gathered (f64 corners)
  case_gamma{0,1,2}/vertex_forces_asmref_f64.npy (nV,3) <f8  f64 sum of f32 corners
  case_gamma{0,1,2}/assembly_budgets_f64.npy (nV,3) <f8  B_vj per component
  case_gamma{0,1,2}/energy_f64.npy scalar <f8
  manifest.json   shapes, dtypes, units, source commit, source hashes,
                  analytic ideal values, preregistered allowances, budget
                  law, adopted B2 budgets (recorded), artifact sha256s.

UNITS  positions [m] (1 wu = 1 m for these fixtures), gamma [J/m^2],
areas [m^2], forces [N], energy [J]. No gravity, inertia, contact,
optimizer or time claim exists in these fixtures. Verification class:
CPU numerical only; the engine window is not exercised.

Recovered-fixture provenance: tools/gpu_fixtures_recovered/ holds verbatim
copies of the pre-crash files with their original SHA-256 recorded in
RECOVERED_HASHES.json; the frozen B2 upload is asserted equal to the
recovered B2's b2_mesh() upload before anything is written.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

_TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(_TOOLS))

from surface_energy_reference import (          # noqa: E402  (published source)
    evaluate_surface, build_vertex_corner_adjacency)

SOURCE_COMMIT = "cf2a0ae2c7bd68f1c64db630c4db5de32785580a"
SOURCE_BRANCH = "astra/gait-capture"
U_F32 = 2.0 ** -24

# Adopted B2 GPU budgets — RECORDED, preserved, NOT applied here.
ADOPTED_B2_BUDGETS = {
    "corner_component_N": 4.0e-6,
    "assembly_only_component_N": 1.0e-6,
    "complete_force_component_N": 2.5e-5,
    "energy_J": 1.1e-5,
    "note": "adopted at ASTRA-B2 (M1); gate GPU face arithmetic and "
            "fixture-level assembly; NOT derived from and NOT replaced by "
            "the per-vertex eta law frozen in these fixtures",
}
# Preregistered force allowances [N] (see module docstring derivation):
FORCE_Z_ALLOW = {"b2": 1.0e-6, "fan12": 2.0e-6}     # PROVISIONAL, fixed now
FORCE_XY_SYM_ALLOW = 1.0e-6                          # both fixtures

FIXTURES = {
    "b2": {"n_rim": 6, "angle_formula": "np.pi/3 * arange(6)  (recovered B2 formula)"},
    "fan12": {"n_rim": 12, "angle_formula": "2*pi/12 * arange(12)  (new fixture)"},
}
CASES = ("gamma0", "gamma1", "gamma2")
CASE_GAMMA = {"gamma0": 0.0, "gamma1": 1.0, "gamma2": 2.0}


def eta(n: float) -> float:
    """eta_n = n*u/(1-n*u), u = 2^-24 (binary32 unit roundoff)."""
    return n * U_F32 / (1.0 - n * U_F32)


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def mesh(n_rim: int, b2_formula: bool):
    """Ideal float64 mesh: rim 0..n-1, centre n at (0,0,0.125); faces
    (centre, r_k, r_{k+1}) CCW (+z normals). Returns (V_ideal, F)."""
    if b2_formula:                       # byte-match the recovered B2 fixture
        ang = np.pi / 3.0 * np.arange(n_rim)
    else:
        ang = 2.0 * np.pi * np.arange(n_rim) / n_rim
    rim = np.stack([np.cos(ang), np.sin(ang), np.zeros(n_rim)], axis=1)
    centre = np.array([[0.0, 0.0, 0.125]])
    V = np.vstack([rim, centre])
    F = np.array([[n_rim, k, (k + 1) % n_rim] for k in range(n_rim)],
                 dtype=np.int64)
    return V, F


def analytic(n_rim: int) -> dict:
    """Ideal-geometry closed forms. A(h) = n*sin(pi/n)*sqrt(cos^2(pi/n)+h^2);
    dA/dh = n*sin(pi/n)*h/sqrt(cos^2(pi/n)+h^2); F_cz = -gamma * dA/dh.
    (For n=6: A = 3*sqrt(3/4+h^2), F_cz = -3*gamma*h/sqrt(3/4+h^2).)"""
    h = 0.125
    s, c = math.sin(math.pi / n_rim), math.cos(math.pi / n_rim)
    root = math.sqrt(c * c + h * h)
    return {"h_m": h, "A_m2": n_rim * s * root,
            "dA_dh_m": n_rim * s * h / root,
            "F_cz_at_gamma1_N": -n_rim * s * h / root,
            "A_flat_m2": n_rim * s * c,
            "reduction_J_at_gamma1": n_rim * s * (root - c)}


def save(out_dir: Path, rel: str, arr: np.ndarray) -> dict:
    p = out_dir / rel
    if p.exists():
        raise SystemExit(f"evidence_path_exists: {p}")
    p.parent.mkdir(parents=True, exist_ok=True)
    np.save(p, arr, allow_pickle=False)
    return {"path": rel, "sha256": sha256_file(p), "shape": list(arr.shape),
            "dtype": str(arr.dtype)}


def build_fixture(name: str, spec: dict, src_hashes: dict) -> dict:
    n_rim = spec["n_rim"]
    V_ideal, F = mesh(n_rim, b2_formula=(name == "b2"))
    nV, nF = V_ideal.shape[0], F.shape[0]

    # ---- the ONE binary32 upload; evaluation uses its exact promotion ----
    pos32 = V_ideal.astype("<f4")
    V_up = pos32.astype(np.float64)
    idx32 = F.astype("<u4")
    F_up = idx32.astype(np.int64)

    if name == "b2":
        # provenance: the frozen upload must equal the RECOVERED fixture's
        # b2_mesh() upload exactly (byte-identity to the pre-crash fixture).
        rec_path = _TOOLS / "gpu_fixtures_recovered" / "membrane_fixture_b2.py"
        spc = importlib.util.spec_from_file_location("rec_b2", rec_path)
        rec = importlib.util.module_from_spec(spc)
        spc.loader.exec_module(rec)
        _, recV_up, recF = rec.b2_mesh()
        assert np.array_equal(V_up, recV_up) and np.array_equal(F_up, recF), \
            "frozen B2 upload differs from the recovered B2 fixture"

    maxedge = np.maximum(np.maximum(
        np.linalg.norm(V_up[F_up[:, 1]] - V_up[F_up[:, 0]], axis=1),
        np.linalg.norm(V_up[F_up[:, 2]] - V_up[F_up[:, 1]], axis=1)),
        np.linalg.norm(V_up[F_up[:, 0]] - V_up[F_up[:, 2]], axis=1))
    # area allowance at gamma=1 (see docstring derivation); exact x2 at gamma=2
    area_allow_1 = float(np.sum(3.0 * 0.5 * maxedge) * math.sqrt(3.0) * U_F32)

    offsets, corner_idx = build_vertex_corner_adjacency(F_up, nV)
    counts = np.diff(offsets).astype(np.int64)          # incident corners = degree
    eta_d = np.array([eta(float(d) - 1.0) for d in counts], dtype=np.float64)

    out = {"name": name, "n_rim": n_rim, "n_vertices": nV, "n_faces": nF,
           "files": [], "cases": {}}

    out["files"].append(save(_EV / name, "geometry/positions_f32.npy", pos32))
    out["files"].append(save(_EV / name, "geometry/indices_u32.npy", idx32))
    for cname in CASES:
        out["files"].append(save(
            _EV / name, f"geometry/{cname}_f32.npy",
            np.full(nF, CASE_GAMMA[cname], dtype="<f4")))
    out["files"].append(save(_EV / name, "adjacency/csr_offsets_i64.npy", offsets))
    out["files"].append(save(_EV / name, "adjacency/csr_corner_idx_i64.npy", corner_idx))
    out["files"].append(save(_EV / name, "adjacency/incident_counts_i64.npy", counts))

    dev = np.abs(V_up - V_ideal)
    coord_dev = float(dev.max())

    for cname in CASES:
        g = CASE_GAMMA[cname]
        gam_up = np.full(nF, g, dtype="<f4").astype(np.float64)
        ev = evaluate_surface(V_up, F_up, gam_up)       # published reference

        # assembly-isolation reference: binary32-round the corner forces
        # FIRST, then the exact binary64 CSR-order sum.
        c32 = ev.face_corner_forces.astype("<f4")
        c32_up = c32.astype(np.float64).reshape(-1, 3)
        asmref = np.zeros_like(V_up)
        np.add.reduceat(c32_up[corner_idx], offsets[:-1], axis=0, out=asmref)

        # per-vertex/component budget law on the binary32 corner forces
        abs_corner = np.abs(c32_up)
        sum_abs = np.add.reduceat(abs_corner[corner_idx], offsets[:-1], axis=0)
        budgets = eta_d[:, None] * sum_abs              # (nV,3) B_vj

        cdir = f"case_{cname}"
        out["files"] += [
            save(_EV / name, f"{cdir}/areas_f64.npy", ev.areas.astype("<f8")),
            save(_EV / name, f"{cdir}/normals_f64.npy", ev.normals.astype("<f8")),
            save(_EV / name, f"{cdir}/corner_forces_f64.npy",
                 ev.face_corner_forces.astype("<f8")),
            save(_EV / name, f"{cdir}/vertex_forces_f64.npy",
                 ev.vertex_forces.astype("<f8")),
            save(_EV / name, f"{cdir}/vertex_forces_asmref_f64.npy",
                 asmref.astype("<f8")),
            save(_EV / name, f"{cdir}/assembly_budgets_f64.npy",
                 budgets.astype("<f8")),
            save(_EV / name, f"{cdir}/energy_f64.npy",
                 np.array(ev.energy, dtype="<f8")),
        ]
        out["cases"][cname] = {
            "gamma_J_per_m2": g,
            "energy_J": ev.energy,
            "centre_vertex_index": n_rim,
            "centre_force_N": ev.vertex_forces[n_rim].tolist(),
            "centre_asmref_N": asmref[n_rim].tolist(),
            "total_area_m2": float(np.sum(ev.areas)),
            "budget_centre_N": budgets[n_rim].tolist(),
            "budget_max_rim_N": [float(budgets[:n_rim, j].max())
                                 for j in range(3)],
            "budget_law": "B_vj = eta_(d_v-1) * sum_incident |f32 corner comp|",
            "degree_centre": int(counts[n_rim]),
            "degree_rim": int(counts[0]),
            "eta_centre": eta(float(counts[n_rim]) - 1.0),
            "eta_rim": eta(float(counts[0]) - 1.0),
        }

    an = analytic(n_rim)
    out["analytic_ideal"] = an
    out["preregistered_allowances"] = {
        "u_binary32": U_F32,
        "max_abs_coord_deviation_uploaded_vs_ideal": coord_dev,
        "coord_bound_used": "sqrt(3)*u per corner (conservative)",
        "area_J_at_gamma1": area_allow_1,
        "area_allowance_note": "gamma-independent: areas do not scale with "
                               "gamma; the x2 energy scaling is exact and "
                               "needs no widened allowance",
        "energy_J_at_gamma1_bound": area_allow_1,
        "force_z_N": FORCE_Z_ALLOW[name],
        "force_z_provenance": ("preserved PROVISIONAL from recovered B2 C2 "
                               "allowance" if name == "b2" else
                               "PROVISIONAL, scaled from B2 by face count 12/6"),
        "force_xy_symmetry_N": FORCE_XY_SYM_ALLOW,
    }
    out["adopted_b2_budgets_recorded"] = ADOPTED_B2_BUDGETS
    out["angle_formula"] = spec["angle_formula"]

    manifest = {
        "what": f"GLM-FREEZE frozen GPU-comparison fixture: {name}",
        "registration": "GLM-FREEZE 2026-09-07 (ASTRA-authorized continuation)",
        "fixture_class": "force-evaluation fixture; NOT optimizer/dynamics",
        "verification_class": "CPU numerical only; no engine-window/DYAD claim",
        "source": {"repo": "https://github.com/GhostDragonAlpha/Chimera",
                   "branch": SOURCE_BRANCH, "commit": SOURCE_COMMIT,
                   "source_file_hashes": src_hashes},
        "python": platform.python_version(), "numpy": np.__version__,
        "upload_law": "positions/gamma binary32 little-endian, uploaded ONCE; "
                      "reference evaluates their exact binary64 promotion; "
                      "face indices uint32",
        "units": {"positions": "m (1 wu = 1 m here)", "gamma": "J/m^2",
                  "areas": "m^2", "forces": "N", "energy": "J"},
        "adjacency": {"order": "vertex asc, face asc, corner slot asc "
                               "(build_vertex_corner_adjacency, fixed order)",
                      "offsets_dtype": "int64", "corner_idx_dtype": "int64",
                      "corner_layout": "face-major flat 3*f+k"},
        "budget_law": "B_vj = eta_(d_v-1) * sum_incident |binary32 corner "
                      "force component|; eta_n = n*u/(1-n*u), u=2^-24; "
                      "bounds GPU binary32 sequential ASSEMBLY only — face "
                      "arithmetic is gated by the recorded adopted B2 "
                      "budgets, not verified here",
        "scope_note": "the recovered 25-vertex/36-face disk demo remains its "
                      "own fixture; it is not relabeled as a fan",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        **out,
    }
    mp = _EV / name / "manifest.json"
    if mp.exists():
        raise SystemExit(f"evidence_path_exists: {mp}")
    mp.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


_EV = _TOOLS.parent / "docs" / "evidence" / "gpu_fixtures"


def main() -> int:
    if _EV.exists():
        raise SystemExit(f"evidence_path_exists: {_EV} — GLM-FREEZE writes once")
    src_files = ["tools/surface_energy_reference.py", "tools/material_contract.py",
                 "tools/overdamped_descent.py", "tools/gpu_fixtures_generate.py"]
    src_hashes = {f: sha256_file(_TOOLS.parent / f) for f in src_files}
    src_hashes["tools/gpu_fixtures_recovered/membrane_fixture_b2.py"] = \
        sha256_file(_TOOLS / "gpu_fixtures_recovered" / "membrane_fixture_b2.py")
    src_hashes["tools/gpu_fixtures_recovered/membrane_demo.py"] = \
        sha256_file(_TOOLS / "gpu_fixtures_recovered" / "membrane_demo.py")

    manifests = {n: build_fixture(n, s, src_hashes) for n, s in FIXTURES.items()}

    for n, m in manifests.items():
        cz, c1 = m["cases"]["gamma0"], m["cases"]["gamma1"]
        c2 = m["cases"]["gamma2"]
        print(f"[{n}] nV={m['n_vertices']} nF={m['n_faces']} "
              f"deg_centre={cz['degree_centre']} deg_rim={cz['degree_rim']}")
        print(f"  A(gamma1)={c1['total_area_m2']:.12g} m^2  "
              f"analytic={m['analytic_ideal']['A_m2']:.12g}")
        print(f"  F_c(gamma1)=({c1['centre_force_N'][0]:+.3e}, "
              f"{c1['centre_force_N'][1]:+.3e}, {c1['centre_force_N'][2]:.12g}) N "
              f"analytic {m['analytic_ideal']['F_cz_at_gamma1_N']:.12g}")
        print(f"  budget centre (deg {cz['degree_centre']}, "
              f"eta={cz['eta_centre']:.6e}): "
              f"{['%.3e' % b for b in cz['budget_centre_N']]} N")
        print(f"  budget max rim (deg {cz['degree_rim']}, "
              f"eta={cz['eta_rim']:.6e}): "
              f"{['%.3e' % b for b in cz['budget_max_rim_N']]} N")
        print(f"  gamma0 energy={cz['energy_J']!r}  "
              f"gamma2/gamma1 energy={c2['energy_J'] / c1['energy_J']!r}")
    print(f"artifacts + manifests: {_EV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
