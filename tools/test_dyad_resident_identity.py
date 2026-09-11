"""test_dyad_resident_identity.py -- preregistered CPU falsifiers for the DYAD's
reported RESIDENT identity (task dyad-resident-identity-01, generation 5).

PREREGISTRATION: docs/evidence/dyad_resident_identity/PREREGISTRATION.md
(committed BEFORE any run of this suite).

STATEMENT: resident_model() reports identity only from explicit loaded-state
metadata in /api/v0/models (state == "loaded" or status == "loaded"); an
on-disk id is never reported resident. Inference served identity stays
response-derived and is never written by the metadata read.

All transports are synthetic: urllib.request.urlopen is monkeypatched inside
each test. No network, no model load, no eviction, no GPU, no inference.

TWO RUN MODES
  canonical  (default)          : tests the installed ChimeraEngine.senses.
  base counterexample (retained): set CHIMERA_RESIDENT_IDENTITY_SENSES_MODULE to
    a senses module file (the evidence snapshot base_senses_accd15b6.py, the
    verbatim `git show accd15b6:ChimeraEngine/senses.py`) and the SAME cases run
    against the exact base code. Preregistration predicts cases 2 (on-disk-only)
    and 4 (multiple-loaded) FAIL there -- that failing run is the retained
    original counterexample, never deleted or weakened.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "ChimeraEngine"
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MODELS_PATH = "/api/v0/models"


def _load_senses():
    """The senses module under test: env-var override (base snapshot) or the
    installed ChimeraEngine.senses."""
    override = os.environ.get("CHIMERA_RESIDENT_IDENTITY_SENSES_MODULE")
    if override:
        path = Path(override)
        if str(path.parent) not in sys.path:
            sys.path.insert(0, str(path.parent))  # so the module's `import dyad_log` resolves
        spec = importlib.util.spec_from_file_location("base_senses_under_test", path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["base_senses_under_test"] = mod
        spec.loader.exec_module(mod)
        return mod, f"base-snapshot:{path.name}"
    import senses  # installed worktree module
    return senses, "installed:ChimeraEngine/senses.py"


class _Response:
    """Synthetic urlopen result: a JSON body served over a with-block."""

    def __init__(self, payload):
        self._data = json.dumps(payload).encode("utf-8")
        self.status = 200

    def read(self):
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class _RawResponse(_Response):
    """A body that is NOT valid JSON (malformed transport payload)."""

    def __init__(self, raw=b"not-json{"):
        self._data = raw
        self.status = 200


class ResidentIdentityContract(unittest.TestCase):
    """The six preregistered cases plus the no-side-effect laws."""

    senses: object
    source: str

    @classmethod
    def setUpClass(cls):
        cls.senses, cls.source = _load_senses()

    def setUp(self):
        # Hygiene only: the identity reader must not depend on or mutate these.
        for attr in ("_SERVED", "_FINISH"):
            if hasattr(self.senses, attr):
                setattr(self.senses, attr, None)

    def run_resident(self, responder):
        """Call resident_model() once under full synthetic instrumentation.

        Enforces the SIDE-EFFECT LAWS on every call:
          - the only network surface is a body-less (GET) /api/v0/models
            metadata read -- never inference, never a load/evict command;
          - a strict eye_control stand-in is in place and is never driven
            (no load/unload/evict/pick), so nothing can evict an
            operator-loaded model;
          - served identity stays response-derived: the metadata read never
            writes a served-identity record (_SERVED/_FINISH stay None).
        Returns (result, calls).
        """
        calls = []

        def fake_urlopen(url, timeout=None):
            calls.append({"url": url, "timeout": timeout,
                          "data": getattr(url, "data", None),
                          "method": getattr(url, "method", None)})
            return responder(url, timeout)

        eye = mock.Mock(name="eye_control")  # any accidental use is recorded
        with mock.patch.object(self.senses.urllib.request, "urlopen",
                               side_effect=fake_urlopen), \
                mock.patch.dict(sys.modules, {"eye_control": eye}):
            result = self.senses.resident_model()

        self.assertGreater(len(calls), 0)
        for c in calls:
            self.assertTrue(str(c["url"]).endswith(MODELS_PATH),
                            f"non-metadata surface touched: {c['url']}")
            self.assertIsNone(c["data"], f"request carried a body (not a GET read): {c}")
        for drive in ("load", "unload", "evict", "pick", "chat_completions"):
            getattr(eye, drive).assert_not_called()
        self.assertIsNone(getattr(self.senses, "_SERVED", None))
        self.assertIsNone(getattr(self.senses, "_FINISH", None))
        return result, calls

    # -- the six preregistered cases ---------------------------------------

    def test_case1_no_model_returns_none(self):
        result, _ = self.run_resident(lambda url, timeout: _Response({"data": []}))
        self.assertIsNone(result)

    def test_case2_on_disk_only_returns_none_never_on_disk_id(self):
        """THE ORIGINAL COUNTEREXAMPLE: every listed model is on-disk
        (not-loaded); reporting any listed id as resident falsifies the
        statement. Preregistered to FAIL against the base accd15b6 snapshot."""
        records = [{"id": "on-disk-model", "state": "not-loaded"},
                   {"id": "other-on-disk-model"}]
        result, _ = self.run_resident(lambda url, timeout: _Response({"data": records}))
        self.assertIsNone(
            result, "an on-disk id was reported resident (falsifier)")

    def test_case3_single_loaded_returns_that_id(self):
        for records in (
            [{"id": "resident-a", "state": "loaded"}],
            # the loaded record need not be listed first
            [{"id": "on-disk-model", "state": "not-loaded"},
             {"id": "resident-a", "state": "loaded"}],
            # status field is the other explicit loaded marker
            [{"id": "resident-a", "status": "loaded"}],
        ):
            with self.subTest(records=records):
                result, _ = self.run_resident(
                    lambda url, timeout, r=records: _Response({"data": r}))
                self.assertEqual(result, "resident-a")

    def test_case4_multiple_loaded_returns_none_not_first(self):
        """Named ambiguity: with several explicitly loaded records the answer is
        None -- never an arbitrary first selection. Preregistered to FAIL
        against the base accd15b6 snapshot (hidden model selection)."""
        for records in (
            [{"id": "resident-a", "state": "loaded"},
             {"id": "resident-b", "state": "loaded"}],
            [{"id": "resident-a", "status": "loaded"},
             {"id": "resident-b", "status": "loaded"}],
        ):
            with self.subTest(records=records):
                result, _ = self.run_resident(
                    lambda url, timeout, r=records: _Response({"data": r}))
                self.assertIsNone(
                    result, "a hidden first-selection was reported (falsifier)")

    def test_case5_malformed_payload_returns_none_no_escape(self):
        payloads = ([],                        # payload not an object
                    {"data": "garbage"},       # data not a list
                    {"data": {"id": "x"}},     # data not a list
                    {})                        # data missing
        for payload in payloads:
            with self.subTest(payload=payload):
                result, _ = self.run_resident(
                    lambda url, timeout, p=payload: _Response(p))
                self.assertIsNone(result)

    def test_case6_transport_failure_returns_none(self):
        failures = (urllib.error.URLError("connection refused"),
                    OSError("socket closed"),
                    _RawResponse())          # unreadable/malformed body
        for failure in failures:
            with self.subTest(failure=repr(failure)):

                def responder(url, timeout, f=failure):
                    if isinstance(f, _RawResponse):
                        return f
                    raise f

                result, _ = self.run_resident(responder)
                self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
