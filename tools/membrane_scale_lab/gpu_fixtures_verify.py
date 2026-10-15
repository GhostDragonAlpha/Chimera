"""gpu_fixtures_verify.py — GLM-FREEZE verifier for the frozen fixtures.

Run:  python tools/gpu_fixtures_verify.py            (verify all fixtures)
      python tools/gpu_fixtures_verify.py --corrupt  (corner-order control)

PREREGISTRATION (written before the first verification run; no tolerance in
this file is chosen after seeing results):
  STATEMENT  The frozen GLM-FREEZE fixtures under docs/evidence/gpu_fixtures/
             are internally consistent, reproducible from their binary32
             inputs through the published reference, and detect any corner-
             order corruption.
  PREDICTIONS R1..R6 of gpu_fixtures_generate.py (bitwise reload, zero-gamma,
             exact gamma-doubling, eps64 scatter/gather bound, analytic
             quantization allowances, corrupt control fails).
  FALSIFIERS any hash/shape/dtype mismatch; any non-bitwise reload; scatter
             beyond the preregistered d_v*eps64*sum|corner| bound; gamma=0
             nonzero; gamma=2 not bitwise 2x; analytic deviation beyond the
             generator's preregistered allowances; the corrupted control
             passing. A FAIL is never repaired here and no tolerance is
             widened: a failing check is reported and the exit code is 1.

ALLOWANCES are read from each fixture's manifest (frozen by the generator
BEFORE any verification). The only bounds derived inside this file are the
preregistered formulas themselves:
  scatter/gather (order difference only, binary64):  per vertex/component,
    |scatter - gather| <= d_v * eps64 * sum_incident |corner component|
    (sequential summation worst case; np.add.at is sequential).
  f32 corner rounding (asmref vs vertex_forces): binary32 rounding gives
    f32(x) = x(1+delta), |delta| <= u (the unit roundoff, u = 2^-24), hence
    per component |asmref - vertex_forces| <= u * sum_incident |binary64
    corner comp|.  [CORRECTION 2026-09-07, first verify run 21:12Z: the
    preregistered bound used 0.5*u -- a factor-2 model error, the unit
    roundoff IS u = eps/2; the failed run is preserved as
    verify_results_20260907T211214.440162Z.json, worst observed ratio 1.239
    against the erroneous bound = 0.62 against the corrected one.]
Both formulas use the STORED corner forces; nothing is empirical.

The --corrupt control swaps corner slots 0<->1 of face 0 in a TEMP COPY of
the b2 gamma1 case, UPDATES the copied manifest hash for that file (so the
failure cannot be the hash check), and requires the full verification of
the copy to FAIL. If the corrupted copy verifies, the control has failed
and this script exits nonzero with verdict CONTROL_FAILED.

Verification class: CPU numerical only. Iterations/time: not applicable.
"""
from __future__ import annotations

import hashlib
import json
import math
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

_TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(_TOOLS))

from surface_energy_reference import evaluate_surface   # noqa: E402

_EV = _TOOLS.parent / "docs" / "evidence" / "gpu_fixtures"
U_F32 = 2.0 ** -24
EPS64 = float(np.finfo(np.float64).eps)


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load(fx: Path, rel: str) -> np.ndarray:
    return np.load(fx / rel, allow_pickle=False)


