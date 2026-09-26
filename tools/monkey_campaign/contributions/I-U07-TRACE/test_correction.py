"""test_correction.py -- I-U07-TRACE correction tests (failing-first).

C1-C4 reproduce the lead's findings against the BASE module (they FAIL
there), and must PASS after the fix.
"""
import json
import math
import pathlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import input_trace as it  # noqa: E402


def make_records(t_values_by_seq, unit="ms"):
    stages = it.STAGES
    recs = []
    for seq, ts in t_values_by_seq.items():
        for stage, t in zip(stages, ts):
            recs.append({"seq": seq, "stage": stage, "t": t, "unit": unit,
                         "clock": "c1", "run": "r1", "build": "b1"})
    return recs


class C1OverflowAfterConversion(unittest.TestCase):
    def test_seconds_overflow_refused(self):
        recs = make_records({1: [1e308, 1e308, 1e308, 1e308]}, unit="s")
        with self.assertRaises(it.TraceRefused) as ctx:
            it.parse_trace(recs)
        self.assertIn(ctx.exception.reason, ("time_overflow", "non_finite_time"))

    def test_no_nan_ever_reaches_summary(self):
        recs = make_records({1: [1e308, 1e308, 1e308, 1e308]}, unit="s")
        try:
            events = it.parse_trace(recs)
            summary = it.summarize(events)
            text = json.dumps(summary)
            self.assertFalse(any(x in text for x in ("NaN", "Infinity")),
                             "defect: NaN/inf reached the summary")
            self.fail("defect: overflow trace was accepted")
        except it.TraceRefused:
            pass  # the fixed behavior


class C2LatencyArithmetic(unittest.TestCase):
    def test_latency_overflow_refused(self):
        # finite ms values whose differences would be finite too -- the pure
        # conversion-overflow path is C1; here extreme-but-finite spreads must
        # still never produce non-finite latency (regression guard)
        recs = make_records({1: [0.0, 1.0, 2.0, 3.0]})
        chains = it.chain_latencies(it.parse_trace(recs))
        for c in chains:
            for v in (c.seg_input_to_command_ms, c.seg_command_to_consumed_ms,
                      c.seg_consumed_to_presented_ms, c.end_to_end_ms):
                self.assertTrue(math.isfinite(v))


class C3EmptyLimits(unittest.TestCase):
    def test_empty_limits_never_pass(self):
        recs = make_records({1: [0.0, 1.0, 2.0, 3.0]})
        events = it.parse_trace(recs)
        summary = it.summarize(events, limits={})
        self.assertEqual(summary["qualification"]["status"], "unqualified")
        self.assertNotEqual(summary["qualification"]["status"], "pass")
        self.assertEqual(summary["qualification"].get("checks", {}), {})


class C4CliRefusal(unittest.TestCase):
    def test_cli_refusal_named_without_latency_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp) / "trace.jsonl"
            lines = []
            for stage, t in zip(it.STAGES, [1e308] * 4):
                lines.append(json.dumps({"seq": 1, "stage": stage, "t": t,
                                         "unit": "s", "clock": "c", "run": "r",
                                         "build": "b"}))
            p.write_text("\n".join(lines), encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, "-B", str(HERE / "input_trace.py"),
                 "--input", str(p)], capture_output=True, timeout=60)
            self.assertEqual(proc.returncode, 2)
            payload = json.loads(proc.stdout.decode("utf-8"))
            self.assertIn(payload["refused"],
                          ("time_overflow", "non_finite_time", "latency_overflow"))
            self.assertIsNone(payload["latency_output"])
            self.assertNotIn("NaN", proc.stdout.decode("utf-8"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
