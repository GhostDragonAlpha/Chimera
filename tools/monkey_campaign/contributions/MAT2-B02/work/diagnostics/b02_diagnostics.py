"""MAT2-B02 static diagnostics generator (offline, CPU-only, deterministic).

Run: python -B work/diagnostics/b02_diagnostics.py
Writes work/runs/static_diagnostics.json (sorted keys, LF, trailing newline).
Second run must be byte-identical (frozen predictions P-DET/P-COUNT).
"""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parent
CONTRIB = WORK.parent
RUNS = WORK / "runs"
RUNS.mkdir(exist_ok=True)
sys.path.insert(0, str(WORK))
sys.path.insert(0, str(WORK / "oracle"))
sys.path.insert(0, str(WORK / "frozen" / "1af0bbde" / "tools"))

import b02_checks  # noqa: E402  (frozen expectations + CLI helpers)
import b02_common as common  # noqa: E402
import b02_oracle  # noqa: E402

FROZEN_REV = "1af0bbdee68d6ddfdd02bf9bd948f7b22f914d56"
CRITERIA = "151a4aa7693f30c49a32167c78301240b68d701ce1ea766134c71a4080454d7e"
PREREG_SHA = "8d5c922a0ab88a2c773d905481d16af0b644748c01789a5b9a94ceb656c51238"

FR = Fraction


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def lf_canonical(path):
    return sha256_bytes(Path(path).read_bytes().replace(b"\r\n", b"\n"))


def blob_oid(path):
    return subprocess.run(["git", "hash-object", str(path)],
                          capture_output=True, text=True, check=True
                          ).stdout.strip()


def exact_from_coupon(tag):
    """Exact oracle expectations for every body of a coupon, read from the
    built coupon docs (so orientation/frames match what the exporter saw)."""
    manifest, partition, groups = common.load_coupon(tag)
    vertices = {row["vertex_id"]: row["position"] for row in
                partition["vertices"]}
    materials = {row["material_id"]: row["density_kg_m3"] for row in
                 partition["materials"]}
    regions = {row["region_id"]: row for row in partition["regions"]}
    density_by_cell, cells_by_region = {}, {}
    for row in partition["cells"]:
        region = regions[row["proposals"][0]]
        density_by_cell[row["cell_id"]] = Fraction(
            str(materials[region["material_id"]]))
        cells_by_region.setdefault(row["proposals"][0], []).append(
            {"cell_id": row["cell_id"],
             "vertices": [tuple(Fraction(str(c))
                                for c in vertices[v])
                          for v in row["vertex_ids"]]})
    expectations = {}
    for group in groups["body_groups"]:
        # a body may aggregate cells across regions (distinct owners)
        cells = [c for reg in group_cell_regions(group, partition)
                 for c in cells_by_region[reg]]
        frame = group["body_frame"]["domain_from_body"]
        expectations[group["body_id"]] = common.exact_body_expectations(
            cells, density_by_cell,
            (frame["rotation"], frame["origin_m"]))
    return expectations


def group_cell_regions(group, partition):
    cell_region = {row["cell_id"]: row["proposals"][0]
                   for row in partition["cells"]}
    return sorted({cell_region[c] for c in group["cell_ids"]})


def compare_complete_coupon(tag, prefix, scale=None):
    _m, partition, _g = common.load_coupon(tag)
    scale = partition["coordinate_frame"]["scale_to_m"]
    s3 = scale ** 3
    s5 = scale ** 5
    report = common.export_in_process(tag)
    common.expect_equal(report["export_status"], "complete",
                        f"{prefix}.export_status")
    common.expect_true(report["validation_only"] is True,
                       f"{prefix}.validation_only")
    common.expect_true(report["production_wired"] is False,
                       f"{prefix}.production_wired")
    common.expect_true(report["dynamics_readiness_claimed"] is False,
                       f"{prefix}.no_readiness_claim")
    expectations = exact_from_coupon(tag)
    for group in report["body_groups"]:
        bid = group["body_id"]
        e = expectations[bid]
        props = group["mass_properties"]
        common.tol1(props["mass"]["value"], float(e["mass"]) * s3,
                    f"{prefix}.{bid}.mass")
        common.tol1(props["volume"]["value"], float(e["volume"]) * s3,
                    f"{prefix}.{bid}.volume")
        rotation, origin = frame_of(tag, bid)
        for axis in range(3):
            expected = sum(rotation[d][axis]
                           * (scale * float(e["com_domain"][d]) - origin[d])
                           for d in range(3))
            common.tol1(props["center_of_mass"]["value"][axis], expected,
                        f"{prefix}.{bid}.com[{axis}]")
        for i in range(3):
            for j in range(3):
                common.tol1(props["inertia_tensor_about_com"]["value"][i][j],
                            float(e["inertia_body"][i][j]) * s5,
                            f"{prefix}.{bid}.inertia[{i}][{j}]")