def verify_fixture(name: str) -> dict:
    fx = _EV / name
    man = json.loads((fx / "manifest.json").read_text(encoding="utf-8"))
    res: dict = {"fixture": name, "checks": {}, "details": {}}
    checks = res["checks"]

    def ck(key: str, ok: bool, detail=None):
        checks[key] = bool(ok)
        if detail is not None:
            res["details"][key] = detail

    # ---- V1 hashes / shapes / dtypes / environment -------------------------
    n_v1_bad = 0
    for ent in man["files"]:
        p = fx / ent["path"]
        if not p.exists() or sha256_file(p) != ent["sha256"]:
            n_v1_bad += 1
            continue
        a = np.load(p, allow_pickle=False)
        if list(a.shape) != ent["shape"] or str(a.dtype) != ent["dtype"]:
            n_v1_bad += 1
    ck("V1_artifact_hashes_shapes_dtypes", n_v1_bad == 0,
       {"files_checked": len(man["files"]), "mismatches": n_v1_bad})
    ck("V1b_numpy_version_matches_generation",
       man["numpy"] == np.__version__,
       {"generated_with": man["numpy"], "verifying_with": np.__version__})

    pos32 = load(fx, "geometry/positions_f32.npy")
    idx32 = load(fx, "geometry/indices_u32.npy")
    V_up = pos32.astype(np.float64)
    F_up = idx32.astype(np.int64)
    nV, nF = V_up.shape[0], F_up.shape[0]

    # ---- V2 CSR coverage and fixed order -----------------------------------
    offsets = load(fx, "adjacency/csr_offsets_i64.npy")
    corner_idx = load(fx, "adjacency/csr_corner_idx_i64.npy")
    counts = load(fx, "adjacency/incident_counts_i64.npy")
    seg_ok = True
    for v in range(nV):
        seg = corner_idx[offsets[v]:offsets[v + 1]]
        if seg.size > 1 and not np.all(np.diff(seg) > 0):
            seg_ok = False
    ck("V2_csr_coverage_and_order",
       bool(offsets[0] == 0 and offsets[-1] == 3 * nF
            and np.all(np.diff(offsets) > 0)
            and np.array_equal(np.diff(offsets), counts)
            and int(counts.sum()) == 3 * nF
            and np.array_equal(np.sort(corner_idx), np.arange(3 * nF))
            and seg_ok),
       {"nV": nV, "nF": nF, "segments_ascending": seg_ok})

    # analytic closed form recomputed HERE (independent of the manifest)
    n_rim = man["n_rim"]
    h = 0.125
    s, c = math.sin(math.pi / n_rim), math.cos(math.pi / n_rim)
    root = math.sqrt(c * c + h * h)
    A_an = n_rim * s * root
    Fcz_an = -n_rim * s * h / root
    man_an = man["analytic_ideal"]
    ck("V2b_manifest_analytic_bitwise_reproducible",
       bool(man_an["A_m2"] == A_an and man_an["F_cz_at_gamma1_N"] == Fcz_an),
       {"A_manifest": man_an["A_m2"], "A_recomputed": A_an,
        "F_manifest": man_an["F_cz_at_gamma1_N"], "F_recomputed": Fcz_an})

    allow = man["preregistered_allowances"]
    cases = {}
    for cname in ("gamma0", "gamma1", "gamma2"):
        d = f"case_{cname}"
        cases[cname] = {
            "gam_up": load(fx, f"geometry/{cname}_f32.npy").astype(np.float64),
            "areas": load(fx, f"{d}/areas_f64.npy"),
            "normals": load(fx, f"{d}/normals_f64.npy"),
            "corner": load(fx, f"{d}/corner_forces_f64.npy"),
            "vforce": load(fx, f"{d}/vertex_forces_f64.npy"),
            "asmref": load(fx, f"{d}/vertex_forces_asmref_f64.npy"),
            "budget": load(fx, f"{d}/assembly_budgets_f64.npy"),
            "energy": float(load(fx, f"{d}/energy_f64.npy")),
        }

    # ---- V3 bitwise reload reproducibility ----------------------------------
    v3 = {}
    for cname, cd in cases.items():
        ev = evaluate_surface(V_up, F_up, cd["gam_up"])
        v3[cname] = bool(
            np.array_equal(ev.areas, cd["areas"])
            and np.array_equal(ev.normals, cd["normals"])
            and np.array_equal(ev.face_corner_forces, cd["corner"])
            and np.array_equal(ev.vertex_forces, cd["vforce"])
            and float(ev.energy) == cd["energy"])
    ck("V3_bitwise_reload_reproducibility", all(v3.values()), v3)

    # ---- V4 independent scatter vs stored gather (eps64 bound) --------------
    v4, v4max = True, {}
    for cname, cd in cases.items():
        scatter = np.zeros_like(V_up)
        np.add.at(scatter, F_up.reshape(-1), cd["corner"].reshape(-1, 3))
        sum_abs = np.add.reduceat(
            np.abs(cd["corner"].reshape(-1, 3))[corner_idx],
            offsets[:-1], axis=0)
        bound = counts[:, None] * EPS64 * sum_abs
        diff = np.abs(scatter - cd["vforce"])
        v4max[cname] = float(np.max(diff - bound))
        if not np.all(diff <= bound):
            v4 = False
        # same independent bound for the f32-asmref arrays
        scatter32 = np.zeros_like(V_up)
        np.add.at(scatter32, F_up.reshape(-1),
                  cd["corner"].astype("<f4").astype(np.float64).reshape(-1, 3))
        if not np.all(np.abs(scatter32 - cd["asmref"])
                      <= counts[:, None] * EPS64
                      * np.add.reduceat(
                          np.abs(cd["corner"].astype("<f4").astype(np.float64)
                                 .reshape(-1, 3))[corner_idx],
                          offsets[:-1], axis=0)):
            v4 = False
    ck("V4_independent_scatter_within_eps64_bound", v4,
       {"max_excess_over_bound": v4max})

    # ---- V5 asmref bitwise recompute + f32-rounding bound -------------------
    v5 = {}
    for cname, cd in cases.items():
        c32_up = cd["corner"].astype("<f4").astype(np.float64).reshape(-1, 3)
        asm = np.zeros_like(V_up)
        np.add.reduceat(c32_up[corner_idx], offsets[:-1], axis=0, out=asm)
        sum_abs = np.add.reduceat(np.abs(cd["corner"].reshape(-1, 3))[corner_idx],
                                  offsets[:-1], axis=0)
        v5[cname] = bool(np.array_equal(asm, cd["asmref"])
                         and np.all(np.abs(cd["asmref"] - cd["vforce"])
                                    <= U_F32 * sum_abs))
    ck("V5_asmref_bitwise_and_f32_rounding_bound", all(v5.values()), v5)

    # ---- V6 zero-gamma control ----------------------------------------------
    c0 = cases["gamma0"]
    ck("V6_zero_gamma_numerically_zero",
       bool(c0["energy"] == 0.0 and not c0["vforce"].any()
            and not c0["corner"].any()),
       {"energy": c0["energy"],
        "max_abs_force": float(np.abs(c0["vforce"]).max())})

    # ---- V7 gamma-doubling exactness (bitwise 2x) ---------------------------
    c1, c2 = cases["gamma1"], cases["gamma2"]
    ck("V7_gamma2_bitwise_double_of_gamma1",
       bool(np.array_equal(c2["areas"], c1["areas"])
            and np.array_equal(c2["normals"], c1["normals"])
            and np.array_equal(c2["corner"], 2.0 * c1["corner"])
            and np.array_equal(c2["vforce"], 2.0 * c1["vforce"])
            and np.array_equal(c2["asmref"], 2.0 * c1["asmref"])
            and np.array_equal(c2["budget"], 2.0 * c1["budget"])
            and c2["energy"] == 2.0 * c1["energy"]),
       {"energy1": c1["energy"], "energy2": c2["energy"],
        "ratio": c2["energy"] / c1["energy"]})

    # ---- V8 analytic vs uploaded-geometry, preregistered allowances ---------
    v8 = {}
    ci = n_rim                                    # centre vertex index
    for cname, cd in cases.items():
        g = cd["gam_up"][0]
        fc = cd["vforce"][ci]
        dev = float(np.max(np.abs(
            fc - np.array([0.0, 0.0, Fcz_an * float(g)]))))
        # force deviation scales exactly with gamma (power-of-two cases),
        # so the allowance scales with gamma too; the AREA allowance does
        # NOT scale with gamma -- areas are gamma-independent geometry.
        f_allow = allow["force_z_N"] * (2.0 if cname == "gamma2" else 1.0)
        a_dev = float(abs(np.sum(cd["areas"]) - A_an))
        a_allow = allow["area_J_at_gamma1"]
        v8[cname] = bool(
            dev <= f_allow
            and abs(fc[0]) <= allow["force_xy_symmetry_N"]
            and abs(fc[1]) <= allow["force_xy_symmetry_N"]
            and a_dev <= a_allow
            and pos32[ci][0] == np.float32(0.0)
            and pos32[ci][1] == np.float32(0.0)
            and pos32[ci][2] == np.float32(0.125))
    ck("V8_analytic_within_preregistered_allowances", all(v8.values()),
       {"per_case": v8,
        "dev_centre_z_gamma1": float(cases["gamma1"]["vforce"][ci][2] - Fcz_an),
        "allow_z_gamma1": allow["force_z_N"],
        "area_dev_gamma1": float(abs(np.sum(cases["gamma1"]["areas"]) - A_an)),
        "allow_area_gamma1": allow["area_J_at_gamma1"]})

    # ---- V9 assembly budgets recompute bitwise + contract eta_5 -------------
    v9 = {}
    for cname, cd in cases.items():
        eta_d = np.array([eta_of(float(d) - 1.0) for d in counts])
        abs_c = np.abs(cd["corner"].astype("<f4").astype(np.float64)
                       .reshape(-1, 3))
        budgets = eta_d[:, None] * np.add.reduceat(
            abs_c[corner_idx], offsets[:-1], axis=0)
        v9[cname] = bool(np.array_equal(budgets, cd["budget"]))
    eta5 = eta_of(5.0)
    # [CORRECTION 2026-09-07, first verify run 21:12Z] the contract prints
    # eta_5 ~= 2.980233126948216e-7 (16 digits); the float64 value is
    # 2.9802331269482156e-07, so bitwise equality to the decimal literal was
    # overreach. Agreement to < 1e-15 relative is the honest check; the
    # structural identity eta_5 == 5u/(1-5u) stays bitwise.
    ck("V9_budgets_bitwise_recompute_and_eta5_contract",
       all(v9.values()) and eta5 == 5.0 * U_F32 / (1.0 - 5.0 * U_F32)
       and abs(eta5 - 2.980233126948216e-7) <= 1e-15 * abs(eta5),
       {"eta5": eta5, "eta11": eta_of(11.0),
        "budget_centre_gamma1_N": cases["gamma1"]["budget"][ci].tolist(),
        "budget_max_rim_gamma1_N": cases["gamma1"]["budget"][:n_rim]
        .max(axis=0).tolist()})

    res["all_pass"] = all(checks.values())
    return res


