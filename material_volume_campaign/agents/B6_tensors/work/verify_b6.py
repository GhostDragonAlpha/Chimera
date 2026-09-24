"""B6 verification -- apply the three preregistered check families.

Reads ONLY: fixtures (geometry, authored frames), receipts/export_report.json
(exporter output), prereg_predictions.json (frozen predictions + tolerances).
All recomputation here is B6-owned float64 code, algebraically distinct from the
exporter's cellwise accumulation (route C: origin second moments; route B:
cellwise q-form + parallel axis with B6-recomputed COM), and from the exact
Fraction derivation (which never reads exporter output).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def mat3(rows):
    return np.asarray(rows, dtype=np.float64)


def check_body(body_id, report_group, partition, groups, pred, tol, results):
    checks = {}
    mp = report_group["mass_properties"]
    I_exp = mat3(mp["inertia_tensor_about_com"]["value"])
    m_exp = float(mp["mass"]["value"])
    com_exp_body = np.asarray(mp["center_of_mass"]["value"], dtype=np.float64)

    # ---------- (a) SYMMETRY ----------
    asym = float(np.abs(I_exp - I_exp.T).max())
    exact_symmetric = bool(np.array_equal(I_exp, I_exp.T))
    checks["A_max_abs_asym"] = asym
    checks["A_exact_bit_symmetric"] = exact_symmetric
    checks["A_bound"] = tol["A_symmetry_max_abs_asym"]
    checks["A_pass"] = asym <= tol["A_symmetry_max_abs_asym"]

    # ---------- (b) PRINCIPAL MOMENTS ----------
    ev_general = np.linalg.eigvals(I_exp)
    max_imag = float(np.abs(ev_general.imag).max())
    lam = np.sort(np.linalg.eigvalsh(I_exp))
    l1, l2, l3 = lam
    margins = np.array([l1 + l2 - l3, l1 + l3 - l2, l2 + l3 - l1])
    det_exp = float(np.linalg.det(I_exp))
    trace_exp = float(np.trace(I_exp))

    lam_pred = np.asarray(pred["eigenvalues_body_sorted"], dtype=np.float64)
    det_pred = float(pred["det_inertia_exact"]["fraction"].split("/")[0]) / \
        float(pred["det_inertia_exact"]["fraction"].split("/")[1]) \
        if "/" in pred["det_inertia_exact"]["fraction"] else float(pred["det_inertia_exact"]["float"])
    trace_pred = float(pred["trace_exact"]["float"])
    m_pred = float(pred["mass_kg"]["float"])
    com_pred_body = np.asarray([x["float"] for x in pred["com_body_m"]], dtype=np.float64)

    b = {}
    b["eig_max_abs_imag"] = max_imag
    b["eig_imag_bound"] = tol["B_eig_max_abs_imag"]
    b["eig_imag_pass"] = max_imag <= tol["B_eig_max_abs_imag"]

    b["min_eigenvalue"] = float(l1)
    b["positivity_pass"] = bool(l1 > 0.0)

    b["triangle_margins"] = [float(x) for x in margins]
    b["triangle_universal_pass"] = bool(margins.min() >= tol["B_triangle_margin_min_abs"])
    b["triangle_fixture_strict_pass"] = bool(
        margins[0] > 0.0) if tol["B_triangle_margin_fixture_strict_positive"] else True

    b["det"] = det_exp
    b["det_positive_pass"] = bool(det_exp > 0.0)
    b["det_rel_err"] = abs(det_exp - det_pred) / abs(det_pred)
    b["det_rel_bound"] = tol["B_det_vs_pred_rel"]
    b["det_consistency_pass"] = b["det_rel_err"] <= tol["B_det_vs_pred_rel"]

    b["trace"] = trace_exp
    b["trace_rel_err"] = abs(trace_exp - trace_pred) / abs(trace_pred)
    b["trace_rel_bound"] = tol["B_trace_vs_pred_rel"]
    b["trace_consistency_pass"] = b["trace_rel_err"] <= tol["B_trace_vs_pred_rel"]

    b["eigenvalues"] = [float(x) for x in lam]
    b["eigenvalues_predicted"] = [float(x) for x in lam_pred]
    b["eig_pred_max_abs_err"] = float(np.abs(lam - lam_pred).max())
    b["eig_pred_abs_bound"] = tol["B_eigenvalues_vs_pred_abs"]
    b["eig_pred_pass"] = b["eig_pred_max_abs_err"] <= tol["B_eigenvalues_vs_pred_abs"]

    b["mass"] = m_exp
    b["mass_rel_err"] = abs(m_exp - m_pred) / abs(m_pred)
    b["mass_rel_bound"] = tol["B_mass_vs_pred_rel"]
    b["mass_pass"] = b["mass_rel_err"] <= tol["B_mass_vs_pred_rel"]

    b["com_body"] = [float(x) for x in com_exp_body]
    b["com_pred_body"] = [float(x) for x in com_pred_body]
    b["com_max_abs_err_m"] = float(np.abs(com_exp_body - com_pred_body).max())
    b["com_abs_bound_m"] = tol["B_com_vs_pred_abs_m"]
    b["com_pass"] = b["com_max_abs_err_m"] <= tol["B_com_vs_pred_abs_m"]

    b["pass"] = all(v for k, v in b.items() if k.endswith("_pass"))
    checks["B"] = b

    # ---------- (c) PARALLEL-AXIS RECOMBINATION (independent) ----------
    vertices = {v["vertex_id"]: np.asarray(v["position"], dtype=np.float64)
                for v in partition["vertices"]}
    scale = float(partition["coordinate_frame"]["scale_to_m"])
    cell_rows = {c["cell_id"]: c for c in partition["cells"]}
    provenance = {row["cell_id"]: row for row in report_group["cell_provenance"]}

    group = next(g for g in groups["body_groups"] if g["body_id"] == body_id)
    R = mat3(group["body_frame"]["domain_from_body"]["rotation"])
    origin = np.asarray(group["body_frame"]["domain_from_body"]["origin_m"],
                        dtype=np.float64)

    cells = []
    for cid in sorted(group["cell_ids"]):
        rho = float(provenance[cid]["density_kg_m3"])
        p = np.asarray([vertices[vid] * scale
                        for vid in cell_rows[cid]["vertex_ids"]], dtype=np.float64)
        vol = float(np.linalg.det(np.column_stack([p[1] - p[0], p[2] - p[0],
                                                   p[3] - p[0]]))) / 6.0
        m = vol * rho
        c = p.mean(axis=0)
        cells.append({"m": m, "c": c, "p": p, "vol": vol})

    M = sum(cell["m"] for cell in cells)
    com = sum(cell["m"] * cell["c"] for cell in cells) / M

    # Route B: cellwise q-form covariance + parallel axis
    I_cw = np.zeros((3, 3))
    for cell in cells:
        q = cell["p"] - cell["c"]
        J = (cell["m"] / 20.0) * sum(np.outer(q[i], q[i]) for i in range(4))
        d = cell["c"] - com
        I_cw += np.trace(J) * np.eye(3) - J \
            + cell["m"] * (np.dot(d, d) * np.eye(3) - np.outer(d, d))

    # Route C: origin second moments, then shift by total COM
    W = np.zeros((3, 3))
    for cell in cells:
        c = cell["c"]
        E = sum(np.outer(p, p) for p in cell["p"]) / 20.0 + (4.0 / 5.0) * np.outer(c, c)
        W += cell["m"] * E
    cc = np.outer(com, com)
    I_org = (np.trace(W) * np.eye(3) - W) - (M * np.trace(cc) * np.eye(3) - M * cc)

    I_cw_body = R.T @ I_cw @ R
    I_org_body = R.T @ I_org @ R
    scale_ref = float(np.abs(I_exp).max())

    c_blk = {}
    for name, I_rec in (("route_B_cellwise", I_cw_body), ("route_C_origin", I_org_body)):
        diff = float(np.abs(I_rec - I_exp).max())
        c_blk[f"{name}_max_abs_diff"] = diff
        c_blk[f"{name}_rel"] = diff / scale_ref
        c_blk[f"{name}_bound"] = tol["C_recomb_max_rel_to_tensor_scale"]
        c_blk[f"{name}_pass"] = c_blk[f"{name}_rel"] <= tol["C_recomb_max_rel_to_tensor_scale"]
    c_blk["recomputed_mass"] = M
    c_blk["mass_diff"] = abs(M - m_exp)
    c_blk["recomputed_com_body"] = [float(x) for x in (R.T @ (com - origin))]
    c_blk["pass"] = all(v for k, v in c_blk.items() if k.endswith("_pass"))
    checks["C"] = c_blk

    checks["pass"] = bool(checks["A_pass"] and checks["B"]["pass"] and checks["C"]["pass"])
    results[body_id] = checks


def main():
    partition = load(ROOT / "fixtures" / "partition.json")
    groups = load(ROOT / "fixtures" / "groups.json")
    report = load(ROOT / "receipts" / "export_report.json")
    pred = load(ROOT / "prereg_predictions.json")
    tol = pred["tolerances_frozen"]

    assert report["export_status"] == "complete", "exporter did not complete"
    assert report["admission_status"] == "validation_only_admissible"
    assert not report["reason_codes"] and not report["unassigned_cell_ids"]

    results = {"meta": {
        "export_status": report["export_status"],
        "admission_status": report["admission_status"],
        "export_report_groups": [g["body_id"] for g in report["body_groups"]],
        "predictions_sha256_freeze": "9aa4147c00b2e08d3b43e229ffabae0524524a6a26eed934eeded09247dad64b",
    }}
    for group in report["body_groups"]:
        body_id = group["body_id"]
        check_body(body_id, group, partition, groups, pred["bodies"][body_id], tol, results)

    out = ROOT / "receipts" / "check_results.json"
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(results, f, indent=2)
        f.write("\n")

    bodies = [g["body_id"] for g in report["body_groups"]]
    print("=" * 100)
    print("B6 VERDICT TABLES  (falsifier = any measured value beyond frozen bound)")
    print("=" * 100)
    hdr = f"{'check':58s}" + "".join(f"{b[:18]:>20s}" for b in bodies)
    rows = []

    def add(label, getter):
        rows.append((label, {b: getter(results[b]) for b in bodies}))

    add("A  max|I-I^T| <= 1e-15", lambda r: f"{r['A_max_abs_asym']:.3e} {'PASS' if r['A_pass'] else 'FAIL'}")
    add("A  bit-exact symmetric", lambda r: str(r["A_exact_bit_symmetric"]))
    add("B  max|Im(eig)| <= 1e-12", lambda r: f"{r['B']['eig_max_abs_imag']:.3e} {'PASS' if r['B']['eig_imag_pass'] else 'FAIL'}")
    add("B  min eigenvalue > 0", lambda r: f"{r['B']['min_eigenvalue']:.6f} {'PASS' if r['B']['positivity_pass'] else 'FAIL'}")
    add("B  triangle margins [l1+l2-l3, l1+l3-l2, l2+l3-l1]",
        lambda r: f"{r['B']['triangle_margins'][0]:.4f}/{r['B']['triangle_margins'][1]:.3f}/{r['B']['triangle_margins'][2]:.1f} "
                  f"{'PASS' if r['B']['triangle_universal_pass'] and r['B']['triangle_fixture_strict_pass'] else 'FAIL'}")
    add("B  det > 0 and rel err vs exact <= 1e-12",
        lambda r: f"{r['B']['det']:.4f} e={r['B']['det_rel_err']:.2e} {'PASS' if r['B']['det_consistency_pass'] and r['B']['det_positive_pass'] else 'FAIL'}")
    add("B  trace rel err vs 2*sum(trJ+m d^2) <= 1e-12",
        lambda r: f"{r['B']['trace_rel_err']:.3e} {'PASS' if r['B']['trace_consistency_pass'] else 'FAIL'}")
    add("B  max|eig-exp| vs frozen pred <= 1e-9",
        lambda r: f"{r['B']['eig_pred_max_abs_err']:.3e} {'PASS' if r['B']['eig_pred_pass'] else 'FAIL'}")
    add("B  mass rel err <= 1e-12", lambda r: f"{r['B']['mass_rel_err']:.3e} {'PASS' if r['B']['mass_pass'] else 'FAIL'}")
    add("B  com max abs err (m) <= 1e-12",
        lambda r: f"{r['B']['com_max_abs_err_m']:.3e} {'PASS' if r['B']['com_pass'] else 'FAIL'}")
    add("C  route B (cellwise) rel diff <= 1e-12",
        lambda r: f"{r['C']['route_B_cellwise_rel']:.3e} {'PASS' if r['C']['route_B_cellwise_pass'] else 'FAIL'}")
    add("C  route C (origin 2nd moments) rel diff <= 1e-12",
        lambda r: f"{r['C']['route_C_origin_rel']:.3e} {'PASS' if r['C']['route_C_origin_pass'] else 'FAIL'}")
    print(hdr)
    for label, vals in rows:
        print(f"{label:58s}" + "".join(f"{vals[b]:>20s}" for b in bodies))
    print("-" * 100)
    for b in bodies:
        print(f"{b:58s} {'PASS' if results[b]['pass'] else 'FAIL':>20s}")
    print("=" * 100)
    all_pass = all(results[b]["pass"] for b in bodies)
    print("OVERALL:", "ALL GREEN" if all_pass else "FALSIFIER FIRED (preserve, classify)")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