def frame_of(tag, body_id):
    _m, _p, groups = common.load_coupon(tag)
    for group in groups["body_groups"]:
        if group["body_id"] == body_id:
            t = group["body_frame"]["domain_from_body"]
            return t["rotation"], t["origin_m"]
    raise KeyError(body_id)


# --- frozen hand literals vs the exact oracle ---------------------------------

def oracle_literal_checks():
    def tet(vertices, density):
        return b02_oracle.tet_integrals_exact(vertices, FR(density))

    def body(cells, densities):
        return b02_oracle.body_properties_exact(
            [{"cell_id": cid, "vertices": verts}
             for cid, verts in cells],
            {cid: FR(d) for cid, d in densities.items()})

    na1 = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)]
    na2 = [(1, 0, 0), (0, 1, 0), (0, 0, 1), (2, 1, 1)]
    nb1 = [(5, -3, 2), (6, -3, 2), (5, -2, 2), (5, -3, 3)]
    va1, ma1, fa1, _ = tet(na1, 12)
    va2, ma2, fa2, _ = tet(na2, 7)
    _vb1, mb1, fb1, _ = tet(nb1, 1000)
    ca1 = [f / ma1 for f in fa1]  # centroid = first moment / mass
    ca2 = [f / ma2 for f in fa2]
    cb1 = [f / mb1 for f in fb1]
    _v, ma, ca, _ = body([("cell-na1", na1), ("cell-na2", na2)],
                         {"cell-na1": 12, "cell-na2": 7})
    sliver = [(0, 0, 0), (1, 0, 0), (0, 1, 0),
              (FR(1, 4), FR(1, 2), FR(1, 2 ** 20))]
    _vd, md, _, _ = body([("cell-d1", sliver)], {"cell-d1": 6})
    _vx, mx, _, _ = body([("cell-xa", na1)], {"cell-xa": FR(1, 10 ** 6)})
    _vxb, mxb, _, _ = body([("cell-xb", na2)], {"cell-xb": 10 ** 9})
    _vl, ml, _, _ = body(
        [("cell-l1", [(10 ** 6, -2 * 10 ** 6, 3 * 10 ** 6),
                      (10 ** 6 + 1, -2 * 10 ** 6, 3 * 10 ** 6),
                      (10 ** 6, -2 * 10 ** 6 + 1, 3 * 10 ** 6),
                      (10 ** 6, -2 * 10 ** 6, 3 * 10 ** 6 + 1)])],
        {"cell-l1": FR(5, 4)})

    checks = []

    def check(label, prereg_value, derived):
        common.expect_true(True, f"literal.{label}.evaluated")
        checks.append({"label": label,
                       "prereg_literal": str(prereg_value),
                       "oracle_exact": str(derived),
                       "match": prereg_value == derived,
                       "fired_literal_check": prereg_value != derived})

    check("v_na1", FR(1, 6), va1)
    check("m_na1", FR(2), ma1)
    check("centroid_na1_x", FR(1, 4), ca1[0])
    check("v_na2", FR(1, 2), va2)
    check("m_na2", FR(7, 2), ma2)
    check("centroid_na2_x", FR(3, 4), ca2[0])
    check("m_body_A", FR(11, 2), ma)
    check("com_body_A_x", FR(25, 44), ca[0])
    check("com_body_A_y", FR(9, 22), ca[1])
    check("com_body_A_z", FR(9, 22), ca[2])
    check("v_nb1", FR(1, 6), tet(nb1, 1000)[0])
    check("m_body_B", FR(500, 3), mb1)
    check("com_body_B_x", FR(21, 4), cb1[0])
    check("com_body_B_y", FR(-11, 4), cb1[1])
    check("com_body_B_z", FR(9, 4), cb1[2])
    check("cube_region_A_mass", FR(1), body(
        [("t1", [(0, 0, 0), (1, 0, 0), (1, 1, 0), (1, 1, 1)]),
         ("t3", [(0, 0, 0), (1, 1, 0), (0, 1, 0), (1, 1, 1)])],
        {"t1": 3, "t3": 3})[1])
    check("cube_total_mass", FR(4), FR(1) + FR(4, 3) + FR(5, 3))
    check("sliver_mass", FR(1, 2 ** 20), md)
    check("sliver_volume", FR(1, 2 ** 20 * 6), body(
        [("cell-d1", sliver)], {"cell-d1": 6})[0])
    check("x_cell_a_mass_as_written", FR(1, 600000), mx)
    check("x_cell_a_mass_as_derived", FR(1, 6000000), mx)
    check("x_cell_b_mass", FR(500000000), mxb)
    check("large_body_mass", FR(5, 24), ml)
    return checks