def eta_of(n: float) -> float:
    return n * U_F32 / (1.0 - n * U_F32)


def run_corrupt_control() -> dict:
    """Swap corner slots 0<->1 of face 0 (b2 gamma1) in a temp copy, update
    the copied manifest hash, and require verification to FAIL."""
    global _EV
    tmp = Path(tempfile.mkdtemp(prefix="glm_freeze_corrupt_"))
    try:
        dst = tmp / "gpu_fixtures"
        shutil.copytree(_EV, dst)
        p = dst / "b2" / "case_gamma1" / "corner_forces_f64.npy"
        arr = np.load(p, allow_pickle=False).copy()
        arr[0, 0], arr[0, 1] = arr[0, 1].copy(), arr[0, 0].copy()
        np.save(p, arr, allow_pickle=False)
        man_p = dst / "b2" / "manifest.json"
        man = json.loads(man_p.read_text(encoding="utf-8"))
        for ent in man["files"]:
            if ent["path"] == "case_gamma1/corner_forces_f64.npy":
                ent["sha256"] = sha256_file(p)      # evade the hash check
        man_p.write_text(json.dumps(man, indent=2), encoding="utf-8")
        saved, _EV = _EV, dst
        try:
            res = verify_fixture("b2")
        finally:
            _EV = saved
        detected = not res["all_pass"]
        failed = [k for k, v in res["checks"].items() if not v]
        return {"control": "corner_order_corruption_b2_gamma1",
                "detected": detected, "failed_checks": failed}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    corrupt_only = "--corrupt" in sys.argv
    results = {"what": "GLM-FREEZE verification results",
               "utc": datetime.now(timezone.utc).isoformat(),
               "numpy": np.__version__, "fixtures": []}
    rc = 0
    if not corrupt_only:
        for name in ("b2", "fan12"):
            r = verify_fixture(name)
            results["fixtures"].append(r)
            print(f"[{name}]")
            for k, v in r["checks"].items():
                print(f"  {k:<48} {'PASS' if v else 'FAIL'}")
            if not r["all_pass"]:
                rc = 1
            man = json.loads((_EV / name / "manifest.json")
                             .read_text(encoding="utf-8"))
            c1 = man["cases"]["gamma1"]
            print(f"  gamma1: A={c1['total_area_m2']:.12g} m^2  "
                  f"F_c=({c1['centre_force_N'][0]:+.3e}, "
                  f"{c1['centre_force_N'][1]:+.3e}, "
                  f"{c1['centre_force_N'][2]:+.12g}) N")
            print(f"  budget centre (deg {c1['degree_centre']}, "
                  f"eta={c1['eta_centre']:.6e}): "
                  f"{['%.4e' % b for b in c1['budget_centre_N']]} N")
            print(f"  budget max rim (deg {c1['degree_rim']}, "
                  f"eta={c1['eta_rim']:.6e}): "
                  f"{['%.4e' % b for b in c1['budget_max_rim_N']]} N")
    ctrl = run_corrupt_control()
    results["corrupt_control"] = ctrl
    print(f"[corner-order corruption control] "
          f"{'DETECTED (control PASS)' if ctrl['detected'] else 'NOT DETECTED (control FAIL)'}"
          f"  failed_checks={ctrl['failed_checks']}")
    if not ctrl["detected"]:
        rc = 1
    out = _EV / ("verify_results_corrupt.json" if corrupt_only else
                 f"verify_results_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')}.json")
    if out.exists():
        raise SystemExit(f"evidence_path_exists: {out}")
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"  results: {out}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
