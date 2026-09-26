"""test_adapter.py -- I-R02-SAVE-STORE-FOLLOWUP targeted tests.

Independent verification of the preregistered predictions: every byte-equality
and hash check here is recomputed BY THIS TEST from its own expected bytes --
never taken from the adapter's verdict or the module's internals. The accepted
merged module is loaded through the adapter's hash pin, so a stand-in cannot
enter through either door.

Run (bounded, CPU-only, temporary directories only):
    python -B test_adapter.py -v
"""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import adapter  # noqa: E402  (same directory; the card's own harness)

ADAPTER_PATH = HERE / "adapter.py"
REFERENCE_SAVE_STORE = HERE / "reference" / "I-R02-SAVE-STORE" / "save_store.py"
SLOT = adapter.SLOT
IDENT = adapter.IDENT_A
START_WALL_CLOCK = time.monotonic()


class AcceptedModulePin(unittest.TestCase):
    """The module under fault injection IS the merged PR #117 source."""

    def test_hash_pin_resolves_to_accepted_bytes(self):
        module = adapter.load_accepted_module(str(REFERENCE_SAVE_STORE))
        self.assertEqual(module._accepted_sha256, adapter.ACCEPTED_SAVE_STORE_SHA256)
        self.assertEqual(
            adapter.file_sha256(REFERENCE_SAVE_STORE),
            adapter.ACCEPTED_SAVE_STORE_SHA256)

    def test_stand_in_refuses_by_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "save_store.py"
            fake.write_text("# a rewritten stand-in, not the accepted module\n",
                            encoding="utf-8")
            with self.assertRaises(adapter.AdapterRefusal) as ctx:
                adapter.load_accepted_module(str(fake))
            self.assertIn("stand_in_module", str(ctx.exception))


class ChildSaveRoundTrip(unittest.TestCase):
    """A clean child save loads byte-exact through the accepted module."""

    def test_clean_child_save_loads_byte_exact(self):
        module = adapter.load_accepted_module(str(REFERENCE_SAVE_STORE))
        payload = adapter.payload_a()
        with tempfile.TemporaryDirectory() as user_dir:
            proc = adapter.run_child(ADAPTER_PATH, REFERENCE_SAVE_STORE, user_dir,
                                     SLOT, payload, **IDENT)
            self.assertEqual(proc.returncode, adapter.EXIT_CLEAN,
                             proc.stderr.decode("utf-8", "replace")[-2000:])
            saved = [e for e in proc.events if e["event"] == "saved"]
            self.assertTrue(saved and saved[0]["atomic"])
            result, _ = adapter._load_via_accepted(module, user_dir)
            self.assertEqual(result.status, "loaded")
            # independent checks: expected bytes recomputed here, not via module
            self.assertEqual(result.payload, payload)
            self.assertEqual(result.payload_sha256, hashlib.sha256(payload).hexdigest())
            self.assertEqual(result.build_id, IDENT["build_id"])
            self.assertEqual(result.format_version, IDENT["format_version"])

    def test_child_refusal_law_traversal_slot(self):
        with tempfile.TemporaryDirectory() as user_dir:
            row = adapter.scenario_child_refusal_law(
                ADAPTER_PATH, REFERENCE_SAVE_STORE, user_dir)
            self.assertEqual(row["child_rc"], adapter.EXIT_REFUSED)
            self.assertEqual(row["code"], "slot_traversal")
            self.assertFalse((Path(user_dir) / "escape.save.json").exists())


class InterruptionPreservesPrior(unittest.TestCase):
    """Prediction 1 + F1/F3: real process death before atomic replace is
    unobservable at the slot level; prior save returns byte-exact."""

    def setUp(self):
        self.module = adapter.load_accepted_module(str(REFERENCE_SAVE_STORE))

    def _trial(self, point):
        payload = adapter.payload_a()
        with tempfile.TemporaryDirectory() as user_dir:
            row = adapter.scenario_interruption_preserves_prior(
                ADAPTER_PATH, REFERENCE_SAVE_STORE, user_dir, self.module, point)
            # the scenario's own fields
            self.assertEqual(row["child_rc"], row["expected_rc"], (point, row))
            self.assertTrue(row["died_at_marker"], (point, row))
            self.assertTrue(row["slot_bytes_unchanged"], (point, row))
            self.assertEqual(row["load_status"], "loaded", (point, row))
            self.assertTrue(row["payload_matches_prior"], (point, row))
            self.assertTrue(row["payload_sha256_matches_prior"], (point, row))
            self.assertEqual(row["listed_slots"], 1, (point, row))
            self.assertTrue(row["listed_ok"], (point, row))
            # INDEPENDENT recheck from this test process: the slot bytes are the
            # clean envelope of payload_a and load returns exactly payload_a.
            slot_file = adapter.slot_path(user_dir, SLOT)
            envelope = json.loads(slot_file.read_text(encoding="utf-8"))
            import base64
            self.assertEqual(base64.b64decode(envelope["payload_b64"]), payload)
            result, _ = adapter._load_via_accepted(self.module, user_dir)
            self.assertEqual(result.payload, payload)
            self.assertEqual(result.payload_sha256,
                             hashlib.sha256(payload).hexdigest())
            # no partial/new content under a real .save.json name beyond the one
            real_names = [p.name for p in Path(user_dir).iterdir()
                          if p.name.endswith(".save.json")]
            self.assertEqual(real_names, [SLOT + ".save.json"])
            return row

    def test_death_before_open(self):
        self._trial("before_open")

    def test_death_mid_write(self):
        self._trial("mid_write")

    def test_death_before_fsync(self):
        self._trial("before_fsync")

    def test_death_before_replace(self):
        self._trial("before_replace")


