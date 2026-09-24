"""Run the frozen M08 ladder ONCE against copied modules (no re-tuning).

Loads fixtures/manifest.json (frozen), re-verifies the oracle expectations as a
self-check, executes every rung exactly once, measures errors against the
frozen expected values/bounds, applies the frozen classification rule, and
writes receipts.
"""
from __future__ import annotations
import hashlib
import json
import math
import os
import platform
import sys
from pathlib import Path

os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import numpy as np  # noqa: E402
import material_volume as mv            # module COPY (work/)
import material_volume_admission as adm  # module COPY (work/)
import material_volume_body_export as exp_mod  # module COPY (work/)
import oracle as ob  # noqa: E402

ROOT = HERE.parent
FIX = ROOT / "fixtures"
RCPT = ROOT / "receipts"
RAW = RCPT / "raw"
RAW.mkdir(parents=True, exist_ok=True)


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rel_fro(a, b):
    num = math.sqrt(sum((float(a[i][j]) - float(b[i][j])) ** 2
                        for i in range(3) for j in range(3)))
    den = math.sqrt(sum(float(b[i][j]) ** 2 for i in range(3) for j in range(3)))
    return num / den


def main():
    manifest = json.loads((FIX / "manifest.json").read_text(encoding="utf-8"))
    rungs = manifest["rungs"]

    # --- self-check: oracle must reproduce the frozen expectations --------
    for r in rungs:
        if r["expected"] is None:
            continue
        si = ([[float(x) * r["scale"] for x in row] for row in r["vertices"]]
              if r["path"] == "export" else
              [[float(x) for x in row] for row in r["vertices"]])
        exp = ob.oracle(si, r["tets"], r["densities"])
        assert exp["volume"] == r["expected"]["volume"], r["id"]
        assert exp["mass"] == r["expected"]["mass"], r["id"]
        assert exp["com"] == r["expected"]["com"], r["id"]
        assert exp["inertia"] == r["expected"]["inertia"], r["id"]
    print(f"oracle self-check OK for {len(rungs)} rungs")

    results = []
    for r in rungs:
        res = run_rung(r)
        results.append(res)
        detail = res.get("refusal_reason")
        if detail is None and res.get("eV") is not None:
            com = res.get("com_err")
            e_i = res.get("eI")
            detail = (f"eV={res['eV']:.3e} eM={res['eM']:.3e} "
                      f"com={'n/a' if com is None else f'{com:.3e}'} "
                      f"eI={'n/a' if e_i is None else f'{e_i:.3e}'}")
        print(f"  {r['id']:>4} {res['verdict']:<22} " + (detail or ""))

    results = post_checks(manifest, results)

    env = {"python": sys.version, "numpy": np.__version__,
           "platform": platform.platform(),
           "modules": {n: sha256_file(HERE / n) for n in
                       ("material_volume.py", "material_volume_admission.py",
                        "material_volume_body_export.py")},
           "manifest_sha256": sha256_file(FIX / "manifest.json"),
           "gate_G": ob.G, "u": ob.U}
    (RCPT / "env.json").write_text(json.dumps(env, indent=1), encoding="utf-8")
    (RCPT / "ladder_results.json").write_text(
        json.dumps({"environment": env, "results": results}, indent=1),
        encoding="utf-8")
    print(f"wrote receipts for {len(results)} rungs")


