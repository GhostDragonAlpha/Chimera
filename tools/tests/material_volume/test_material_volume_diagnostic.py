"""M09 acceptance tests (preregistered in ../preregistration.md, frozen).

Read-only: the shipped tools/ example reports are READ as-is; every other
fixture is a GENUINE exporter output generated in memory by calling the
exporter's public ``build_export_report`` on mutated IN-MEMORY copies of the
shipped example manifest/partition/groups, then written only under
``tools/tests/material_volume/work/``. No landed tools/ or docs/ file is
ever written.
"""
from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True  # never let __pycache__ appear in tools/

MY_DIR = Path(__file__).resolve().parents[2]  # landed: tools/ (home: the agent dir)
WORK_DIR = Path(__file__).resolve().parents[0] / "work"  # landed: inside this tests dir
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


def generate_hostile_fixtures() -> dict:
    """Reader-ACCEPTED but contract-violating reports (B2a probes P4/P5 class).

    Base is the GENUINE complete exporter report; each mutation touches exactly
    the hostile field. Protocol matches B2a's: the reader's public
    ``summarize_export_report`` must ACCEPT each fixture BEFORE any CLI
    assertion, so every test here exercises the display path on reader-accepted
    input. Files are written only under ``tools/tests/material_volume/work/``.
    """
    generate_fixtures()
    if "hostile" in _fixture_cache:
        return _fixture_cache["hostile"]
    complete = _fixture_cache["reports"]["complete"]

    docs = {}
    doc = copy.deepcopy(complete)          # D3: IDs as a bare string
    doc["unassigned_cell_ids"] = "cell-B"
    docs["string_ids"] = doc
    doc = copy.deepcopy(complete)          # D2: rows as bare strings
    doc["unassigned_cell_ids"] = ["cell-B", "cell-C"]
    doc["unassigned_cells"] = ["cell-B", "cell-C"]
    docs["string_rows"] = doc
    doc = copy.deepcopy(complete)          # G: key absent -> "(not reported)"
    del doc["unassigned_cells"]
    docs["no_unassigned_cells"] = doc
    for name, doc in docs.items():
        summary = reader.summarize_export_report(doc)
        assert summary["export_status"] == "complete", (
            f"hostile fixture {name}: reader did not accept as complete")

    WORK_DIR.mkdir(parents=True, exist_ok=True)
    paths = {}
    for name, doc in docs.items():
        path = WORK_DIR / f"fixture_hostile_{name}.json"
        path.write_text(exporter.canonical_json(doc), encoding="utf-8")
        paths[name] = path
    _fixture_cache["hostile"] = {"docs": docs, "paths": paths}
    return _fixture_cache["hostile"]


def tree_snapshot() -> dict:
    """SHA-256 + st_mtime_ns of every file under tools/ and Chimera/docs/matter.

    Same roots and same shape as run_suite.snapshot — the in-suite form of the
    preregistered T9 hash proof (its second half), applied to whatever CLI
    subprocesses run while a snapshot pair is held.
    """
    worktree = TOOLS.parent
    state = {}
    for root in (worktree / "tools", worktree / "Chimera" / "docs" / "matter"):
        for path in sorted(root.rglob("*")):
            if path.is_file():
                stat = path.stat()
                state[str(path.relative_to(worktree))] = {
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "mtime_ns": stat.st_mtime_ns,
                }
    return state


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
        # G-hashproof (preregistered T9 second half, moved in-suite): the
        # snapshot below straddles EVERY CLI subprocess this class (the whole
        # suite) spawns; tearDownClass asserts tools/ + Chimera/docs/matter
        # byte- and mtime-identical across all of them.
        cls._tree_before = tree_snapshot()

    @classmethod
    def tearDownClass(cls):
        after = tree_snapshot()
        added = sorted(set(after) - set(cls._tree_before))
        removed = sorted(set(cls._tree_before) - set(after))
        changed = sorted(path for path in set(cls._tree_before) & set(after)
                         if cls._tree_before[path] != after[path])
        if added or removed or changed:
            raise cls.failureException(
                "F1: tools/ + Chimera/docs/matter changed during the suite "
                f"(added={added}, removed={removed}, changed={changed})")

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
    # (landed scope: tools/ TOP LEVEL -- every landed material-volume module's
    # bytecode would land there; nested pre-existing __pycache__ dirs of OTHER
    # campaigns are outside the M09/M10 surface. New pycache anywhere under
    # tools/ mid-suite is still caught by the F1 tree snapshot in tearDown.)
    def test_t9_no_pycache_in_tools(self):
        pycache = list(TOOLS.glob("__pycache__"))
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


