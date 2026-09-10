"""CPU-only domain audit using the committed frozen STVK fixture."""
from __future__ import annotations
import argparse, glob, json, math
from pathlib import Path
import numpy as np
try:
    from .geometry import build_rest_geometry
    from .law import evaluate_elastic
    from .materials import synthetic, validate_material
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from elastic_foundation.geometry import build_rest_geometry
    from elastic_foundation.law import evaluate_elastic
    from elastic_foundation.materials import synthetic, validate_material

PROVENANCE = ["docs/evidence/elastic_foundation/DERIVATION.md§§2-3,6,12",
              "docs/evidence/elastic_foundation/GPU_HANDOFF.md§§3-4",
              "docs/evidence/elastic_foundation/fixtures/v1/run_20260908T231140Z/trisingle_stretch.npz"]

def _refusal(name, fn):
    try: fn()
    except ValueError as exc:
        return {"name": name, "status": "refused", "reason": getattr(exc, "reason", type(exc).__name__)}
    return {"name": name, "status": "accepted"}

def audit(fixture=None):
    fixture = fixture or sorted(glob.glob("docs/evidence/elastic_foundation/fixtures/v1/*/trisingle_stretch.npz"))[-1]
    z = np.load(fixture); rest_pos = z["rest_pos"].astype(np.float64); cur = z["cur_pos"].astype(np.float64)
    faces = z["faces_int32"].astype(np.int64); E = float(z["E_f64"]); nu = float(z["nu_f64"]); h = float(z["h_f64"])
    rest = build_rest_geometry(rest_pos, faces, build_info={"units": "m", "source": fixture})
    mat = synthetic("frozen-fixture", E=E, nu=nu, h=h); base = evaluate_elastic(rest, mat, cur)
    expected_energy = float(z["exp_energy_f64"]); expected_forces = z["exp_vertex_f64"].astype(np.float64)
    Q = np.array([[0., 1., 0.], [0., 0., 1.], [1., 0., 0.]])
    rigid = evaluate_elastic(rest, mat, cur @ Q.T)
    covariance = np.max(np.abs(rigid.vertex_forces - base.vertex_forces @ Q.T))
    mutation = evaluate_elastic(rest, mat, cur, _mutations={"eulerian_frame": True})
    mutation_rot = evaluate_elastic(rest, mat, cur @ Q.T, _mutations={"eulerian_frame": True})
    mutation_covariance = np.max(np.abs(mutation_rot.vertex_forces - mutation.vertex_forces @ Q.T))
    reflected = evaluate_elastic(rest, mat, cur*np.array([-1.,1.,1.]))
    lam, mu, area = mat.lambda_bar, mat.mu_bar, float(np.sum(rest.areas0))
    compression = []
    for s in (1.0, 1.0 / math.sqrt(3.0), 1.0e-6):
        e = (s*s-1.0)/2.0; analytic = area * 2.0 * (lam+mu) * e*e
        ev = evaluate_elastic(rest, mat, rest_pos*s)
        compression.append({"scale": s, "energy": ev.energy, "analytic_energy": analytic,
                            "abs_error": abs(ev.energy-analytic)})
    alg = 512.0 * np.finfo(np.float64).eps
    energy_budget = alg * max(abs(expected_energy), np.finfo(np.float64).tiny)
    force_budget = alg * max(float(np.max(np.abs(expected_forces))), np.finfo(np.float64).tiny)
    oracle_energy_error = abs(base.energy - expected_energy)
    oracle_force_error = float(np.max(np.abs(base.vertex_forces - expected_forces)))
    return {"schema": "elastic-domain-audit-2", "status": "bounded_diagnostic", "fixture": fixture,
            "provenance": PROVENANCE,
            "proper_rotation": {"matrix": Q.tolist(), "det": float(np.linalg.det(Q)),
                                "energy_delta": abs(rigid.energy-base.energy), "force_covariance_max": float(covariance),
                                "energy_budget": energy_budget, "force_budget": force_budget,
                                "gate": "PASS" if covariance <= force_budget and abs(rigid.energy-base.energy) <= energy_budget else "FAIL"},
            "frozen_oracle": {"expected_energy": expected_energy, "expected_force_max": float(np.max(np.abs(expected_forces))),
                              "energy_error": oracle_energy_error, "force_error_max": oracle_force_error,
                              "energy_budget": energy_budget, "force_budget": force_budget},
            "known_law_mutation": {"name": "eulerian_frame", "energy_delta": abs(mutation.energy-base.energy),
                                   "force_covariance_max": float(mutation_covariance),
                                   "covariance_broken": bool(mutation_covariance>force_budget), "status": "known_failure"},
            "reflection": {"status": "accepted_with_inversion_flag", "inverted_faces": int(np.count_nonzero(reflected.per_face.inverted)),
                           "expected_inverted_faces": int(len(faces)), "energy": reflected.energy,
                           "force_finite": bool(np.all(np.isfinite(reflected.vertex_forces)))},
            "compression": compression,
            "units": {"E_input": "Pa", "h_input": "m", "per_area_energy": "force/length",
                      "same_pose_energy_h": base.energy, "same_pose_energy_2h": evaluate_elastic(rest,synthetic("2h",E=E,nu=nu,h=2*h),cur).energy,
                      "contract": "CONTRACT_CONFLICT_NOT_CERTIFIED: lambda_bar/mu_bar omit h; law uses implicit unit thickness"},
            "negative_controls": [_refusal("collapsed_triangle", lambda: evaluate_elastic(rest,mat,np.array([rest_pos[0],rest_pos[0],rest_pos[2]]))),
                                  _refusal("invalid_material", lambda: validate_material(synthetic(E=0.0)))],
            "certification": "NOT_CERTIFIED_UNITS_CONFLICT"}

