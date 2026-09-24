"""M09 acceptance tests (preregistered in ../preregistration.md, frozen).

Read-only: the shipped tools/ example reports are READ as-is; every other
fixture is a GENUINE exporter output generated in memory by calling the
exporter's public ``build_export_report`` on mutated IN-MEMORY copies of the
shipped example manifest/partition/groups, then written only under
``agents/M09_diagnostic/work/``. No tools/ or docs/ file is ever written.
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True  # never let __pycache__ appear in tools/

MY_DIR = Path(__file__).resolve().parents[1]
WORK_DIR = MY_DIR / "work"
sys.path.insert(0, str(MY_DIR))

import material_volume_diagnostic as diag  # noqa: E402  (sets dont_write_bytecode)

reader, exporter = diag.load_reader(diag.find_tools_dir(None))
TOOLS = diag.find_tools_dir(None)

EXAMPLE_REPORT = TOOLS / "material_volume_body_export_example_report.json"
MANIFEST = TOOLS / "material_volume_body_export_manifest_example.json"
PARTITION = TOOLS / "material_volume_body_export_partition_example.json"
GROUPS = TOOLS / "material_volume_body_export_groups_example.json"

_fixture_cache = {}


def generate_fixtures() -> dict:
    """Genuine exporter outputs from in-memory mutations of shipped examples."""
    if _fixture_cache:
        return _fixture_cache
    manifest = exporter.read_json_file(str(MANIFEST))
    partition = exporter.read_json_file(str(PARTITION))
    groups = exporter.read_json_file(str(GROUPS))

    reports = {}
    reports["complete"] = exporter.build_export_report(manifest, partition, groups)

    groups_partial = copy.deepcopy(groups)
    groups_partial["body_groups"] = [row for row in groups_partial["body_groups"]
                                     if row["body_id"] != "coupon-body-B"]
    reports["partial"] = exporter.build_export_report(manifest, partition, groups_partial)

    partition_blocked = copy.deepcopy(partition)
    partition_blocked["regions"][1]["material_id"] = "tissue-MISSING"
    reports["blocked"] = exporter.build_export_report(manifest, partition_blocked, groups)

    manifest_unsupported = copy.deepcopy(manifest)
    manifest_unsupported["mass_authority"] = "source_effective_segment_mass"
    reports["unsupported"] = exporter.build_export_report(
        manifest_unsupported, partition, groups)

    groups_refused = copy.deepcopy(groups)
    groups_refused["body_groups"][0]["body_id"] = "   "
    reports["refused"] = exporter.build_export_report(manifest, partition, groups_refused)

    expected = {"complete": "complete", "partial": "partial", "blocked": "blocked",
                "unsupported": "unsupported", "refused": "refused"}
    for name, report in reports.items():
        actual = report.get("export_status")
        assert actual == expected[name], (
            f"fixture generator: {name} case produced export_status {actual!r}, "
            f"expected {expected[name]!r}")
    # authenticity: the complete case must reproduce the shipped example report
    shipped = exporter.read_json_file(str(EXAMPLE_REPORT))
    assert reports["complete"] == shipped, (
        "fixture generator: build_export_report on shipped example inputs did not "
        "reproduce the shipped example report")

    WORK_DIR.mkdir(parents=True, exist_ok=True)
    paths = {}
    for name, report in reports.items():
        path = WORK_DIR / f"fixture_{name}.json"
        path.write_text(exporter.canonical_json(report), encoding="utf-8")
        paths[name] = path
    malformed_version = WORK_DIR / "fixture_malformed_version.json"
    malformed_version.write_text(json.dumps({
        "schema_version": "chimera.rigid_body_mass_export.v0",
        "export_status": "complete", "body_groups": []}), encoding="utf-8")
    malformed_key = WORK_DIR / "fixture_malformed_duplicate_key.json"
    malformed_key.write_text(
        '{"schema_version": "chimera.rigid_body_mass_export.v1",'
        ' "export_status": "complete", "export_status": "partial",'
        ' "body_groups": []}\n', encoding="utf-8")
    paths["malformed_version"] = malformed_version
    paths["malformed_duplicate_key"] = malformed_key

    _fixture_cache.update(reports=reports, paths=paths)
    return _fixture_cache


def run_cli(paths, extra_args=()):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run([sys.executable, str(MY_DIR / "material_volume_diagnostic.py"),
                           *[str(p) for p in paths], *extra_args],
                          capture_output=True, text=True, env=env, cwd=str(MY_DIR))


def run_cli_json(paths):
    proc = run_cli(paths, ["--json"])
    assert proc.returncode in (0, 2, 4), f"unexpected CLI exit {proc.returncode}: {proc.stderr}"
    return proc.returncode, json.loads(proc.stdout)


class AcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fx = generate_fixtures()
        cls.paths = cls.fx["paths"]

    # T1 — happy path on the shipped example report
    def test_t1_happy_path_shipped_example(self):
        code, payload = run_cli_json([EXAMPLE_REPORT])
        self.assertEqual(code, 0)
        entry = payload["reports"][0]
        self.assertTrue(entry["ok"])
        self.assertEqual(entry["export_status"], "complete")
        self.assertEqual(entry["schema_version"], exporter.EXPORT_SCHEMA)
        self.assertEqual(len(entry["bodies"]), 2)
        self.assertEqual(entry["omitted_bodies"], [])
        self.assertEqual(entry["unassigned_cell_ids"], [])
        self.assertFalse(any(body["omitted"] for body in entry["bodies"]))
        self.assertEqual(entry["frames"], ["coupon-A-authored", "coupon-B-authored"])
        self.assertEqual(entry["units"], ["kg", "kg*m^2", "m"])
        self.assertFalse(payload["readiness"])

    # T2 — unassigned-cells case (partial)
    def test_t2_partial_unassigned_cells(self):
        code, payload = run_cli_json([self.paths["partial"]])
        self.assertEqual(code, 0)
        entry = payload["reports"][0]
        self.assertEqual(entry["export_status"], "partial")
        self.assertEqual(entry["unassigned_cell_ids"], ["cell-B"])
        rows = entry["unassigned_cells"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(set(rows[0]), {"cell_id", "assignment_status", "reason"})
        self.assertEqual(rows[0]["cell_id"], "cell-B")
        self.assertEqual(rows[0]["reason"], "not_assigned_to_an_authored_body_group")
        self.assertEqual(len(entry["bodies"]), 1)  # only body-A exported
        self.assertEqual(entry["bodies"][0]["body_id"], "coupon-body-A")

    # T3 — omitted bodies case (blocked), incl. U7 summary observation
    def test_t3_blocked_omitted_bodies(self):
        code, payload = run_cli_json([self.paths["blocked"]])
        self.assertEqual(code, 0)
        entry = payload["reports"][0]
        self.assertEqual(entry["export_status"], "blocked")
        omitted = entry["omitted_bodies"]
        self.assertEqual({body["body_id"] for body in omitted},
                         {"coupon-body-A", "coupon-body-B"})
        for body in omitted:
            self.assertEqual(body["export_status"], "not_exported")
            self.assertEqual(body["reason_codes"],
                             ["reconstructed_mass_admission_required"])
            self.assertNotIn("mass_kg", body)  # no mass fields for omitted bodies
        blocking = {body["body_id"]: body["blocking_cell_ids"] for body in omitted}
        # Genuine exporter semantics (observed, locked): with region-B pointing at
        # an unknown material, cell-A stays "resolved" so body-A is omitted by the
        # report-global admission failure with an EMPTY per-body blocking list;
        # only body-B names its blocking cell. Admission failure is report-global;
        # blocking_cell_ids lists only that body's non-resolved cells.
        self.assertEqual(blocking, {"coupon-body-A": [],
                                    "coupon-body-B": ["cell-B"]})
        # U7 observation, locked: the reader SUMMARY drops the blocking detail
        raw = exporter.read_json_file(str(self.paths["blocked"]))
        summary = reader.summarize_export_report(raw)
        for body in summary["bodies"]:
            self.assertNotIn("blocking_cell_ids", body)
            self.assertNotIn("blocking_assignment_statuses", body)

    # T4 — refused case (U7-adjacent), still exit 0: a diagnosed refusal
    def test_t4_refused_status(self):
        code, payload = run_cli_json([self.paths["refused"]])
        self.assertEqual(code, 0)
        entry = payload["reports"][0]
        self.assertTrue(entry["ok"])
        self.assertEqual(entry["export_status"], "refused")
        self.assertEqual(entry["top_level_reason_codes"], ["bad_identifier"])
        self.assertIsInstance(entry.get("detail"), str)
        self.assertTrue(entry["detail"])
        self.assertEqual(entry["bodies"], [])
        self.assertFalse(entry["readiness_claimed"])
        # U7 observation, locked: the reader SUMMARY drops reason_codes/detail
        raw = exporter.read_json_file(str(self.paths["refused"]))
        summary = reader.summarize_export_report(raw)
        self.assertNotIn("reason_codes", summary)
        self.assertNotIn("detail", summary)

    # T5 — unsupported case
    def test_t5_unsupported_status(self):
        code, payload = run_cli_json([self.paths["unsupported"]])
        self.assertEqual(code, 0)
        entry = payload["reports"][0]
        self.assertEqual(entry["export_status"], "unsupported")
        omitted = entry["omitted_bodies"]
        self.assertEqual({body["body_id"] for body in omitted},
                         {"coupon-body-A", "coupon-body-B"})
        for body in omitted:
            self.assertEqual(body["reason_codes"],
                             ["source_effective_segment_mass_unsupported"])
        self.assertFalse(entry["readiness_claimed"])

    # T6 — malformed reports are reader-rejected, CLI ok=false, exit 2
    def test_t6_malformed_reports(self):
        code, payload = run_cli_json([self.paths["malformed_version"],
                                      self.paths["malformed_duplicate_key"]])
        self.assertEqual(code, 2)
        entry_version, entry_key = payload["reports"]
        self.assertFalse(entry_version["ok"])
        self.assertEqual(entry_version["error"]["reason"], "bad_export_report_version")
        self.assertNotIn("export_status", entry_version)
        self.assertFalse(entry_key["ok"])
        self.assertEqual(entry_key["error"]["reason"], "duplicate_json_key")

    # T7 — F2 falsifier: readiness false in every output, human and JSON
    def test_t7_readiness_always_false(self):
        accepted = ["complete", "partial", "blocked", "unsupported", "refused"]
        paths = [EXAMPLE_REPORT] + [self.paths[name] for name in accepted]
        code, payload = run_cli_json(paths)
        self.assertEqual(code, 0)
        self.assertFalse(payload["readiness"])
        for entry in payload["reports"]:
            self.assertIs(entry["readiness_claimed"], False)
        human = run_cli(paths)
        self.assertEqual(human.returncode, 0)
        self.assertIn("readiness_claimed: false", human.stdout)
        self.assertEqual(human.stdout.splitlines()[-1], "readiness: false")

    # T8 — F3 falsifier: no status invention; displayed == raw == summary
    def test_t8_no_status_invention(self):
        for name in ("complete", "partial", "blocked", "unsupported", "refused"):
            path = self.paths[name]
            code, payload = run_cli_json([path])
            self.assertEqual(code, 0)
            entry = payload["reports"][0]
            raw = exporter.read_json_file(str(path))
            summary = reader.summarize_export_report(raw)
            self.assertEqual(entry["export_status"], raw["export_status"])
            self.assertEqual(entry["export_status"], summary["export_status"])
            self.assertIn(entry["export_status"], diag.STATUSES)
            raw_rows = {row["body_id"]: row for row in raw.get("body_groups", [])}
            for body in entry["bodies"]:
                self.assertEqual(body["export_status"],
                                 raw_rows[body["body_id"]]["export_status"])
            for body in entry["omitted_bodies"]:
                self.assertNotEqual(body["export_status"], "exported")
            self.assertEqual(entry["admission_status"],
                             summary["admission_status"] or "not_reported")

    # T9 — F1 falsifier, in-suite portion: no __pycache__ appears in tools/
    def test_t9_no_pycache_in_tools(self):
        pycache = list(TOOLS.rglob("__pycache__"))
        self.assertEqual(pycache, [],
                         f"__pycache__ appeared in tools/: {pycache}")

    # T10 — exit codes incl. refused == 0, malformed == 2
    def test_t10_exit_codes(self):
        self.assertEqual(run_cli([self.paths["complete"]]).returncode, 0)
        self.assertEqual(run_cli([self.paths["partial"]]).returncode, 0)
        self.assertEqual(run_cli([self.paths["blocked"]]).returncode, 0)
        self.assertEqual(run_cli([self.paths["unsupported"]]).returncode, 0)
        self.assertEqual(run_cli([self.paths["refused"]]).returncode, 0)
        self.assertEqual(run_cli([self.paths["malformed_version"]]).returncode, 2)

    # T11 — human output grammar on the blocked case (omission lines, units)
    def test_t11_human_format_blocked(self):
        proc = run_cli([self.paths["blocked"]])
        self.assertEqual(proc.returncode, 0)
        out = proc.stdout
        self.assertIn("export_status: blocked", out)
        self.assertIn("omitted_bodies: 2", out)
        self.assertIn("reason_codes=reconstructed_mass_admission_required", out)
        self.assertIn("blocking_cell_ids=cell-B", out)
        self.assertIn("blocking_assignment_statuses=cell-B:invalid_material_reference", out)
        self.assertIn("unassigned_cell_ids: (none)", out)
        self.assertIn("unassigned_cells: 0", out)
        self.assertIn("frames: (none)", out)  # no exported bodies -> no summary frames
        self.assertIn("units: (none)", out)


if __name__ == "__main__":
    unittest.main()