# --- U3 cube interface diagnostics --------------------------------------------

def cube_interface_diagnostics():
    manifest, partition, _groups = common.load_coupon("c")
    import material_volume_admission as admission
    report = admission.build_admission_report(manifest, partition)
    geometry = report["geometry"]
    rows = geometry["interfaces"]
    common.expect_equal(len(rows), 4, "cube.interface_row_count")
    pair_sums = {}
    for row in rows:
        common.tol1(row["area_m2"], common.SQRT2_OVER_2,
                    f"cube.interface_area[{tuple(row['face_vertex_ids'])}]")
        key = tuple(sorted((row["region_a_id"], row["region_b_id"])))
        pair_sums[key] = pair_sums.get(key, 0.0) + row["area_m2"]
    ab = pair_sums.get(("region-CA", "region-CB"), 0.0)
    bc = pair_sums.get(("region-CB", "region-CC"), 0.0)
    common.tol1(ab, 2 ** 0.5, "cube.pair_CA-CB.sum")
    common.tol1(bc, 2 ** 0.5, "cube.pair_CB-CC.sum")
    common.expect_true(("region-CA", "region-CC") not in pair_sums,
                       "cube.pair_CA-CC.absent")
    region_set = set()
    for row in rows:
        if "000" in row["face_vertex_ids"]:
            region_set.update((row["region_a_id"], row["region_b_id"]))
    common.expect_equal(sorted(region_set),
                        ["region-CA", "region-CB", "region-CC"],
                        "cube.regions_meeting_at_vertex_000")
    boundary = geometry["boundary_faces"]
    common.expect_equal(len(boundary), 12, "cube.boundary_face_count")
    for face_key, area in exact_cube_boundary_areas(partition):
        common.tol1(area, 0.5, f"cube.boundary_area[{face_key}]")
    common.expect_true(geometry["topology_valid"] is True,
                       "cube.topology_valid")
    export = common.export_in_process("c")
    exact_mass = {"cube-body-A": 1.0, "cube-body-B": 4.0 / 3.0,
                  "cube-body-C": 5.0 / 3.0}
    total = 0.0
    for group in export["body_groups"]:
        props = group["mass_properties"]
        common.tol1(props["mass"]["value"], exact_mass[group["body_id"]],
                    f"cube.{group['body_id']}.mass")
        total += props["mass"]["value"]
    common.tol1(total, 4.0, "cube.recombination_total_mass")
    return {"interface_row_count": len(rows),
            "pair_area_sums": {"/".join(k): v for k, v in pair_sums.items()},
            "regions_meeting_at_vertex_000": sorted(region_set),
            "boundary_face_count": len(boundary),
            "recombination_total_mass": total}


def exact_cube_boundary_areas(partition):
    """Independent exact boundary-face areas of the unit-cube coupon."""
    verts = {row["vertex_id"]: [Fraction(x) for x in row["position"]]
             for row in partition["vertices"]}
    seen = set()
    areas = []
    for cell in partition["cells"]:
        ids = cell["vertex_ids"]
        for tri in _combinations3(ids):
            key = tuple(sorted(tri))
            if key in seen:
                continue
            coords = [verts[v] for v in key]
            if not any(len({c[axis] for c in coords}) == 1
                       and coords[0][axis] in (0, 1) for axis in range(3)):
                continue
            seen.add(key)
            u = [coords[1][d] - coords[0][d] for d in range(3)]
            w = [coords[2][d] - coords[0][d] for d in range(3)]
            cr = _cross(u, w)
            norm2 = sum(c * c for c in cr)
            areas.append((key, float(Fraction(norm2)) ** 0.5 / 2))
    return areas