class B8RegressionTests(unittest.TestCase):
    """B2a-review regressions D1/D2/D3 + coverage gaps (B8 preregistration,
    frozen in ../B8_fixes/preregistration_fixes.md BEFORE any edit).

    The D-tests FAIL on the pre-fix CLI by construction (demonstrated and
    preserved in agents/B8_fixes/receipts/tests_before_fix.log); the gap tests
    pin honest current behavior and must be green both before and after.
    Hostile fixtures are reader-ACCEPTED reports (gated in
    generate_hostile_fixtures), so everything below exercises display-path
    behavior only — never re-validation, never a status invention.
    """

    @classmethod
    def setUpClass(cls):
        cls.fx = generate_fixtures()["paths"]
        cls.hostile = generate_hostile_fixtures()["paths"]

    # D1 — argparse usage errors must NOT collide with frozen exit 2
    # (reader-rejected); frozen contract: usage = "other nonzero". Decision
    # recorded in the B8 preregistration: 64 = BSD sysexits EX_USAGE.
    def test_d1_usage_errors_exit_distinct_from_reader_rejection(self):
        no_args = run_cli([])
        self.assertEqual(no_args.returncode, 64)
        self.assertTrue(no_args.stderr.startswith("usage:"),
                        f"usage text lost: {no_args.stderr!r}")
        bogus = run_cli([EXAMPLE_REPORT, "--bogus-flag"])
        self.assertEqual(bogus.returncode, 64)
        # the frozen reader-rejection code itself must be untouched by the remap
        self.assertEqual(run_cli([self.fx["malformed_version"]]).returncode, 2)

    # D2 — reader-accepted string rows in unassigned_cells must render
    # gracefully in human mode (pre-fix: AttributeError, exit 1 + traceback)
    def test_d2_string_unassigned_cells_rows_render_gracefully(self):
        proc = run_cli([self.hostile["string_rows"]])
        self.assertEqual(proc.returncode, 0)
        self.assertNotIn("Traceback", proc.stderr)
        self.assertIn("unassigned_cells: 2", proc.stdout)
        self.assertIn("<non-object row: 'cell-B'>", proc.stdout)
        self.assertIn("<non-object row: 'cell-C'>", proc.stdout)
        self.assertEqual(proc.stdout.splitlines()[-1], "readiness: false")
        code, payload = run_cli_json([self.hostile["string_rows"]])
        self.assertEqual(code, 0)
        self.assertEqual(payload["reports"][0]["unassigned_cells"],
                         ["cell-B", "cell-C"])  # JSON passthrough unchanged

    # D3 — a string unassigned_cell_ids renders WHOLE (pre-fix: per-character
    # mangle "c, e, l, l, -, B"; the class M09 locked for a sibling field)
    def test_d3_string_unassigned_cell_ids_not_mangled(self):
        proc = run_cli([self.hostile["string_ids"]])
        self.assertEqual(proc.returncode, 0)
        self.assertIn("unassigned_cell_ids: cell-B", proc.stdout)
        self.assertNotIn("c, e, l, l", proc.stdout)
        code, payload = run_cli_json([self.hostile["string_ids"]])
        self.assertEqual(code, 0)
        self.assertEqual(payload["reports"][0]["unassigned_cell_ids"], "cell-B")

    # G-exit4 — the readiness-alarm path (unreachable with the real reader, by
    # its construction): force a lying summary via the reader's public seam.
    def test_exit4_readiness_alarm_path(self):
        real = reader.summarize_export_report

        def lying(document):
            summary = dict(real(document))
            summary["dynamics_readiness_claimed"] = True
            return summary

        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch.object(reader, "summarize_export_report", lying):
            with contextlib.redirect_stdout(stdout), \
                    contextlib.redirect_stderr(stderr):
                code = diag.main([str(self.fx["complete"]), "--json"])
        self.assertEqual(code, 4)
        self.assertIn("READINESS-VIOLATION", stderr.getvalue())
        payload = json.loads(stdout.getvalue())
        self.assertIs(payload["readiness"], False)  # F2 sentinel stays false
        human_out, human_err = io.StringIO(), io.StringIO()
        with mock.patch.object(reader, "summarize_export_report", lying):
            with contextlib.redirect_stdout(human_out), \
                    contextlib.redirect_stderr(human_err):
                code = diag.main([str(self.fx["complete"])])
        self.assertEqual(code, 4)
        self.assertIn("READINESS-VIOLATION", human_err.getvalue())
        self.assertEqual(human_out.getvalue().splitlines()[-1], "readiness: false")

    # G-mixed — accepted + rejected in ONE invocation: exit 2, argv order,
    # rejected entry carries no summary fields
    def test_mixed_accepted_and_rejected_invocation(self):
        code, payload = run_cli_json(
            [self.fx["complete"], self.fx["malformed_version"]])
        self.assertEqual(code, 2)
        accepted, rejected = payload["reports"]
        self.assertEqual(accepted["path"], str(self.fx["complete"]))
        self.assertTrue(accepted["ok"])
        self.assertEqual(accepted["export_status"], "complete")
        self.assertEqual(rejected["path"], str(self.fx["malformed_version"]))
        self.assertFalse(rejected["ok"])
        self.assertEqual(rejected["error"]["reason"], "bad_export_report_version")
        for field in ("export_status", "schema_version", "input_hashes",
                      "bodies", "readiness_claimed"):
            self.assertNotIn(field, rejected)  # never invented (frozen contract)
        human = run_cli([self.fx["complete"], self.fx["malformed_version"]])
        self.assertEqual(human.returncode, 2)
        self.assertIn("export_status: complete", human.stdout)
        self.assertIn("error_reason: bad_export_report_version", human.stdout)
        self.assertEqual(human.stdout.splitlines()[-1], "readiness: false")

    # G-notreported — the third grammar token, untested per B2a (G1)
    def test_unassigned_cells_not_reported_token(self):
        proc = run_cli([self.hostile["no_unassigned_cells"]])
        self.assertEqual(proc.returncode, 0)
        self.assertIn("unassigned_cells: (not reported)", proc.stdout)
        self.assertEqual(proc.stdout.splitlines()[-1], "readiness: false")
        code, payload = run_cli_json([self.hostile["no_unassigned_cells"]])
        self.assertEqual(code, 0)
        self.assertNotIn("unassigned_cells", payload["reports"][0])


if __name__ == "__main__":
    unittest.main()
