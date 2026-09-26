"""test_implementation.py -- I-S04-PLAYER-DIAGNOSTICS-FOLLOWUP adapter tests.

Self-contained at ANY checkout: the seam modules are imported ONLY through
impl.bind(), which materializes the vendored reference/ bytes hash-asserted
(pinned revision 9afbddcd, see reference/EXTRACTION_LEDGER.json) -- no live
play-worktree or parent-reference path is touched. Real pinned product errors
flow through the accepted diagnostics; unknowns keep correlation + scrubbed
paths; loaded/first_run produce nothing; identity tamper refuses.
"""
import json
import pathlib
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
import implementation as impl  # noqa: E402


class AdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bound = impl.bind()
        cls.pd = cls.bound["pd"]

    def test_identity_pin_and_tamper_refusal(self):
        # accepted module bytes still pinned at bind
        real = impl.ACCEPTED_DIR / "player_diagnostics.py"
        self.assertEqual(impl.hashlib.sha256(real.read_bytes()).hexdigest(),
                         impl.ACCEPTED_SHA256)
        # vendored seam materializes with every pin hash asserted
        with tempfile.TemporaryDirectory() as tmp:
            root = impl.materialize_pinned_seam(root=pathlib.Path(tmp) / "m")
            for repo_path, want in impl.SEAM_PINS.items():
                got = impl.hashlib.sha256(
                    (root / repo_path).read_bytes()).hexdigest()
                self.assertEqual(got, want)
        # a drifted pin refuses BY NAME, before any import
        bad_pins = dict(impl.SEAM_PINS)
        first = next(iter(bad_pins))
        bad_pins[first] = "0" * 64
        with self.assertRaises(impl.AdapterIdentityFailure) as ctx:
            impl.materialize_pinned_seam(pins=bad_pins)
        self.assertIn("pinned_source_hash_mismatch", str(ctx.exception))

    def test_real_corrupt_json_known_translation(self):
        iset = self.bound["iset"]  # vendored pinned copy (hash-asserted bind)
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp) / "corrupt.json"
            p.write_bytes(b'{"bindings": [not json')
            result = iset.load_settings(str(p))
        self.assertEqual(result.status, "refused")
        record = impl.translate_load_result(result)
        self.assertIsNotNone(record)
        self.assertEqual(record["status"], "refused")
        self.assertNotEqual(record["status"], "unknown")
        self.assertTrue(record["message"])
        self.assertFalse(record["ok"])

    def test_real_unsupported_action_known_translation(self):
        iset = self.bound["iset"]
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp) / "bad.json"
            defaults = iset.default_settings()
            doc = {"schema": iset.SCHEMA_ID,
                   "bindings": {**defaults.bindings, "P9": "teleport"},
                   "sensitivity": {"yaw": defaults.sensitivity},
                   "invert": {"yaw": defaults.invert_yaw}}
            p.write_text(json.dumps(doc), encoding="utf-8")
            result = iset.load_settings(str(p))
        record = impl.translate_load_result(result)
        self.assertIsNotNone(record)
        self.assertNotEqual(record["status"], "unknown")
        self.assertIn("teleport", json.dumps(record["diagnostic"]))

    def test_real_flow_drop_known_translation(self):
        sf = self.bound["sf"]
        class Mapper:
            def press(self, *a): pass
            def release(self, *a): pass
            def release_all(self, *a): pass
            def mouse(self, *a): pass
            def tick(self, *a): pass
            def held(self): return {}
        flow = sf.SessionFlow(Mapper(), lambda: None, lambda: None)
        flow.key("Up", 1, 100)            # ATTRACT: Up is a no-op -> dropped
        drops = flow.last_trace.get("dropped", [])
        self.assertTrue(drops)
        record = impl.translate_flow_drop(drops[0]["kind"], drops[0]["detail"],
                                          state="attract")
        self.assertNotEqual(record["status"], "unknown")
        self.assertTrue(record["message"])

    def test_future_code_lands_unknown_with_correlation(self):
        record = impl.translate_unknown_name("future_code_2030",
                                             "at C:/Users/x/save.json")
        self.assertEqual(record["status"], "unknown")
        self.assertTrue(record["correlation_id"])

    def test_path_scrubbed_from_message_kept_in_diagnostic(self):
        record = impl.translate_unknown_name("future_code_2030",
                                             "at C:/Users/x/save.json")
        self.assertNotIn("C:/Users", record["message"])
        self.assertIn("save.json", json.dumps(record["diagnostic"]))

    def test_path_bearing_exception_scrubbed(self):
        try:
            raise OSError("cannot read E:/saves/slot1.save.json")
        except OSError as exc:
            record = impl.translate_exception(exc)
        self.assertFalse(record["ok"])
        self.assertNotIn("E:/saves", record["message"])
        self.assertIn("slot1.save.json", json.dumps(record["diagnostic"]))

    def test_loaded_and_first_run_produce_nothing(self):
        self.assertIsNone(impl.translate_load_result(
            type("R", (), {"status": "loaded"})()))
        self.assertIsNone(impl.translate_load_result(
            type("R", (), {"status": "first_run"})()))

    def test_samples_table_written(self):
        samples = impl.sample_table()
        self.assertEqual(len(samples), 4)
        out = HERE / "samples.json"
        if out.is_file():
            loaded = json.loads(out.read_text("utf-8"))
            self.assertEqual(loaded["schema"], impl.SCHEMA)
        for s in samples:
            self.assertTrue(s["player_line"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