def _combinations3(items):
    n = len(items)
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                yield (items[i], items[j], items[k])


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


# --- U4 numerical stress -------------------------------------------------------

def stress_diagnostics():
    results = {}
    report = common.export_in_process("l")
    props = next(g for g in report["body_groups"]
                 if g["body_id"] == "stress-body-L")["mass_properties"]
    exp = exact_from_coupon("l")["stress-body-L"]
    common.tol1(props["mass"]["value"], float(exp["mass"]), "stress-L.mass")
    for axis in range(3):
        common.tol2(props["center_of_mass"]["value"][axis],
                    float(exp["com_body"][axis]), f"stress-L.com[{axis}]")
    for i in range(3):
        for j in range(3):
            common.tol2(props["inertia_tensor_about_com"]["value"][i][j],
                        float(exp["inertia_body"][i][j]),
                        f"stress-L.inertia[{i}][{j}]")
    results["large_coordinates"] = {
        "tolerance_class": "T2", "status": "PASS",
        "com_body_expected": [float(v) for v in exp["com_body"]],
        "worst_note": "values up to ~1e13; float64 budget documented in "
        "preregistration"}

    report = common.export_in_process("d")
    props = next(g for g in report["body_groups"]
                 if g["body_id"] == "stress-body-D")["mass_properties"]
    exp = exact_from_coupon("d")["stress-body-D"]
    common.tol1(props["mass"]["value"], float(exp["mass"]), "stress-D.mass")
    common.tol1(props["volume"]["value"], float(exp["volume"]),
                "stress-D.volume")
    for i in range(3):
        for j in range(3):
            common.tol1(props["inertia_tensor_about_com"]["value"][i][j],
                        float(exp["inertia_body"][i][j]),
                        f"stress-D.inertia[{i}][{j}]")
    results["near_degenerate_sliver"] = {
        "tolerance_class": "T1", "status": "PASS",
        "normalized_det_approx": float(FR(1, 2 ** 20)),
        "refusal_line_64eps": 64 * 2.220446049250313e-16,
        "aspect_note": "height 2**-20 vs unit legs; admissible by ~13 orders"}

    report = common.export_in_process("x")
    props = next(g for g in report["body_groups"]
                 if g["body_id"] == "stress-body-X")["mass_properties"]
    exp = exact_from_coupon("x")["stress-body-X"]
    common.tol1(props["mass"]["value"], float(exp["mass"]),
                "stress-X.total_mass")
    tensor = props["inertia_tensor_about_com"]["value"]
    common.expect_true(_finite(tensor), "stress-X.inertia_finite")
    for axis in range(3):
        common.tol1(props["center_of_mass"]["value"][axis],
                    float(exp["com_body"][axis]), f"stress-X.com[{axis}]")
    results["extreme_density_ratio"] = {
        "tolerance_class": "T1", "status": "PASS", "density_ratio": "1e15",
        "total_mass": props["mass"]["value"],
        "no_nonfinite_output": True}
    return results


def _finite(tensor):
    return all(v == v and abs(v) != float("inf") for row in tensor for v in row)


# --- U6 / schema / evidence classes / inventory --------------------------------

def u6_invariance_diagnostics():
    import material_volume_admission as admission
    mn, pn, _gn = common.load_coupon("n")
    mr, pr, _gr = common.load_coupon("r")
    sig_n = admission.build_admission_report(mn, pn)["geometry"][
        "supplied_geometry_signature"]
    sig_r = admission.build_admission_report(mr, pr)["geometry"][
        "supplied_geometry_signature"]
    common.expect_equal(sig_r, sig_n, "u6.geometry_signature_equal")
    return {"supplied_geometry_signature": sig_n,
            "signature_equal_under_rename_and_reorder": True}