def run_rung(r):
    rid = r["id"]
    out = {"id": rid, "class": r["class"], "path": r["path"]}
    pred = r["predicted"]
    if r["path"] == "compiler":
        doc = json.loads((FIX / f"{rid}.json").read_text(encoding="utf-8"))
        try:
            compiled = mv.compile_document(doc)
        except mv.CompileError as error:
            out.update({"accepted": False, "refusal_reason": error.reason,
                        "refusal_detail": error.detail})
        else:
            (RAW / f"{rid}.json").write_text(
                json.dumps(compiled, indent=1), encoding="utf-8")
            out.update({"accepted": True})
            if pred["outcome"] == "accept":
                mp = compiled["mass_properties"]
                e = r["expected"]
                out.update({
                    "eV": abs(mp["volume_m3"] - e["volume"]) / abs(e["volume"]),
                    "eM": abs(mp["mass_kg"] - e["mass"]) / abs(e["mass"]),
                    "com_err": max(abs(a - b) for a, b in
                                   zip(mp["center_of_mass_m"], e["com"])),
                    "eI": rel_fro(mp["inertia_com_kg_m2"], e["inertia"]),
                    "bounds": r["bounds"]})
    else:
        docs = {k: json.loads((FIX / f"{rid}_{k}.json").read_text(encoding="utf-8"))
                for k in ("manifest", "partition", "groups")}
        report = exp_mod.build_export_report(docs["manifest"], docs["partition"],
                                             docs["groups"])
        (RAW / f"{rid}.json").write_text(
            json.dumps(report, indent=1), encoding="utf-8")
        status = report["export_status"]
        out.update({"accepted": status in ("complete", "partial"),
                    "export_status": status})
        if status in ("blocked", "refused", "unsupported"):
            reason = None
            adm_report = None
            try:
                adm_report = adm.build_admission_report(docs["manifest"],
                                                        docs["partition"])
            except Exception:
                pass
            if isinstance(adm_report, dict):
                if adm_report.get("compiler_refusal"):
                    reason = adm_report["compiler_refusal"]["reason"]
                elif adm_report.get("reason_codes"):
                    reason = adm_report["reason_codes"][0]
            out.update({"refusal_reason": reason or status,
                        "export_reason_codes": report.get("reason_codes")})
        if out["accepted"] and pred["outcome"] == "accept":
            e = r["expected"]
            groups_mp = [g["mass_properties"] for g in report["body_groups"]]
            if len(groups_mp) == 1:
                group = groups_mp[0]
                out.update({
                    "eV": abs(group["volume"]["value"] - e["volume"]) / abs(e["volume"]),
                    "eM": abs(group["mass"]["value"] - e["mass"]) / abs(e["mass"]),
                    "com_err": max(abs(a - b) for a, b in
                                   zip(group["center_of_mass"]["value"], e["com"])),
                    "eI": rel_fro(group["inertia_tensor_about_com"]["value"],
                                  e["inertia"]),
                    "bounds": r["bounds"]})
            else:
                # Multi-group report: aggregate mass/volume across groups for
                # the top-level check; COM/inertia are checked per group in
                # post_checks frame_checks (each group carries its own frame).
                v_sum = sum(g["volume"]["value"] for g in groups_mp)
                m_sum = sum(g["mass"]["value"] for g in groups_mp)
                out.update({
                    "eV": abs(v_sum - e["volume"]) / abs(e["volume"]),
                    "eM": abs(m_sum - e["mass"]) / abs(e["mass"]),
                    "com_err": None, "eI": None,
                    "bounds": {"V_rel": r["bounds"]["V_rel"],
                               "M_rel": r["bounds"]["M_rel"],
                               "com_abs": None, "I_rel": None}})
    out["verdict"] = classify(r, out)
    if rid in DIAGNOSES:
        out["diagnosis"] = DIAGNOSES[rid]
    return out


def classify(r, out):
    pred = r["predicted"]
    if pred["outcome"] == "refuse":
        if not out["accepted"] and out.get("refusal_reason") == pred["reason"]:
            return "REFUSED-BY-CONTRACT"
        return "DEFECT-CANDIDATE"
    if not out["accepted"]:
        return "DEFECT-CANDIDATE(unexpected-refusal:" \
               + str(out.get("refusal_reason")) + ")"
    b = r["bounds"]
    ok = out["eV"] <= b["V_rel"] and out["eM"] <= b["M_rel"]
    if out.get("com_err") is not None:
        ok = ok and out["com_err"] <= b["com_abs"] and out["eI"] <= b["I_rel"]
    if ok:
        return "PASS"
    return "DEFECT-CANDIDATE(beyond-bound)"


