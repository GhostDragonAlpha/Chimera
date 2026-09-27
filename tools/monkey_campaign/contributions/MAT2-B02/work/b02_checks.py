"""MAT2-B02 verification suite — scale/transform/status tests at pinned bytes.

Run: python -B work/b02_checks.py
(frozen probes: PREREGISTRATION.md; 11 tests, negative control included)
"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

WORK = Path(__file__).resolve().parent
sys.path.insert(0, str(WORK))
sys.path.insert(0, str(WORK / "oracle"))

import b02_common as common  # noqa: E402
import b02_oracle  # noqa: E402

RUNS = common.RUNS
RUNS.mkdir(exist_ok=True)
FROZEN = common.FROZEN_TOOLS
PY = [sys.executable, "-B"]


def cli_export(tag, out_path, manifest=None, partition=None, groups=None):
    manifest = manifest or f"{common.COUPONS / ('coupon_' + tag + '_manifest.json')}"
    partition = partition or f"{common.COUPONS / ('coupon_' + tag + '_partition.json')}"
    groups = groups or f"{common.COUPONS / ('coupon_' + tag + '_groups.json')}"
    proc = subprocess.run(
        PY + [str(FROZEN / "material_volume_body_export.py"),
              "--manifest", manifest, "--partition", partition,
              "--groups", groups],
        capture_output=True, text=True)
    Path(out_path).write_text(proc.stdout, encoding="utf-8", newline="")
    return proc


def cli_reader(report_path, out_path):
    proc = subprocess.run(
        PY + [str(FROZEN / "material_volume_body_export_reader.py"),
              str(report_path)], capture_output=True, text=True)
    Path(out_path).write_text(proc.stdout + proc.stderr, encoding="utf-8",
                              newline="")
    return proc


# --- frozen exact expectations ----------------------------------------------

FR = b02_oracle.Fraction


def n_expectations():
    """Exact oracle expectations for coupon N (and U, physically identical)."""
    frame_a = ([[0, -1, 0], [1, 0, 0], [0, 0, 1]], (0, 0, 0))
    frame_b = ([[1, 0, 0], [0, 1, 0], [0, 0, 1]], (5, -3, 2))
    cells_a = [
        {"cell_id": "cell-na1",
         "vertices": [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)]},
        {"cell_id": "cell-na2",
         "vertices": [(1, 0, 0), (0, 1, 0), (0, 0, 1), (2, 1, 1)]},
    ]
    cells_b = [
        {"cell_id": "cell-nb1",
         "vertices": [(5, -3, 2), (6, -3, 2), (5, -2, 2), (5, -3, 3)]},
    ]
    rho_a = {"cell-na1": FR(12), "cell-na2": FR(7)}
    rho_b = {"cell-nb1": FR(1000)}
    exp_a = common.exact_body_expectations(cells_a, rho_a, frame_a)
    exp_b = common.exact_body_expectations(cells_b, rho_b, frame_b)
    return {"coupon-body-A": exp_a, "coupon-body-B": exp_b}


EXP_N = n_expectations()


def _frame_of(body_id):
    _m, _p, groups = common.load_coupon("n")
    for group in groups["body_groups"]:
        if group["body_id"] == body_id:
            transform = group["body_frame"]["domain_from_body"]
            return (transform["rotation"], transform["origin_m"])
    raise KeyError(body_id)


def expect_body_vs_oracle(report, prefix=""):
    for bid, exp in EXP_N.items():
        group = next(g for g in report["body_groups"] if g["body_id"] == bid)
        props = group["mass_properties"]
        common.tol1(props["mass"]["value"], exp["mass"], f"{prefix}{bid}.mass")
        common.tol1(props["volume"]["value"], exp["volume"],
                    f"{prefix}{bid}.volume")
        for axis in range(3):
            common.tol1(props["center_of_mass"]["value"][axis],
                        exp["com_body"][axis],
                        f"{prefix}{bid}.com_body[{axis}]")
        for i in range(3):
            for j in range(3):
                common.tol1(props["inertia_tensor_about_com"]["value"][i][j],
                            exp["inertia_body"][i][j],
                            f"{prefix}{bid}.inertia[{i}][{j}]")


# --- the frozen 11 tests ------------------------------------------------------

class B02ScaleTransformStatusChecks(unittest.TestCase):
    def test_01_u2_unit_conversion_equivalence(self):
        """P-U2: cm-authored coupon (scale_to_m 0.01) == physical coupon N."""
        report_n = common.export_in_process("n")
        report_u = common.export_in_process("u")
        common.expect_equal(report_u["export_status"], "complete",
                            "u.export_status")
        common.expect_equal(report_n["export_status"], "complete",
                            "n.export_status")
        expect_body_vs_oracle(report_n, prefix="n.")
        expect_body_vs_oracle(report_u, prefix="u.")

    def test_02_u5_scale_covariance_sweep(self):
        """P-U5: m s^3, volume s^3, I s^5, COM frame law for s in {0.5,2,10}."""
        report_1 = common.export_in_process("n")
        base = {g["body_id"]: g["mass_properties"] for g in
                report_1["body_groups"]}
        frames = {g["body_id"]: g["body_frame"] for g in
                  report_1["body_groups"]}
        for tag, s in (("s0_5", 0.5), ("s2_0", 2.0), ("s10_0", 10.0)):
            report_s = common.export_in_process(tag)
            common.expect_equal(report_s["export_status"], "complete",
                                f"{tag}.export_status")
            s3 = s ** 3
            s5 = s ** 5
            for group in report_s["body_groups"]:
                bid = group["body_id"]
                props = group["mass_properties"]
                ref = base[bid]
                common.tol1_rel(props["mass"]["value"],
                                ref["mass"]["value"] * s3,
                                f"{tag}.{bid}.mass_s3")
                common.tol1_rel(props["volume"]["value"],
                                ref["volume"]["value"] * s3,
                                f"{tag}.{bid}.volume_s3")
                for i in range(3):
                    for j in range(3):
                        common.tol1_rel(
                            props["inertia_tensor_about_com"]["value"][i][j],
                            ref["inertia_tensor_about_com"]["value"][i][j] * s5,
                            f"{tag}.{bid}.inertia_s5[{i}][{j}]")
                # COM frame law: com_body(s) = R^T (s*com_domain - origin)
                # with the authored origin fixed (not scaled). Exact oracle
                # com_domain supplies c(1); rotation/origin come from the
                # frozen authored frame of each body.
                exp = EXP_N[bid]
                rotation, origin = _frame_of(bid)
                for axis in range(3):
                    expected = sum(
                        rotation[d][axis] * (s * float(exp["com_domain"][d])
                                             - origin[d])
                        for d in range(3))
                    common.tol1(props["center_of_mass"]["value"][axis],
                                expected,
                                f"{tag}.{bid}.com_frame_law[{axis}]")
                common.expect_equal(
                    props["mass"]["unit"], "kg", f"{tag}.{bid}.mass_unit")
                common.expect_true(
                    props["mass"]["frame_invariant"] is True
                    and props["volume"]["frame_invariant"] is True,
                    f"{tag}.{bid}.frame_invariant_flags")

    def test_03_u2s_invalid_scale_statuses(self):
        """P-U2S: scale 0 / negative / missing -> blocked + refused + exit 1."""
        manifest, partition, groups = common.load_coupon("n")
        for label, mutate in (
                ("zero", lambda frame: frame.update(scale_to_m=0.0)),
                ("negative", lambda frame: frame.update(scale_to_m=-1.0)),
                ("missing", lambda frame: frame.pop("scale_to_m"))):
            m = copy.deepcopy(manifest)
            p = copy.deepcopy(partition)
            mutate(m["coordinate_frame"])
            mpath = RUNS / f"coupon_badscale_{label}_manifest.json"
            ppath = RUNS / f"coupon_badscale_{label}_partition.json"
            mpath.write_text(json.dumps(m, indent=1, sort_keys=True) + "\n")
            ppath.write_text(json.dumps(p, indent=1, sort_keys=True) + "\n")
            reason = {"zero": "bad_scale", "negative": "bad_scale",
                      "missing": "bad_schema"}[label]
            proc = cli_export("n", str(RUNS / f"run_badscale_{label}.json"),
                              manifest=str(mpath), partition=str(ppath))
            common.expect_equal(proc.returncode, 1,
                                f"badscale_{label}.cli_exit")
            report = json.loads(proc.stdout)
            common.expect_equal(report["export_status"], "blocked",
                                f"badscale_{label}.export_status")
            common.expect_equal(report["admission_status"], "refused",
                                f"badscale_{label}.admission_status")
            common.expect_true(reason in report["admission_reason_codes"],
                               f"badscale_{label}.reason[{reason}]")
            for group in report["body_groups"]:
                common.expect_true(group["mass_properties"] is None,
                                   f"badscale_{label}.{group['body_id']}.no_mass")

    def test_04_u6_reorder_renumber_invariance(self):
        """P-U6: coupon R is coupon N under rename/reorder; physics invariant."""
        report_n = common.export_in_process("n")
        report_r = common.export_in_process("r")
        common.expect_equal(report_r["export_status"], "complete",
                            "r.export_status")
        common.expect_equal(report_r["export_status"], report_n["export_status"],
                            "r-vs-n.export_status_equal")
        common.expect_equal(report_r["reason_codes"], report_n["reason_codes"],
                            "r-vs-n.reason_codes_equal")
        common.expect_equal(report_r["unassigned_cell_ids"],
                            report_n["unassigned_cell_ids"],
                            "r-vs-n.unassigned_equal")
        # mass properties: R vs N within T1
        n_props = {g["body_id"]: g["mass_properties"] for g in
                   report_n["body_groups"]}
        for group in report_r["body_groups"]:
            props = group["mass_properties"]
            ref = n_props[group["body_id"]]
            common.tol1(props["mass"]["value"], ref["mass"]["value"],
                        f"r-vs-n.{group['body_id']}.mass")
            for i in range(3):
                for j in range(3):
                    common.tol1(props["inertia_tensor_about_com"]["value"][i][j],
                                ref["inertia_tensor_about_com"]["value"][i][j],
                                f"r-vs-n.{group['body_id']}.inertia[{i}][{j}]")
        # geometry signature exactly equal (renumber-invariant signature),
        # straight from the pinned admission module on both partitions
        if str(FROZEN) not in sys.path:
            sys.path.insert(0, str(FROZEN))
        import material_volume_admission as admission
        mn, pn, _gn = common.load_coupon("n")
        mr, pr, _gr = common.load_coupon("r")
        sig_n = admission.build_admission_report(mn, pn)["geometry"][
            "supplied_geometry_signature"]
        sig_r = admission.build_admission_report(mr, pr)["geometry"][
            "supplied_geometry_signature"]
        common.expect_equal(sig_r, sig_n, "r-vs-n.geometry_signature_equal")
        # input hashes DIFFER (canonical JSON preserves array order)
        common.expect_true(
            report_r["input_hashes"]["partition_sha256"]
            != report_n["input_hashes"]["partition_sha256"],
            "r-vs-n.partition_hash_differs")
        common.expect_true(
            report_r["input_hashes"]["body_groups_sha256"]
            != report_n["input_hashes"]["body_groups_sha256"],
            "r-vs-n.groups_hash_differs")
        common.expect_true(
            report_r["input_hashes"]["manifest_sha256"]
            != report_n["input_hashes"]["manifest_sha256"],
            "r-vs-n.manifest_hash_differs")
        common.expect_true(
            report_r["admission_report_sha256"]
            != report_n["admission_report_sha256"],
            "r-vs-n.admission_report_hash_differs")
        # the two CLI report bytes are NOT byte-identical (identity fields)
        proc_n = cli_export("n", str(RUNS / "run_n.json"))
        proc_r = cli_export("r", str(RUNS / "run_r.json"))
        common.expect_equal(proc_n.returncode, 0, "n.cli_exit")
        common.expect_equal(proc_r.returncode, 0, "r.cli_exit")
        common.expect_true(
            (RUNS / "run_n.json").read_bytes()
            != (RUNS / "run_r.json").read_bytes(),
            "r-vs-n.report_bytes_differ")

    def test_05_u7_blocked_report_and_reader(self):
        """P-U7(a): missing density -> blocked; pinned reader accepts, exit 0."""
        report = common.export_in_process("b")
        common.expect_equal(report["export_status"], "blocked",
                            "b.export_status")
        common.expect_equal(report["admission_status"], "not_admitted",
                            "b.admission_status")
        by_body = {g["body_id"]: g for g in report["body_groups"]}
        common.expect_true(by_body["coupon-body-A"]["mass_properties"] is None,
                           "b.body-A.no_mass")
        common.expect_true(by_body["coupon-body-B"]["mass_properties"] is None,
                           "b.body-B.no_mass")
        common.expect_equal(
            by_body["coupon-body-A"]["blocking_assignment_statuses"],
            [{"cell_id": "cell-na2", "status": "missing_density"}],
            "b.body-A.blocking_rows")
        common.expect_equal(by_body["coupon-body-B"]["blocking_cell_ids"], [],
                            "b.body-B.no_blocking_rows")
        proc = cli_export("b", str(RUNS / "run_blocked.json"))
        common.expect_equal(proc.returncode, 1, "b.cli_exit")
        reader = cli_reader(RUNS / "run_blocked.json", RUNS / "reader_blocked.json")
        common.expect_equal(reader.returncode, 0, "b.reader_exit")
        summary = json.loads(reader.stdout)
        common.expect_equal(summary["export_status"], "blocked",
                            "b.reader_status")
        common.expect_equal(len(summary["bodies"]), 2, "b.reader_body_count")
        for body in summary["bodies"]:
            common.expect_true(body["mass_properties"] is None,
                               f"b.reader.{body['body_id']}.no_mass")

    def test_06_u7_refused_unknown_group_cell_reader(self):
        """P-U7(b): unknown group cell -> refused, exit 1; reader exit 0."""
        proc = cli_export("g", str(RUNS / "run_refused_ghost.json"))
        common.expect_equal(proc.returncode, 1, "g.cli_exit")
        report = json.loads(proc.stdout)
        common.expect_equal(report["export_status"], "refused",
                            "g.export_status")
        common.expect_equal(report["reason_codes"], ["unknown_group_cell_id"],
                            "g.reason_codes")
        reader = cli_reader(RUNS / "run_refused_ghost.json",
                            RUNS / "reader_refused_ghost.json")
        common.expect_equal(reader.returncode, 0, "g.reader_exit")
        common.expect_equal(json.loads(reader.stdout)["export_status"],
                            "refused", "g.reader_status")

    def test_07_u7_refused_bad_frame_reader(self):
        """P-U7(c): non-orthonormal frame -> refused; admission not evaluated."""
        proc = cli_export("f", str(RUNS / "run_refused_frame.json"))
        common.expect_equal(proc.returncode, 1, "f.cli_exit")
        report = json.loads(proc.stdout)
        common.expect_equal(report["export_status"], "refused",
                            "f.export_status")
        common.expect_equal(report["reason_codes"], ["invalid_authored_frame"],
                            "f.reason_codes")
        common.expect_equal(report["admission_status"], "not_evaluated",
                            "f.admission_not_evaluated")
        reader = cli_reader(RUNS / "run_refused_frame.json",
                            RUNS / "reader_refused_frame.json")
        common.expect_equal(reader.returncode, 0, "f.reader_exit")
        common.expect_equal(json.loads(reader.stdout)["export_status"],
                            "refused", "f.reader_status")

    def test_08_u7_reader_tamper_control(self):
        """P-U7(d): non-exported group carrying mass -> reader exit 2."""
        report = common.export_in_process("b")
        report["body_groups"][0]["mass_properties"] = {
            "mass": {"value": 1.0, "unit": "kg", "coordinate_frame": "x",
                     "frame_invariant": True},
            "volume": {"value": 1.0, "unit": "m^3", "coordinate_frame": "x",
                       "frame_invariant": True},
            "center_of_mass": {"value": [0.0, 0.0, 0.0], "unit": "m",
                               "coordinate_frame": "x"},
            "inertia_tensor_about_com": {
                "value": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                "unit": "kg*m^2", "coordinate_frame": "x", "frame_id": "x",
                "basis": "authored_body_frame",
                "full_symmetric_tensor": True,
                "off_diagonal_terms_preserved": True,
                "principal_axis_transform_applied": False}}
        tampered = RUNS / "tampered_blocked_report.json"
        tampered.write_text(json.dumps(report, sort_keys=True) + "\n")
        reader = cli_reader(tampered, RUNS / "reader_tampered.json")
        common.expect_equal(reader.returncode, 2, "tamper.reader_exit")
        common.expect_true("blocked_group_has_mass" in reader.stderr,
                           "tamper.reason_named")

    def test_09_u7_reader_bad_status_control(self):
        """P-U7(e): unknown export_status -> reader exit 2 bad_export_status."""
        report = common.export_in_process("n")
        report["export_status"] = "exploded"
        bad = RUNS / "bad_status_report.json"
        bad.write_text(json.dumps(report, sort_keys=True) + "\n")
        reader = cli_reader(bad, RUNS / "reader_bad_status.json")
        common.expect_equal(reader.returncode, 2, "badstatus.reader_exit")
        common.expect_true("bad_export_status" in reader.stderr,
                           "badstatus.reason_named")

    def test_10_negative_control_perturbed_expectation_must_fire(self):
        """P-NC: +1e-6 relative perturbation of an oracle mass must be
        REJECTED by this comparator; a PASS here voids every verdict."""
        exp = EXP_N["coupon-body-A"]["mass"]
        perturbed = float(exp) * (1.0 + 1e-6)
        fired = False
        try:
            common.tol1(perturbed, exp, "negative-control.body-A.mass")
        except AssertionError:
            fired = True
        common.expect_true(fired, "negative-control.fired")

    def test_11_determinism_two_runs_byte_identical(self):
        """P-DET: two exporter CLI runs on coupon C are byte-identical."""
        first = cli_export("c", str(RUNS / "run_c_1.json"))
        second = cli_export("c", str(RUNS / "run_c_2.json"))
        common.expect_equal(first.returncode, 0, "c.run1_exit")
        common.expect_equal(second.returncode, 0, "c.run2_exit")
        common.expect_equal((RUNS / "run_c_1.json").read_bytes(),
                            (RUNS / "run_c_2.json").read_bytes(),
                            "c.runs_byte_identical")


def main():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules["__main__"])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    (RUNS / "suite_comparison_count.json").write_text(
        json.dumps({"suite_comparisons": common.COUNTS["comparisons"],
                    "tests_run": result.testsRun,
                    "failures": len(result.failures),
                    "errors": len(result.errors)}, indent=1, sort_keys=True)
        + "\n", encoding="utf-8", newline="\n")
    print(f"comparison ledger: {common.COUNTS['comparisons']} fields asserted")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