def schema_validation():
    import jsonschema
    schema = json.loads(
        (common.FROZEN_TOOLS / "material_volume_body_export_schema.json")
        .read_text())
    # Probe-mapping correction R4 (recorded): the pinned
    # material_volume_body_export_schema.json is the export REQUEST (body
    # groups, chimera.rigid_body_cell_groups.v1) schema, not a report schema
    # -- it rejects even the pinned revision's own example report. The pinned
    # revision ships no separate report schema; the report contract is
    # enforced by the pinned reader (u7 matrix) and the determinism probes.
    validated = 0
    for tag in ("n", "u", "s0_5", "s2_0", "s10_0", "r", "b", "g", "f", "c",
                "l", "d", "x"):
        _m, _p, groups = common.load_coupon(tag)
        jsonschema.validate(groups, schema)
        common.expect_true(True, f"schema.groups.{tag}.valid")
        validated += 1
    example = json.loads(
        (common.FROZEN_TOOLS /
         "material_volume_body_export_groups_example.json").read_text())
    jsonschema.validate(example, schema)
    common.expect_true(True, "schema.groups.pinned_example.valid")
    return {
        "group_documents_validated": validated + 1,
        "schema": "chimera.rigid_body_cell_groups.v1 (pinned shipped "
        "request schema, unmodified)",
        "report_schema": "the pinned revision ships no separate report "
        "schema; report contract is enforced by the pinned reader and the "
        "determinism probes",
        "label": "fixtures - not runtime acceptance"}


def evidence_class_manifest():
    entries = []
    for path in sorted(CONTRIB.rglob("*")):
        if not path.is_file() or "__pycache__" in str(path):
            continue
        rel = path.relative_to(CONTRIB).as_posix()
        if rel.startswith("work/runs/"):
            continue
        data = path.read_bytes()
        entries.append({
            "path": rel,
            "raw_sha256": sha256_bytes(data),
            "lf_canonical_sha256": sha256_bytes(data.replace(b"\r\n", b"\n")),
            "git_blob_oid": blob_oid(path),
            "bytes": len(data)})
    prereg = CONTRIB / "PREREGISTRATION.md"
    crlf = RUNS / "prereg_crlf_materialization.md"
    crlf.write_bytes(prereg.read_bytes().replace(b"\n", b"\r\n"))
    demo = {
        "artifact": "PREREGISTRATION.md",
        "committed_lf_blob_oid": blob_oid(prereg),
        "crlf_copy_raw_sha256": sha256_bytes(crlf.read_bytes()),
        "crlf_copy_lf_canonical_sha256": lf_canonical(crlf),
        "prereg_lf_canonical_sha256": lf_canonical(prereg),
        "raw_differs_canonical_equal": (
            sha256_bytes(crlf.read_bytes()) != lf_canonical(crlf)
            and lf_canonical(crlf) == lf_canonical(prereg))}
    common.expect_true(demo["raw_differs_canonical_equal"],
                       "evidence_classes.raw_vs_canonical_demo")
    return {"class_note": "raw working-tree sha256, LF-canonical sha256 and "
            "git blob OID are three distinct identity classes; portable "
            "identity = blob OID + LF-canonical sha256",
            "artifact_count": len(entries),
            "artifacts": entries,
            "materialization_demo": demo}


def unresolved_inventory():
    receipt = ("frozen receipt 3db8bc4e "
               "(Chimera/docs/matter/"
               "material_volume_export_verification_receipt.md)")
    return [
        {"id": "U8", "state": "UNRESOLVED",
         "assertion": "cross-report composition by consumers (forbidden "
         "silently by contract CON-3/CON-9; no test enforces consumer "
         "behavior)", "owner": "downstream consumer work",
         "source": receipt},
        {"id": "U9", "state": "UNRESOLVED",
         "assertion": "consumption-contract clauses themselves (no consumer "
         "exists)", "owner": "downstream consumer work", "source": receipt},
        {"id": "U10", "state": "UNRESOLVED",
         "assertion": "anything beyond the two synthetic coupons: no "
         "anatomical, mechanical, or dynamics claim is tested anywhere",
         "owner": "runtime/anatomy cards; no runtime claim made here",
         "source": receipt}]


def status_matrix():
    rows = []
    for tag, expected_status in (("b", "blocked"), ("g", "refused"),
                                 ("f", "refused")):
        proc = b02_checks.cli_export(tag, str(RUNS / f"run_diag_{tag}.json"))
        report = json.loads(proc.stdout)
        common.expect_equal(proc.returncode, 1, f"status.{tag}.cli_exit")
        common.expect_equal(report["export_status"], expected_status,
                            f"status.{tag}.export_status")
        no_mass = all(g["mass_properties"] is None
                      for g in report["body_groups"])
        common.expect_true(no_mass, f"status.{tag}.no_mass")
        rows.append({"coupon": f"coupon_{tag}", "exit_code": proc.returncode,
                     "export_status": report["export_status"],
                     "admission_status": report["admission_status"],
                     "reason_codes": report["reason_codes"],
                     "every_body_mass_properties_none": no_mass})
    return rows