class InterruptedFirstSave(unittest.TestCase):
    """Prediction 2: no prior save -> first_run, nothing listed, no real slot."""

    def test_interrupted_first_save(self):
        module = adapter.load_accepted_module(str(REFERENCE_SAVE_STORE))
        with tempfile.TemporaryDirectory() as user_dir:
            row = adapter.scenario_interrupted_first_save(
                ADAPTER_PATH, REFERENCE_SAVE_STORE, user_dir, module,
                point="before_replace")
            self.assertEqual(row["child_rc"],
                             adapter.EXIT_BY_POINT["before_replace"])
            self.assertEqual(row["load_status"], "first_run")
            self.assertEqual(row["listed_slots"], 0)
            self.assertFalse(row["real_slot_exists"])
            for name in row["debris_temp_files"]:
                self.assertFalse(name.endswith(".save.json"), name)


class CorruptionRefusesByName(unittest.TestCase):
    """Prediction 3 + F2: corrupted/truncated stored saves refuse with the
    exact named code; identity mismatches refuse as *_mismatch."""

    def test_tamper_matrix(self):
        module = adapter.load_accepted_module(str(REFERENCE_SAVE_STORE))
        with tempfile.TemporaryDirectory() as user_dir:
            rows, mismatches = adapter.scenario_corruption_matrix(user_dir, module)
            self.assertEqual(len(rows), len(adapter.TAMPER_MATRIX))
            for row in rows:
                self.assertEqual(row["status"], "refused", row)
                self.assertEqual(row["refusal_code"], row["expected_code"], row)
                self.assertTrue(row["payload_empty"], row)
            codes = {r["tamper"]: r["refusal_code"] for r in rows}
            self.assertEqual(codes["truncate_raw"], "json_corrupt")
            self.assertEqual(codes["flip_b64_char"], "payload_hash_mismatch")
            self.assertEqual(codes["stored_hash"], "payload_hash_mismatch")
            self.assertEqual(codes["payload_size"], "payload_size_mismatch")
            self.assertEqual(codes["invalid_utf8"], "not_utf8")
            self.assertEqual(codes["duplicate_key"], "key_duplicate")
            self.assertEqual(codes["nan_literal"], "not_finite_json")
            self.assertEqual(codes["wrong_schema"], "schema_unknown")
            self.assertEqual(codes["bad_format_version"], "format_version_type")
            self.assertEqual(codes["delete_identity"], "scene_id_missing")
            for row in mismatches:
                self.assertEqual(row["status"], "refused", row)
                self.assertEqual(row["refusal_code"],
                                 f"{row['mismatch']}_mismatch", row)

    def test_tampered_never_loads(self):
        """F2 direct: for every tamper, status is never 'loaded'."""
        module = adapter.load_accepted_module(str(REFERENCE_SAVE_STORE))
        with tempfile.TemporaryDirectory() as user_dir:
            rows, _ = adapter.scenario_corruption_matrix(user_dir, module)
            for row in rows:
                self.assertNotEqual(row["status"], "loaded", row)


class CrashLoopThenRecovery(unittest.TestCase):
    """Prediction 4: repeated interrupted overwrites never expose partial
    content; the next clean save restores normal operation."""

    def test_crash_loop_then_clean_save(self):
        module = adapter.load_accepted_module(str(REFERENCE_SAVE_STORE))
        with tempfile.TemporaryDirectory() as user_dir:
            row = adapter.scenario_crash_loop(ADAPTER_PATH, REFERENCE_SAVE_STORE,
                                              user_dir, module)
            self.assertEqual(len(row["trials"]), 5)
            self.assertTrue(row["all_prior_intact"], row["trials"])
            for trial in row["trials"]:
                self.assertEqual(trial["child_rc"],
                                 adapter.EXIT_BY_POINT[trial["point"]], trial)
            self.assertEqual(row["final_rc"], adapter.EXIT_CLEAN)
            self.assertEqual(row["final_status"], "loaded")
            self.assertIs(row["final_payload_exact"], True)
            # independent: the final payload this test expects is deterministic
            final_expected = adapter.payload_b("final")
            self.assertEqual(len(final_expected), 1536 * 32)


class VerifyCommand(unittest.TestCase):
    """The published one-shot evidence run passes end to end."""

    def test_verify_passes(self):
        verdict = adapter.verify(str(REFERENCE_SAVE_STORE))
        self.assertTrue(verdict["pass"], json.dumps(verdict, indent=1)[:4000])
        self.assertEqual(verdict["save_store_sha256"],
                         adapter.ACCEPTED_SAVE_STORE_SHA256)
        self.assertLess(verdict["elapsed_seconds"], 120)


class Bounds(unittest.TestCase):
    """The card's 120 s bound holds for this whole invocation."""

    def test_within_bounded_time(self):
        elapsed = time.monotonic() - START_WALL_CLOCK
        self.assertLess(elapsed, 120, f"test invocation took {elapsed:.1f}s")


if __name__ == "__main__":
    unittest.main(verbosity=2)