def _report_gate(r):
    o = r["frozen_oracle"]; rot = r["proper_rotation"]; mut = r["known_law_mutation"]; refl = r["reflection"]
    finite = all(math.isfinite(float(o[k])) for k in ("energy_error", "force_error_max", "expected_energy", "expected_force_max"))
    return ("law_gate" not in r and finite and o["expected_energy"] != 0.0 and o["expected_force_max"] != 0.0
            and o["energy_error"] <= o["energy_budget"] and o["force_error_max"] <= o["force_budget"]
            and rot["energy_delta"] <= o["energy_budget"] and rot["force_covariance_max"] <= o["force_budget"]
            and mut["covariance_broken"] and refl["inverted_faces"] == refl["expected_inverted_faces"]
            and math.isfinite(float(refl["energy"])) and refl["force_finite"]
            and all(math.isfinite(float(c["abs_error"])) and c["abs_error"] <= o["energy_budget"] for c in r["compression"])
            and r["negative_controls"][0].get("reason") == "collapsed_triangle"
            and r["negative_controls"][1].get("reason") == "nonpositive_young_modulus")

def main():
    p=argparse.ArgumentParser(); p.add_argument("--json",action="store_true"); p.add_argument("--assert-clean",action="store_true"); p.add_argument("--self-test",action="store_true"); a=p.parse_args(); r=audit()
    if a.self_test:
        import copy
        for key, edit in (("zero_force", lambda q: q["frozen_oracle"].update(expected_force_max=0.0)),
                          ("energy_offset", lambda q: q["frozen_oracle"].update(energy_error=1.0)),
                          ("nonfinite", lambda q: q["frozen_oracle"].update(force_error_max=float("nan"))),
                          ("mutation_survives", lambda q: q["known_law_mutation"].update(covariance_broken=False)),
                          ("reflection_flag", lambda q: q["reflection"].update(inverted_faces=0)),
                          ("reflection_nonfinite", lambda q: q["reflection"].update(energy=float("nan"))),
                          ("empty_reflection", lambda q: q["reflection"].update(inverted_faces=0, expected_inverted_faces=1)),
                          ("wrong_refusal", lambda q: q["negative_controls"][0].update(reason="other")),
                          ("legacy_gate", lambda q: q.update(law_gate="PASS"))):
            q=copy.deepcopy(r); edit(q)
            if _report_gate(q): print("self-test failure: " + key); return 1
        print("adversarial_gate_controls=PASS")
    r["numeric_gate"] = "PASS" if _report_gate(r) else "FAIL"
    print(json.dumps(r,indent=2,sort_keys=True)); return 0 if not a.assert_clean or r["numeric_gate"]=="PASS" else 1
if __name__ == "__main__": raise SystemExit(main())