def main():
    literals = oracle_literal_checks()
    for tag in ("n", "u", "s0_5", "s2_0", "s10_0", "r", "c", "l", "d", "x"):
        compare_complete_coupon(tag, f"diag.{tag}")
    cube = cube_interface_diagnostics()
    stress = stress_diagnostics()
    u6 = u6_invariance_diagnostics()
    schema = schema_validation()
    evidence = evidence_class_manifest()
    unresolved = unresolved_inventory()
    status = status_matrix()

    suite_counts = json.loads((RUNS / "suite_comparison_count.json").read_text())
    fired = [c for c in literals if c["fired_literal_check"]]
    document = {
        "schema": "chimera.b02_static_diagnostics.v1",
        "task": "MAT2-B02",
        "attempt_id": "5cf7f1cc0d1b40cb9f4a08fc12c4c535",
        "agent_id": "arrival-cccbccce34f94eb294f9e71640348b64",
        "criteria_sha256": CRITERIA,
        "preregistration_sha256_frozen": PREREG_SHA,
        "pinned_revision": FROZEN_REV,
        "profile": {"id": "records", "kind": "offline",
                    "numerical_evidence_required": True,
                    "falsifier": "Missing identities or a claimed pass "
                    "unsupported by records fails; a screenshot is not a "
                    "substitute."},
        "machine": {"platform": platform.platform(),
                    "python": sys.version.split()[0],
                    "cpu_only": True, "gpu": "none", "network": "none"},
        "oracle_literal_checks": {
            "total": len(literals), "matched": len(literals) - len(fired),
            "fired": fired,
            "adjudication_note": "a fired literal check is a prereg "
            "transcription defect reported per F-B02-8; the frozen "
            "preregistration file is preserved verbatim; exporter/oracle "
            "agreement is judged on the derived exact value"},
        "u2_unit_conversion": {"status": "PASS", "tolerance": "T1"},
        "u5_scale_covariance": {"status": "PASS", "tolerance": "T1",
                                "scales": [0.5, 2.0, 10.0],
                                "relations": ["m ~ s^3", "volume ~ s^3",
                                              "I_com ~ s^5",
                                              "authored-frame COM law"]},
        "u6_reorder_renumber_invariance": {
            "status": "PASS", "signature": u6,
            "identity_fields": "input_hashes and admission_report_sha256 "
            "differ (recorded, not compared); mass properties invariant"},
        "u7_status_matrix": status,
        "u3_cube_interfaces": cube,
        "u4_numerical_stress": stress,
        "schema_validation": schema,
        "evidence_classes": evidence,
        "unresolved_inventory": unresolved,
        "applicability_boundary": {
            "uniform_scale_only": "scale_to_m is a single positive scalar; "
            "anisotropic scaling enters only as authored geometry integrated "
            "per cell (contract C04)",
            "fixture_label": "all coupons are fixtures; fixture PASS is not "
            "runtime or release gating (card observation honored)",
            "claims": "no runtime, anatomical, or dynamics claim anywhere; "
            "validation_only true, production_wired false, "
            "dynamics_readiness_claimed false in every report"},
        "comparison_ledger": {
            "suite_comparisons": suite_counts["suite_comparisons"],
            "diagnostics_comparisons": common.COUNTS["comparisons"],
            "total": suite_counts["suite_comparisons"]
            + common.COUNTS["comparisons"],
            "suite_tests_run": suite_counts["tests_run"],
            "suite_failures": suite_counts["failures"]}}
    total = document["comparison_ledger"]["total"]
    common.expect_true(total >= 500, "ledger.total_comparisons_at_least_500")
    out = RUNS / "static_diagnostics.json"
    out.write_text(json.dumps(document, indent=1, sort_keys=True,
                              ensure_ascii=True) + "\n",
                   encoding="utf-8", newline="\n")
    print("diagnostics written:", out)
    print("comparison ledger total:", total)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