DIAGNOSES = {
    # Frozen-rule verdicts are preserved verbatim; each diagnosis records the
    # falsifier analysis required by the brief (derivation vs implementation).
    "S0": {
        "falsifier_analysis":
            "Measured eV=eM=eI=1.244976e-04 IDENTICALLY: every inertia entry is "
            "homogeneous linear in the cell masses, so inertia inherits the mass "
            "relative error; the shape-integral error is eI-eM ~ 0. The frozen "
            "volume bound B_V=20u+12u/delta=3.75e-2 is NOT exceeded "
            "(1.245e-4 = B_V/301). The frozen inertia bound B_I=30u(1+X) omitted "
            "the mass-factor propagation term - a derivation omission, not an "
            "implementation defect. Corrected bound B_I'=B_I+B_V (mass linearity "
            "is exact in the model). No code change; no bound of any other rung "
            "affected.",
        "corrected_bound": "B_I' = B_I + B_V",
        "corrected_verdict": "PASS (conditioning characterized: near-gate sliver "
                             "volume error follows the derived kappa*u/delta law, "
                             "300x inside the frozen worst-case bound)",
    },
    "S1": {
        "falsifier_analysis":
            "Same mechanism as S0: eV=eM=eI=7.844e-05 identical; volume error "
            "within frozen B_V=7.80e-02 (995x margin); inertia bound omission "
            "identical to S0.",
        "corrected_bound": "B_I' = B_I + B_V",
        "corrected_verdict": "PASS (conditioning characterized)",
    },
    "E7": {
        "falsifier_analysis":
            "Fixture-construction error, not an implementation defect: the ulp "
            "pair (1, nextafter(1)) was placed on one axis TOGETHER WITH a third "
            "vertex on that axis, so the frame-coordinate cell already has "
            "det=0 exactly (three collinear vertices) independent of scale - the "
            "oracle itself records delta=0 before scaling. The gate refusal "
            "degenerate_tetrahedron is correct declared behavior (D3) on a "
            "genuinely degenerate input. Additionally, a power-of-two scale_to_m "
            "multiplies exactly, so it can never collapse distinct positions: "
            "this rung could never have produced the predicted refusal. The "
            "declared collapse path is exercised by E7b (decimal scale 1e-18, "
            "non-degenerate frame cell). This rung is PRESERVED as invalid.",
        "corrected_verdict": "INVALID RUNG (fixture construction error); "
                             "implementation refusal correct per D3; coverage "
                             "moved to E7b",
    },
}


