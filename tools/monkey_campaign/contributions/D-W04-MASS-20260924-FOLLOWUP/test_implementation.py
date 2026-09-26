"""Tests for the walking body/manifest consistency validator.

Run:  python -B -m unittest test_implementation -v   (from this directory)

Real-source tests use the read-only play repo at PLAY_REPO with the pins the
winning D-W04-MASS-20260924 diagnostic cited; they are skipped automatically
if that repo is absent. Fixture tests build throwaway git repos in the system
temp dir (removed afterwards; nothing is written to any real source tree).

Fixtures are SYNTHETIC REGISTRATIONS, clearly labeled; no output of this suite
is native acceptance. Each validator invocation is bounded (timeout 110 s);
the whole suite is CPU-only and stdlib-only.
"""
import json
import math
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
IMPL = HERE / "implementation.py"

PLAY_REPO = pathlib.Path("E:/ChimeraWork/monkey-play-20260924")
ACC_PIN = "8294053b"           # first_skill prestage lane tip (acceptance.py blob 3df32b59…)
ABSENT_PIN = "43b599a7c1f11e789cd414b40d7305b9be05066d"  # acceptance.py not yet present
TRN_PIN = "a62b286e"           # typeb tip (walker chain)
SCN_PIN = "33e7a444"           # scene numbers / builder (10.038 kg)

EXPECTED_DEN_KG = 13824.5      # frozen membrane inventory literal (acceptance.py:18)
EXPECTED_TRAIN_KG = 10.038     # Oku-2021 assembly (derived_numbers.json:11)
EXPECTED_RATIO = EXPECTED_DEN_KG / EXPECTED_TRAIN_KG  # 1377.216577007372

ACCEPTANCE_REL = "tools/science_funnel/first_skill/acceptance.py"
MANIFEST_REL = "tools/science_funnel/validation/first_skill_prestage_20260922/run_manifest.json"
RUNBOOK_REL = "tools/science_funnel/validation/first_skill_prestage_20260922/RUNBOOK.md"
WALKER_REL = "tools/science_funnel/typeb_gpu/walker_model.py"
LABEL_REL = "tools/report_first_skill_checkpoint.py"
SCN_REL = "tools/science_funnel/validation/gait_controller_20260918/derived_numbers.json"


def run_validator(argv, timeout=110):
    proc = subprocess.run([sys.executable, "-B", str(IMPL), *argv],
                          capture_output=True, timeout=timeout)
    return {"exit": proc.returncode,
            "stdout": proc.stdout.decode("utf-8", errors="replace"),
            "stderr": proc.stderr.decode("utf-8", errors="replace")}


def base_args(repo, out, acc=ACC_PIN, trn=TRN_PIN, scn=SCN_PIN, extra=()):
    return ["--source-repo", str(repo),
            "--acceptance-commit", acc, "--trainer-commit", trn,
            "--scene-numbers-commit", scn, "--out", str(out), *extra]


def git(repo, *argv):
    proc = subprocess.run(["git", "-C", str(repo), *argv], capture_output=True)
    assert proc.returncode == 0, proc.stderr.decode("utf-8", errors="replace")
    return proc.stdout.decode("utf-8", errors="replace")


def make_fixture_repo(den_literal, train_kg="10.038", weight_n="98.439",
                      with_denominator_line=True):
    """A throwaway git repo holding a minimal, structurally faithful registration.

    Everything is synthetic and labeled 'fixture'; this is NOT a real
    registration and NOT native acceptance.
    """
    root = pathlib.Path(tempfile.mkdtemp(prefix="d_w04_fixture_"))
    for rel in (ACCEPTANCE_REL, MANIFEST_REL, RUNBOOK_REL, WALKER_REL, LABEL_REL, SCN_REL):
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
    denom = ("M_BODY_KG = %s       # fixture: synthetic registration denominator\n"
             % den_literal) if with_denominator_line else ""
    (root / ACCEPTANCE_REL).write_text(
        "# fixture synthetic registration (D-W04-MASS-20260924-FOLLOWUP test)\n"
        + denom +
        "EPISODE_CAP_TICKS = 300\n"
        "INF = float('inf')\n"
        "def episode_bars(record, reached, fell):\n"
        "    dist = float(record.get('distance_m', 0.0))\n"
        "    work = float(record.get('work_J', 0.0))\n"
        "    cot = work / (M_BODY_KG * dist) if dist > 0.0 else INF\n"
        "    return {'cot': cot}\n", encoding="utf-8")
    (root / MANIFEST_REL).write_text(json.dumps({
        "fixture": True,
        "hard_conditions": {"cot_within_band": {"definition":
            "CoT = E_episode / (m_body * d_reached); m_body = %s kg (fixture)" % den_literal}}}),
        encoding="utf-8")
    (root / RUNBOOK_REL).write_text(
        "# fixture runbook\nstep 5: CoT = E_ledger/(%s kg x d_reached).\n" % den_literal,
        encoding="utf-8")
    (root / WALKER_REL).write_text(
        "# fixture walker model\n        self.body_mass[i] = float(b[\"mass_kg\"])\n",
        encoding="utf-8")
    (root / LABEL_REL).write_text(
        "# fixture checkpoint report\nLABEL = \"work_J/(%s kg x distance)\"\n" % den_literal,
        encoding="utf-8")
    (root / SCN_REL).write_text(json.dumps({
        "fixture": True,
        "body_model": {"mass_kg": float(train_kg), "weight_N": float(weight_n)}}),
        encoding="utf-8")
    git(root, "init", "-q")
    git(root, "config", "user.email", "fixture@example.invalid")
    git(root, "config", "user.name", "fixture")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "fixture registration den=%s train=%s" % (den_literal, train_kg))
    return root


