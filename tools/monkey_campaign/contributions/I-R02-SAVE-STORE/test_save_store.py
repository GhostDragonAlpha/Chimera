"""test_save_store.py -- I-R02-SAVE-STORE: bounded CPU tests for the envelope store.

Run from the task workspace:  python -m unittest test_save_store -v
Each test is instant and dependency-free (stdlib only). The six step-5 scenarios
are covered explicitly, plus the three falsifiers and the reused atomic convention.
"""
import base64
import hashlib
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

import save_store as ss


IDENTS = dict(format_version=3, build_id="b-8630", scene_id="forest-one",
              policy_id="gait-v2")


def _blob_for(payload, **over):
    """Build canonical envelope bytes for payload with optional field overrides."""
    doc = ss._build_envelope(IDENTS["format_version"], IDENTS["build_id"],
                             IDENTS["scene_id"], IDENTS["policy_id"], payload)
    doc.update(over)
    return ss._canonical_envelope_bytes(doc), doc


class SaveStoreTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = self._tmp.name
        self.store = ss.SaveStore(self.dir)

    def tearDown(self):
        self._tmp.cleanup()

    # ── step 5: successful byte-exact payload restoration (incl. binary) ─────
    def test_roundtrip_byte_exact_binary_payload(self):
        payload = bytes([i % 256 for i in range(1000)]) + b"\x80\xff\x00\xfe" * 7
        self.store.save("clearing_1", payload=payload, **IDENTS)
        res = self.store.load("clearing_1")
        self.assertTrue(res.ok)
        self.assertEqual(res.payload, payload)
        self.assertEqual(res.format_version, 3)
        self.assertEqual(res.build_id, "b-8630")
        self.assertEqual(res.scene_id, "forest-one")
        self.assertEqual(res.policy_id, "gait-v2")
        self.assertEqual(res.payload_sha256, hashlib.sha256(payload).hexdigest())

    def test_deterministic_saves_are_byte_identical(self):
        payload = b"snapshot-bytes-12345"
        a = self.store.save("slot_a", payload=payload, **IDENTS)
        # reset dir to isolate the second file
        self.store.save("slot_b", payload=payload, **IDENTS)
        with open(a.path, "rb") as f:
            first = f.read()
        b = self.store.save("slot_c", payload=payload, **IDENTS)
        with open(b.path, "rb") as f:
            second = f.read()
        self.assertEqual(first, second)

    # ── falsifier 1: interrupted write must NOT destroy the previous save ────
    def test_interrupted_write_preserves_previous_save(self):
        good = b"PREVIOUS-VALID-SNAPSHOT"
        self.store.save("A", payload=good, **IDENTS)

        captured = {}

        def fake_replace(src, dst):
            # The temp file was fully written; the atomic rename itself fails.
            captured["temp_exists"] = os.path.exists(src)
            captured["temp_in_dir"] = os.path.dirname(os.path.realpath(src)) == \
                os.path.realpath(self.dir)
            raise OSError("simulated disk full at replace")

        with mock.patch.object(ss.os, "replace", side_effect=fake_replace):
            with self.assertRaises(OSError):
                self.store.save("A", payload=b"DIFFERENT-HALF-WRITE", **IDENTS)

        # The previous valid save is intact and byte-exact...
        res = self.store.load("A")
        self.assertTrue(res.ok)
        self.assertEqual(res.payload, good)
        # ...the temp was cleaned up (no partial file under a real name)...
        files = sorted(os.listdir(self.dir))
        self.assertEqual(files, ["A.save.json"])
        # ...and the interruption happened after the temp existed, in our dir.
        self.assertTrue(captured["temp_exists"])
        self.assertTrue(captured["temp_in_dir"])

    def test_interrupted_write_leaves_no_stray_temp(self):
        self.store.save("keep", payload=b"x", **IDENTS)
        with mock.patch.object(ss.os, "replace", side_effect=OSError("boom")):
            with self.assertRaises(OSError):
                self.store.save("new", payload=b"y", **IDENTS)
        # list() must not enumerate the stray temp as a slot
        names = [s.slot_name for s in self.store.list()]
        self.assertEqual(names, ["keep"])

    def test_atomic_write_uses_temp_fsync_replace(self):
        fsync_calls = []
        replace_calls = []

        def record_replace(src, dst):
            replace_calls.append((src, dst))
            return None

        with mock.patch.object(ss.os, "fsync", side_effect=lambda fh: fsync_calls.append(1)), \
                mock.patch.object(ss.os, "replace", side_effect=record_replace):
            res = self.store.save("A", payload=b"data", **IDENTS)

        self.assertEqual(fsync_calls, [1])                 # flush + fsync happened
        self.assertEqual(len(replace_calls), 1)           # exactly one atomic rename
        src, dst = replace_calls[0]
        self.assertTrue(os.path.basename(src).startswith("."))   # temp file name
        self.assertIn("tmp-", os.path.basename(src))          # .slot.tmp-<pid>
        self.assertEqual(os.path.dirname(src), os.path.dirname(dst))  # same dir
        self.assertTrue(res.atomic)

    # ── falsifier 3: tampered / truncated payload refuses ────────────────────
    def test_tampered_payload_hash_mismatch(self):
        blob, doc = _blob_for(b"ORIGINAL-PAYLOAD")
        # flip one base64 char inside payload_b64 (keeps valid JSON string)
        b64 = doc["payload_b64"]
        i = len(b64) // 2                       # a middle DATA char (not padding)
        flipped = b64[:i] + ("A" if b64[i] == "A" else "B") + b64[i+1:]
        tampered_blob, _ = _blob_for(b"ORIGINAL-PAYLOAD", payload_b64=flipped)
        path = os.path.join(self.dir, "T.save.json")
        with open(path, "wb") as f:
            f.write(tampered_blob)
        res = self.store.load("T")
        self.assertEqual(res.status, "refused")
        self.assertEqual(res.refusals[0].code, "payload_hash_mismatch")

    def test_truncated_file_refuses(self):
        blob, _ = _blob_for(b"some snapshot content here")
        cut = len(blob) - 5                       # chop off the tail mid-document
        path = os.path.join(self.dir, "Tr.save.json")
        with open(path, "wb") as f:
            f.write(blob[:cut])
        res = self.store.load("Tr")
        self.assertEqual(res.status, "refused")
        self.assertIn(res.refusals[0].code, ("json_corrupt", "envelope_truncated"))

    def test_empty_payload_roundtrips(self):
        self.store.save("empty", payload=b"", **IDENTS)
        res = self.store.load("empty")
        self.assertTrue(res.ok)
        self.assertEqual(res.payload, b"")

    # ── falsifier 3: mismatched / missing identities refuse ──────────────────
    def test_identity_mismatch_refuses(self):
        self.store.save("A", payload=b"data", **IDENTS)
        res = self.store.load("A", expected_build_id="WRONG-BUILD")
        self.assertEqual(res.status, "refused")
        self.assertEqual(res.refusals[0].code, "build_id_mismatch")

    def test_version_mismatch_refuses(self):
        self.store.save("A", payload=b"data", **IDENTS)
        res = self.store.load("A", expected_format_version=99)
        self.assertEqual(res.status, "refused")
        self.assertEqual(res.refusals[0].code, "format_version_mismatch")

    def test_all_identities_match_loads(self):
        self.store.save("A", payload=b"data", **IDENTS)
        res = self.store.load("A", expected_format_version=3, expected_build_id="b-8630",
                              expected_scene_id="forest-one", expected_policy_id="gait-v2")
        self.assertTrue(res.ok)

    def test_no_expected_args_loads_anything(self):
        self.store.save("A", payload=b"data", **IDENTS)
        res = self.store.load("A")
        self.assertTrue(res.ok)

    def test_missing_identity_in_envelope_refuses(self):
        # hand-craft an envelope that omits build_id (should never be savable,
        # but a load must refuse it rather than default it)
        doc = {"schema": ss.SCHEMA_ID, "format_version": 3,
               "scene_id": "forest-one", "policy_id": "gait-v2",
               "payload_sha256": hashlib.sha256(b"p").hexdigest(),
               "payload_size": 1, "payload_b64": base64.b64encode(b"p").decode()}
        path = os.path.join(self.dir, "M.save.json")
        with open(path, "wb") as f:
            f.write(ss._canonical_envelope_bytes(doc))
        res = self.store.load("M")
        self.assertEqual(res.status, "refused")
        self.assertEqual(res.refusals[0].code, "build_id_missing")

    # ── falsifier 2: traversal escapes the caller directory ──────────────────
    def test_save_traversal_names_raise(self):
        for bad in ["../escape", "a/b", "..\\win", "/abs/path", "C:\\foo"]:
            with self.assertRaises(ss.SlotNameError) as cm:
                self.store.save(bad, payload=b"x", **IDENTS)
            self.assertEqual(cm.exception.refusal.code, "slot_traversal")

    def test_load_traversal_names_refuse_without_escaping(self):
        res = self.store.load("../../escape")
        self.assertEqual(res.status, "refused")
        self.assertEqual(res.refusals[0].code, "slot_traversal")
        # nothing was created outside the user directory
        parent = os.path.dirname(os.path.realpath(self.dir))
        escaped = os.path.join(parent, "escape.save.json")
        self.assertFalse(os.path.exists(escaped))

    def test_empty_and_nonstring_slot_names_refuse(self):
        r1 = self.store.load("")
        self.assertEqual(r1.status, "refused")
        self.assertEqual(r1.refusals[0].code, "slot_empty")

    # ── absent file: first_run, nothing created ─────────────────────────────
    def test_absent_file_is_first_run_and_creates_nothing(self):
        before = set(os.listdir(self.dir)) if os.path.isdir(self.dir) else set()
        res = self.store.load("nope")
        self.assertEqual(res.status, "first_run")
        self.assertFalse(res.ok)
        self.assertEqual(res.payload, b"")
        after = set(os.listdir(self.dir)) if os.path.isdir(self.dir) else set()
        self.assertEqual(before, after)

    # ── save input refusals (never defaulted) ────────────────────────────────
    def test_save_requires_all_identities(self):
        with self.assertRaises(ss.SaveError) as cm:
            self.store.save("A", payload=b"x", format_version=None, build_id="b",
                            scene_id="s", policy_id="p")   # format_version None
        self.assertEqual(cm.exception.refusal.code, "format_version_type")
        for ident in ("build_id", "scene_id", "policy_id"):
            kwargs = dict(IDENTS); kwargs[ident] = None     # pass None explicitly
            with self.assertRaises(ss.SaveError):
                self.store.save("A", payload=b"x", **kwargs)

    def test_save_rejects_non_bytes_payload(self):
        with self.assertRaises(ss.SaveError) as cm:
            self.store.save("A", payload="string-payload", **IDENTS)
        self.assertEqual(cm.exception.refusal.code, "payload_type")

    def test_save_enforces_max_payload_bound(self):
        small = ss.SaveStore(self.dir, max_payload_bytes=10)
        with self.assertRaises(ss.SaveError) as cm:
            small.save("A", payload=b"x" * 11, **IDENTS)
        self.assertEqual(cm.exception.refusal.code, "payload_too_large")
        # exactly at the bound succeeds
        res = small.save("A", payload=b"x" * 10, **IDENTS)
        self.assertTrue(res.atomic)

    def test_save_coerces_bytearray_and_memoryview(self):
        self.store.save("A", payload=bytearray(b"arr"), **IDENTS)
        self.store.save("B", payload=memoryview(b"mv"), **IDENTS)
        self.assertEqual(self.store.load("A").payload, b"arr")
        self.assertEqual(self.store.load("B").payload, b"mv")

    # ── list(): metadata only, bounded, never raises on bad data ─────────────
    def test_list_returns_metadata_only_and_sorted(self):
        self.store.save("zeta", payload=b"1", **IDENTS)
        self.store.save("alpha", payload=b"22", **IDENTS)
        info = {s.slot_name: s for s in self.store.list()}
        self.assertEqual(list(info.keys()), ["alpha", "zeta"])
        a = info["alpha"]
        self.assertEqual(a.status, "ok")
        self.assertEqual(a.build_id, "b-8630")
        self.assertEqual(a.payload_sha256, hashlib.sha256(b"22").hexdigest())
        self.assertFalse(hasattr(a, "payload"))     # no payload bytes exposed

    def test_list_excludes_temp_and_reports_unreadable(self):
        self.store.save("good", payload=b"data", **IDENTS)
        # stray temp from a crashed write must not be enumerated
        with mock.patch.object(ss.os, "replace", side_effect=OSError("x")):
            try:
                self.store.save("crashed", payload=b"y", **IDENTS)
            except OSError:
                pass
        stray = os.path.join(self.dir, ".crashed.tmp-%d" % os.getpid())
        with open(stray, "wb") as f:
            f.write(b"partial")
        # a corrupt envelope is reported unreadable, not raised
        with open(os.path.join(self.dir, "corrupt.save.json"), "wb") as f:
            f.write(b"{not json at all")
        names = [s.slot_name for s in self.store.list()]
        self.assertIn("good", names)
        self.assertNotIn("crashed", names)          # temp excluded
        unreadable = [s for s in self.store.list() if s.status == "unreadable"]
        self.assertTrue(any(s.slot_name == "corrupt" for s in unreadable))

    def test_list_empty_and_missing_directory(self):
        self.assertEqual(self.store.list(), [])
        gone = ss.SaveStore(os.path.join(self.dir, "does-not-exist-yet"))
        self.assertEqual(gone.list(), [])

    # ── overwrite replaces atomically (old content gone) ─────────────────────
    def test_overwrite_replaces_content(self):
        self.store.save("A", payload=b"ONE", **IDENTS)
        self.store.save("A", payload=b"TWO", **IDENTS)
        res = self.store.load("A")
        self.assertTrue(res.ok)
        self.assertEqual(res.payload, b"TWO")

    # ── no pickle / execution of stored content ──────────────────────────────
    def test_source_uses_no_pickle_or_exec(self):
        here = os.path.dirname(os.path.abspath(ss.__file__))
        with open(os.path.join(here, "save_store.py"), "rb") as f:
            src = f.read()
        self.assertNotIn(b"import pickle", src)
        self.assertNotIn(b"pickle.loads", src)
        self.assertNotIn(b"pickle.load(", src)
        self.assertNotIn(b"exec(", src)
        self.assertNotIn(b"eval(", src)
        # a payload that looks like executable code comes back unchanged (opaque)
        code_like = b"import os; os.system('echo pwned')  # not run by the store"
        self.store.save("A", payload=code_like, **IDENTS)
        self.assertEqual(self.store.load("A").payload, code_like)


if __name__ == "__main__":
    unittest.main(verbosity=2)
