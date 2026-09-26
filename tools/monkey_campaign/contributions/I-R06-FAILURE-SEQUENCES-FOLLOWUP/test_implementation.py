"""test_implementation.py -- I-R06-FAILURE-SEQUENCES-FOLLOWUP entry tests.

The adapter verifies identity, reproduces the clean 8/8 run + suite, proves
injected-counterexample detection, and refuses a tampered runner copy.
"""
import pathlib
import shutil
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import implementation as impl  # noqa: E402


class RegressionEntryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = impl.run_entry()

    def test_all_ok(self):
        self.assertTrue(self.result["all_ok"], self.result)

    def test_identity_verified_before_invocation(self):
        ident = self.result["identity"]
        self.assertEqual(ident["runner_sha256"], impl.RUNNER_SHA256)
        self.assertEqual(ident["suite_sha256"], impl.SUITE_SHA256)

    def test_clean_run_reproduces(self):
        clean = self.result["clean_run"]
        self.assertEqual(clean["exit"], 0)
        self.assertTrue(clean["all_eight"])

    def test_suite_passes(self):
        self.assertTrue(self.result["suite_run"]["ok"])

    def test_injected_counterexample_detected(self):
        det = self.result["counterexample_detection"]
        self.assertTrue(det["detected"])
        self.assertEqual(det["payload"]["control"], "LatchingMapper")
        self.assertFalse(det["payload"]["passed"])
        self.assertTrue(any(str(v).startswith("zombie")
                            for v in det["payload"]["violations"]))

    def test_no_device_claim(self):
        self.assertFalse(self.result["device_testing_claimed"])

    def test_tampered_runner_refused(self):
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="i_r06_tamper_"))
        try:
            for name in (impl.RUNNER, impl.SUITE):
                shutil.copy2(impl.RUNNER_DIR / name, tmp / name)
            (tmp / "reference").mkdir()
            shutil.copy2(impl.RUNNER_DIR / "reference" /
                         "EXTRACTION_LEDGER.json", tmp / "reference")
            text = (tmp / impl.RUNNER).read_text(encoding="utf-8")
            (tmp / impl.RUNNER).write_text(text + "# tampered\n",
                                           encoding="utf-8")
            with self.assertRaises(impl.IdentityFailure):
                impl.verify_identity(tmp)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