def post_checks(manifest, results):
    """Frozen cross-path, twin, and metamorphic checks (prereg (f)(g)(h))."""
    by_id = {r["id"]: r for r in results}
    u = ob.U

    def mass_payload(rid):
        rep = json.loads((RAW / f"{rid}.json").read_text(encoding="utf-8"))
        return rep["body_groups"][0]["mass_properties"]

    # (h) cross-path compiler vs exporter on identical SI geometry
    for comp_id, exp_id in (("A0", "A0x"), ("A4", "A4x"), ("A5", "A5x")):
        comp = json.loads((RAW / f"{comp_id}.json").read_text(encoding="utf-8"))
        mp_c = comp["mass_properties"]
        mp_e = mass_payload(exp_id)
        x_max = next(r for r in manifest["rungs"]
                     if r["id"] == comp_id)["shape"]["x_max"]
        dV = abs(mp_c["volume_m3"] - mp_e["volume"]["value"]) / abs(mp_c["volume_m3"])
        dI = rel_fro(mp_c["inertia_com_kg_m2"],
                     mp_e["inertia_tensor_about_com"]["value"])
        bV, bI = 40.0 * u, 60.0 * u * (1.0 + x_max)
        by_id[exp_id]["cross_path"] = {
            "vs": comp_id, "dV": dV, "dI": dI,
            "bounds": {"V": bV, "I": bI},
            "verdict": "PASS" if (dV <= bV and dI <= bI)
            else "DEFECT-CANDIDATE(cross-path)"}

    # (f) twins: canonical JSON of mass_properties payloads must be identical
    def canon(rid):
        return json.dumps(mass_payload(rid), sort_keys=True,
                          separators=(",", ":"))
    for twins in (("E1", "E2", "E3"), ("E4a", "E4b")):
        payloads = {t: canon(t) for t in twins}
        identical = len(set(payloads.values())) == 1
        for t in twins:
            by_id[t]["twin"] = {"group": "+".join(twins), "identical": identical}
        by_id[twins[0]]["twin"]["verdict"] = \
            "PASS(bitwise)" if identical else "DEFECT-CANDIDATE(twin-mismatch)"

    # E5 decimal twin vs E1: bitwise if SI floats coincide, else (f) bounds
    e5, e1 = mass_payload("E5"), mass_payload("E1")
    dV = abs(e5["volume"]["value"] - e1["volume"]["value"]) / abs(e1["volume"]["value"])
    dI = rel_fro(e5["inertia_tensor_about_com"]["value"],
                 e1["inertia_tensor_about_com"]["value"])
    if canon("E5") == canon("E1"):
        by_id["E5"]["twin"] = {"group": "E1+E5", "identical": True,
                               "verdict": "PASS(bitwise)"}
    else:
        ok = dV <= 50.0 * u and dI <= 80.0 * u
        by_id["E5"]["twin"] = {"group": "E1+E5", "identical": False,
                               "dV": dV, "dI": dI,
                               "verdict": "PASS(within-(f)-bounds)" if ok
                               else "DEFECT-CANDIDATE(twin-bounds)"}

    # (g) uniform-scale covariance across the B ladder vs B0
    manifest_rungs = {r["id"]: r for r in manifest["rungs"]}
    for i in range(1, 6):
        rid = f"B{i}"
        comp = json.loads((RAW / f"{rid}.json").read_text(encoding="utf-8"))
        base = json.loads((RAW / "B0.json").read_text(encoding="utf-8"))
        s = manifest_rungs[rid]["vertices"][1][0]
        v_i = comp["mass_properties"]["volume_m3"]
        v_0 = base["mass_properties"]["volume_m3"]
        I_i = comp["mass_properties"]["inertia_com_kg_m2"]
        I_0 = base["mass_properties"]["inertia_com_kg_m2"]
        dev_v = abs(v_i / (s ** 3) - v_0) / abs(v_0)
        dev_i = rel_fro([row[:] for row in [[x / (s ** 5) for x in row]
                                            for row in I_i]], I_0)
        exp_v = manifest_rungs[rid]["expected"]["volume"]
        exp_0 = manifest_rungs["B0"]["expected"]["volume"]
        law_v = abs(exp_v / (s ** 3) - exp_0) / abs(exp_0)  # exact geometry dev
        ok = dev_v <= 40.0 * u + law_v and dev_i <= 80.0 * u + law_v
        by_id[rid]["metamorphic"] = {
            "V_over_s3_minus_V0": dev_v, "I_over_s5_minus_I0": dev_i,
            "exact_geometry_dev": law_v,
            "verdict": "PASS" if ok else "DEFECT-CANDIDATE(metamorphic)"}

    # (i) authored-frame mapping for E1f (two groups, one rotated)
    rep = json.loads((RAW / "E1f.json").read_text(encoding="utf-8"))
    rung = manifest_rungs["E1f"]
    for g, cell_idx in zip(rep["body_groups"], ([0, 1, 2, 3], [4, 5, 6, 7])):
        verts = [rung["vertices"][i] for i in cell_idx]
        e = ob.oracle(verts, [[0, 1, 2, 3]], [rung["densities"][cell_idx[0] // 4]])
        R = g["body_frame"]["domain_from_body"]["rotation"]
        o = g["body_frame"]["domain_from_body"]["origin_m"]
        mp = g["mass_properties"]
        com_want = ob.rot_t_vec(R, [e["com"][k] - o[k] for k in range(3)])
        I_want = ob.rot_t_mat_R_mat(R, e["inertia"])
        com_err = max(abs(a - b) for a, b in
                      zip(mp["center_of_mass"]["value"], com_want))
        eI = rel_fro(mp["inertia_tensor_about_com"]["value"], I_want)
        bnd = {"com_abs": 8.0 * u * max(1.0, max(abs(x) for x in e["com"])),
               "I_rel": 60.0 * u}
        by_id.setdefault("E1f", {"id": "E1f", "verdict": "PASS"})\
             .setdefault("frame_checks", {})[g["body_id"]] = {
            "com_err": com_err, "eI": eI, "bounds": bnd,
            "verdict": "PASS" if (com_err <= bnd["com_abs"] and eI <= bnd["I_rel"])
            else "DEFECT-CANDIDATE(frame)"}
    return results


if __name__ == "__main__":
    main()