class ValidatorRealSourceTests(unittest.TestCase):
    """The actual resolved binding on the pinned play repo."""

    @classmethod
    def setUpClass(cls):
        if not PLAY_REPO.is_dir():
            raise unittest.SkipTest("play repo not present: %s" % PLAY_REPO)
        cls.tmp = pathlib.Path(tempfile.mkdtemp(prefix="d_w04_real_"))
        cls.out = cls.tmp / "out"

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_actual_binding_incompatible_with_exact_ratio(self):
        res = run_validator(base_args(PLAY_REPO, self.out))
        self.assertEqual(res["exit"], 1, res)
        self.assertIn("VERDICT: INCOMPATIBLE", res["stdout"])
        data = json.loads((self.out / "validation_result.json").read_text(encoding="utf-8"))
        self.assertEqual(data["verdict"], "INCOMPATIBLE")
        self.assertEqual(data["denominator_mass_kg"], EXPECTED_DEN_KG)
        self.assertEqual(data["training_body_mass_kg"], EXPECTED_TRAIN_KG)
        self.assertTrue(math.isclose(data["ratio_dimensionless"], EXPECTED_RATIO,
                                     rel_tol=1e-12),
                        data["ratio_dimensionless"])
        check = next(c for c in data["checks"]
                     if c["check"] == "denominator_equals_training_mass")
        self.assertFalse(check["ok"])

    def test_units_explicit_in_output(self):
        data = json.loads((self.out / "validation_result.json").read_text(encoding="utf-8"))
        self.assertEqual(data["units"]["denominator_mass"], "kg")
        self.assertEqual(data["units"]["training_body_mass"], "kg")
        self.assertEqual(data["units"]["weight"], "N")
        self.assertEqual(data["units"]["ratio"], "dimensionless")
        self.assertTrue(math.isclose(data["weight_newton"], EXPECTED_TRAIN_KG * 9.80665,
                                     rel_tol=1e-12))
        self.assertEqual(data["provenance"]["acceptance.py"]["blob_id"],
                         "3df32b59b09411721913229c8df4eb3efa04379e")
        self.assertEqual(data["provenance"]["derived_numbers.json"]["blob_id"],
                         "8b6d75fbd408a8e1e2db31cdf15fc4a104b9a36a")

    def test_frozen_sites_agree_on_current_literal(self):
        data = json.loads((self.out / "validation_result.json").read_text(encoding="utf-8"))
        for name in ("manifest_definition_consistent", "runbook_definition_consistent",
                     "report_label_consistent", "denominator_used_in_cot_expression",
                     "trainer_structural_binding", "weight_consistency"):
            c = next(c for c in data["checks"] if c["check"] == name)
            self.assertTrue(c["ok"], (name, c["detail"]))


