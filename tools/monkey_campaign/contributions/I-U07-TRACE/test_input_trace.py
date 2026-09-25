"""test_input_trace.py -- I-U07-TRACE falsifier suite (PREREGISTRATION F1-F5).

Every analytic trace below is a FIXTURE (hand-built, exact numbers). None of
them is actual-play evidence; U07's native gates stay open. Runtime is bounded
trivially (< a few seconds) and output is tiny, per the card limits.

Run:  python -B test_input_trace.py   (unittest, exit code is the verdict)
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from input_trace import (  # noqa: E402
    STAGES, TraceEvent, TraceRefused, chain_latencies, parse_trace, summarize,
)

CLOCK, RUN, BUILD = "steady_ns", "run-fixture-1", "build-fixture-9afbddcd"


def ev(seq: int, stage: str, t: float, unit: str = "ms", **over) -> dict:
    rec = {"seq": seq, "stage": stage, "t": t, "unit": unit,
           "clock": CLOCK, "run": RUN, "build": BUILD}
    rec.update(over)
    return rec


def chain(seq: int, t0: float, a: float, b: float, c: float) -> list[dict]:
    """A complete chain: input at t0, then three exact segment lengths (ms)."""
    return [ev(seq, "input", t0),
            ev(seq, "command_emitted", t0 + a),
            ev(seq, "simulation_consumed", t0 + a + b),
            ev(seq, "presented", t0 + a + b + c)]


class AnalyticExactness(unittest.TestCase):
    """P1: planted intervals come back exactly; stats equal hand-computed."""

    def test_exact_intervals_and_stats(self):
        # 4 chains, planted segment lengths chosen for exact float arithmetic.
        planted = {1: (10.0, 20.0, 30.0),        # e2e 60
                   2: (11.0, 19.0, 31.0),        # e2e 61
                   3: (12.0, 21.0, 29.5),        # e2e 62.5
                   4: (13.0, 18.0, 32.5)}        # e2e 63.5
        records = []
        for seq, (a, b, c) in planted.items():
            records.extend(chain(seq, 1000.0 * seq, a, b, c))
        events = parse_trace(records)
        chains = {cl.seq: cl for cl in chain_latencies(events)}
        for seq, (a, b, c) in planted.items():
            self.assertEqual(chains[seq].seg_input_to_command_ms, a)
            self.assertEqual(chains[seq].seg_command_to_consumed_ms, b)
            self.assertEqual(chains[seq].seg_consumed_to_presented_ms, c)
            self.assertEqual(chains[seq].end_to_end_ms, a + b + c)

        s = summarize(events)
        e2e = s["segments"]["end_to_end_ms"]
        self.assertEqual(e2e["count"], 4)
        self.assertEqual(e2e["min_ms"], 60.0)
        self.assertEqual(e2e["max_ms"], 63.5)
        self.assertEqual(e2e["mean_ms"], (60.0 + 61.0 + 62.5 + 63.5) / 4)
        # nearest-rank on [60, 61, 62.5, 63.5]: p50=ceil(2)->61, p95=ceil(3.8)->63.5
        self.assertEqual(e2e["p50_ms"], 61.0)
        self.assertEqual(e2e["p95_ms"], 63.5)
        self.assertEqual(e2e["p99_ms"], 63.5)
        self.assertEqual(s["qualification"]["status"], "unqualified")
        self.assertEqual(s["qualification"]["reason"], "p06_limits_absent")

    def test_unit_conversion_exact(self):
        # one chain in seconds, same chain in ms -- identical canonical values
        s_records = chain(7, 1.5, a=0.010, b=0.020, c=0.030)  # seconds
        for r in s_records:
            r["unit"] = "s"
        ms_records = chain(7, 1500.0, 10.0, 20.0, 30.0)
        c_s = chain_latencies(parse_trace(s_records))[0]
        c_ms = chain_latencies(parse_trace(ms_records))[0]
        self.assertEqual(c_s.end_to_end_ms, c_ms.end_to_end_ms)
        self.assertEqual(c_s.end_to_end_ms, 60.0)
        # per-event mixed units inside one trace are legal (one clock identity)
        mixed = [ev(8, "input", 1.0, unit="s"), ev(8, "command_emitted", 1010.0),
                 ev(8, "simulation_consumed", 1030.0), ev(8, "presented", 1060.0)]
        self.assertEqual(chain_latencies(parse_trace(mixed))[0].seg_input_to_command_ms, 10.0)

    def test_interleaved_and_out_of_order_records(self):
        # arrival order is not the pipeline order; matching is by (seq, stage)
        recs = [ev(1, "presented", 1160.0), ev(2, "input", 2000.0),
                ev(1, "input", 1000.0), ev(2, "presented", 2061.0),
                ev(1, "simulation_consumed", 1030.0), ev(2, "command_emitted", 2011.0),
                ev(1, "command_emitted", 1010.0), ev(2, "simulation_consumed", 2030.0)]
        chains = {c.seq: c for c in chain_latencies(parse_trace(recs))}
        self.assertEqual(chains[1].end_to_end_ms, 160.0)
        self.assertEqual(chains[2].end_to_end_ms, 61.0)


class Refusals(unittest.TestCase):
    """P2 + F1/F2: each break refuses by name and yields NO latency."""

    def _refused(self, records, reason):
        with self.assertRaises(TraceRefused) as cm:
            parse_trace(records)
        self.assertEqual(cm.exception.reason, reason, msg=str(cm.exception.details))
        return cm.exception

    def test_empty_trace(self):
        self._refused([], "empty_trace")

    def test_missing_stage(self):
        recs = chain(1, 0.0, 5.0, 5.0, 5.0)[:-1]  # drop 'presented'
        self._refused(recs, "missing_stage")

    def test_mixed_clock(self):
        recs = chain(1, 0.0, 5.0, 5.0, 5.0)
        recs[2]["clock"] = "qpc"
        self._refused(recs, "mixed_clock")

    def test_mixed_run_and_build(self):
        recs = chain(1, 0.0, 5.0, 5.0, 5.0)
        recs[1]["run"] = "run-other"
        self._refused(recs, "mixed_run")
        recs = chain(1, 0.0, 5.0, 5.0, 5.0)
        recs[1]["build"] = "build-other"
        self._refused(recs, "mixed_build")

    def test_duplicate_seq_stage(self):
        recs = chain(1, 0.0, 5.0, 5.0, 5.0) + [ev(1, "input", 999.0)]
        self._refused(recs, "duplicate_seq_stage")

    def test_non_finite_time(self):
        recs = chain(1, 0.0, 5.0, 5.0, 5.0)
        recs[3]["t"] = float("inf")
        self._refused(recs, "non_finite_time")
        recs = chain(1, 0.0, 5.0, 5.0, 5.0)
        recs[3]["t"] = float("nan")
        self._refused(recs, "non_finite_time")

    def test_reversed_stage_order(self):
        recs = chain(1, 0.0, 5.0, 5.0, 5.0)
        recs[3]["t"] = 9.0  # presented BEFORE simulation_consumed (10.0)
        self._refused(recs, "reversed_stage_order")

    def test_unknown_stage_and_missing_field_and_bad_type(self):
        recs = chain(1, 0.0, 5.0, 5.0, 5.0)
        recs[0]["stage"] = "teleport"
        self._refused(recs, "unknown_stage")
        recs = chain(1, 0.0, 5.0, 5.0, 5.0)
        del recs[2]["clock"]
        self._refused(recs, "missing_field")
        recs = chain(1, 0.0, 5.0, 5.0, 5.0)
        recs[1]["seq"] = "one"
        self._refused(recs, "bad_type")

    def test_bad_unit(self):
        recs = chain(1, 0.0, 5.0, 5.0, 5.0)
        recs[0]["unit"] = "frames"
        self._refused(recs, "bad_unit")

    def test_chain_latencies_also_refuses_partial(self):
        # F1 belt-and-braces: even bypassing parse_trace, arithmetic never sees
        # a partial chain (chain_latencies refuses on its own).
        fake = [TraceEvent(seq=9, stage="input", t=0.0, unit="ms", t_ms=0.0,
                           clock=CLOCK, run=RUN, build=BUILD)]
        with self.assertRaises(TraceRefused) as cm:
            chain_latencies(fake)
        self.assertEqual(cm.exception.reason, "missing_stage")


class Qualification(unittest.TestCase):
    """P3: verdicts derive ONLY from caller-supplied limits."""

    def _events(self):
        recs = []
        for seq, (a, b, c) in {1: (10.0, 20.0, 30.0), 2: (12.0, 22.0, 32.0)}.items():
            recs.extend(chain(seq, 100.0 * seq, a, b, c))
        return parse_trace(recs)

    def test_limits_absent_is_unqualified(self):
        q = summarize(self._events())["qualification"]
        self.assertEqual(q["status"], "unqualified")

    def test_pass_and_fail_against_caller_data(self):
        # chains: e2e 60.0 and 66.0 -> max 66.0, p95 66.0 (nearest-rank)
        s = summarize(self._events(), limits={"end_to_end_ms": 66.0})
        self.assertEqual(s["qualification"]["status"], "pass")
        s = summarize(self._events(), limits={"end_to_end_ms": 61.0})
        self.assertEqual(s["qualification"]["status"], "fail")
        self.assertEqual(s["qualification"]["checks"]["end_to_end_ms"]["observed_ms"], 66.0)
        s = summarize(self._events(), limits={"p95_end_to_end_ms": 66.0,
                                              "seg_input_to_command_ms": 12.0})
        self.assertEqual(s["qualification"]["status"], "pass")

    def test_unknown_or_bad_limit_refuses(self):
        with self.assertRaises(TraceRefused) as cm:
            summarize(self._events(), limits={"frames_per_second_min": 60})
        self.assertEqual(cm.exception.reason, "unknown_limit_key")
        with self.assertRaises(TraceRefused) as cm:
            summarize(self._events(), limits={"end_to_end_ms": float("nan")})
        self.assertEqual(cm.exception.reason, "bad_limit")


class CLI(unittest.TestCase):
    """CLI JSON out: refusal prints ONLY the refusal (F1); pass path round-trips."""

    HERE = os.path.dirname(os.path.abspath(__file__))

    def _run(self, *args):
        return subprocess.run([sys.executable, "-B", os.path.join(self.HERE, "input_trace.py"), *args],
                              capture_output=True, text=True, timeout=60)

    def test_cli_summary_and_unqualified(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "trace.jsonl")
            with open(path, "w", encoding="utf-8") as fh:
                for r in chain(1, 0.0, 5.0, 6.0, 7.0):
                    fh.write(json.dumps(r) + "\n")
            r = self._run("--input", path)
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            out = json.loads(r.stdout)
            self.assertEqual(out["schema"], "chimera.input_trace.summary.v1")
            self.assertEqual(out["qualification"]["status"], "unqualified")
            self.assertEqual(out["chains"][0]["end_to_end_ms"], 18.0)

    def test_cli_refusal_emits_no_latency(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "broken.jsonl")
            with open(path, "w", encoding="utf-8") as fh:
                for r in chain(1, 0.0, 5.0, 6.0, 7.0)[:-1]:
                    fh.write(json.dumps(r) + "\n")
            r = self._run("--input", path)
            self.assertEqual(r.returncode, 2)
            out = json.loads(r.stdout)
            self.assertEqual(out["refused"], "missing_stage")
            self.assertIsNone(out["latency_output"])
            self.assertNotIn("end_to_end", json.dumps(out))  # F1: no numbers

    def test_cli_with_limits_file(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "trace.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(chain(1, 0.0, 5.0, 6.0, 7.0), fh)
            lim = os.path.join(td, "limits.json")
            with open(lim, "w", encoding="utf-8") as fh:
                json.dump({"end_to_end_ms": 100.0}, fh)
            r = self._run("--input", path, "--limits", lim)
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            out = json.loads(r.stdout)
            self.assertEqual(out["qualification"]["status"], "pass")
            self.assertEqual(out["qualification"]["source"], "explicit caller data")


class HeadlessLaw(unittest.TestCase):
    """F4: the module never reads a wall clock / opens a window / does hidden IO."""

    def test_source_imports_no_clock_or_window(self):
        src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "input_trace.py"), encoding="utf-8").read()
        for banned in ("time.time(", "perf_counter(", "monotonic(", "pygame",
                       "tkinter", "urllib", "socket", "requests"):
            self.assertNotIn(banned, src, msg=f"banned token {banned!r} in source")
        # deterministic: same input, byte-identical output
        recs = chain(3, 12.0, 1.0, 2.0, 3.0)
        a = json.dumps(summarize(parse_trace(recs)), sort_keys=True)
        b = json.dumps(summarize(parse_trace(recs)), sort_keys=True)
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main(verbosity=1)