class ValidatorRefusalTests(unittest.TestCase):
    """Unresolved lineage must refuse (exit 3, named), never emit a verdict."""

    @classmethod
    def setUpClass(cls):
        if not PLAY_REPO.is_dir():
            raise unittest.SkipTest("play repo not present: %s" % PLAY_REPO)
        cls.tmp = pathlib.Path(tempfile.mkdtemp(prefix="d_w04_refusal_"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _out(self, name):
        return self.tmp / ("out_" + name)

    def test_refusal_missing_repo(self):
        res = run_validator(base_args(self.tmp / "no_such_repo", self._out("a")))
        self.assertEqual(res["exit"], 3, res)
        self.assertIn("SOURCE_REPO_MISSING", res["stderr"])

    def test_refusal_unresolvable_pin(self):
        res = run_validator(base_args(PLAY_REPO, self._out("b"),
                                      acc="0" * 40))
        self.assertEqual(res["exit"], 3, res)
        self.assertIn("PIN_UNRESOLVABLE", res["stderr"])

    def test_refusal_path_not_in_pin(self):
        res = run_validator(base_args(PLAY_REPO, self._out("c"), acc=ABSENT_PIN))
        self.assertEqual(res["exit"], 3, res)
        self.assertIn("PATH_NOT_IN_PIN", res["stderr"])
        self.assertIn("acceptance.py", res["stderr"])

    def test_refusal_blob_anchor_mismatch(self):
        res = run_validator(base_args(PLAY_REPO, self._out("d"),
                                      extra=["--expect-acceptance-blob", "0" * 40]))
        self.assertEqual(res["exit"], 3, res)
        self.assertIn("BLOB_ANCHOR_MISMATCH", res["stderr"])

    def test_refusal_writes_no_output_file(self):
        out = self._out("e")
        res = run_validator(base_args(PLAY_REPO, out, acc=ABSENT_PIN))
        self.assertEqual(res["exit"], 3)
        self.assertFalse((out / "validation_result.json").is_file(),
                         "a refusal must not write an output file")


class ValidatorFixtureTests(unittest.TestCase):
    """Synthetic registrations (clearly labeled fixtures, never native acceptance)."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = pathlib.Path(tempfile.mkdtemp(prefix="d_w04_fx_"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_corrected_fixture_is_compatible(self):
        root = make_fixture_repo("10.038")
        try:
            out = self.tmp / "out_ok"
            anchors = ["--expect-acceptance-blob",
                       git(root, "rev-parse", "HEAD:" + ACCEPTANCE_REL).strip(),
                       "--expect-scene-numbers-blob",
                       git(root, "rev-parse", "HEAD:" + SCN_REL).strip()]
            res = run_validator(base_args(root, out, acc="HEAD", trn="HEAD", scn="HEAD",
                                          extra=anchors))
            self.assertEqual(res["exit"], 0, res)
            self.assertIn("VERDICT: COMPATIBLE", res["stdout"])
            data = json.loads((out / "validation_result.json").read_text(encoding="utf-8"))
            self.assertEqual(data["verdict"], "COMPATIBLE")
            self.assertEqual(data["denominator_mass_kg"], 10.038)
            self.assertEqual(data["training_body_mass_kg"], 10.038)
            self.assertEqual(data["ratio_dimensionless"], 1.0)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_mismatched_lineage_incompatible_named_ratio(self):
        root = make_fixture_repo("6.15")  # the k-fill book mass, NOT the walker mass
        try:
            out = self.tmp / "out_mis"
            res = run_validator(base_args(root, out, acc="HEAD", trn="HEAD", scn="HEAD"))
            self.assertEqual(res["exit"], 1, res)
            data = json.loads((out / "validation_result.json").read_text(encoding="utf-8"))
            self.assertEqual(data["verdict"], "INCOMPATIBLE")
            self.assertTrue(math.isclose(data["ratio_dimensionless"], 6.15 / 10.038,
                                         rel_tol=1e-12))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_refusal_unparseable_denominator(self):
        root = make_fixture_repo("10.038", with_denominator_line=False)
        try:
            out = self.tmp / "out_unp"
            res = run_validator(base_args(root, out, acc="HEAD", trn="HEAD", scn="HEAD"))
            self.assertEqual(res["exit"], 3, res)
            self.assertIn("UNPARSEABLE_DENOMINATOR", res["stderr"])
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_validator_is_readonly_against_sources(self):
        root = make_fixture_repo("10.038")
        try:
            head_before = git(root, "rev-parse", "HEAD").strip()
            status_before = git(root, "status", "--porcelain")
            out = self.tmp / "out_ro"
            run_validator(base_args(root, out, acc="HEAD", trn="HEAD", scn="HEAD"))
            self.assertEqual(git(root, "rev-parse", "HEAD").strip(), head_before)
            self.assertEqual(git(root, "status", "--porcelain"), status_before)
            self.assertEqual(status_before, "")
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
