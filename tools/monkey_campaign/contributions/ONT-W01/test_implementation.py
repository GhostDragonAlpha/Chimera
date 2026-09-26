"""ONT-W01 verifier tests — synthetic fixtures and mutation controls (P10).

Everything here runs on in-memory synthetic bytes; the real pinned records are
only touched by the explicitly-marked live test (read-only). Run:

    python -B -m unittest test_implementation -v
"""

from __future__ import annotations

import unittest

import implementation as impl


def _state_body(seed: float) -> str:
    toks = " ".join("q%d=%.17g" % (i, seed + i * 1e-3) for i in range(18))
    vtoks = " ".join("v%d=%.17g" % (i, seed * 2 + i * 1e-4) for i in range(18))
    return "%s %s" % (toks, vtoks)


def _state_line(t: int, seed: float) -> str:
    return "FULL t=%d %s" % (t, _state_body(seed))


def _walk_cpp(n_states: int) -> bytes:
    lines = []
    for t in range(n_states):
        lines.append("tick=%d q3=%.9f" % (t, t * 0.001))
        lines.append(_state_line(t, seed=t * 0.5))
    lines.append("END refused= refused_tick=-1")
    return ("\n".join(lines) + "\n").encode()


def _walk_host(n_states: int, break_at: int | None = None) -> bytes:
    """Host-style walk: FULL t=1..n_states, aligned to cpp t=0..n_states-1."""
    lines = ["reset: q4=0.386076555 rc_uninit"]
    for t in range(1, n_states + 1):
        lines.append("tick %4d: y=0.1 vx=0.2 rc=0 adv=1 refused=0 ticks=%d" % (t, t))
        seed = (t - 1) * 0.5 if break_at is None or t < break_at else (t - 1) * 0.5 + 1e9
        lines.append(_state_line(t, seed=seed))
    return ("\n".join(lines) + "\n").encode()


def _census_line(kind: str, t: int, sub: int, val: float, kernel: bool) -> str:
    pre = "batpost=78.7 w2=0.003 " if kernel else ""
    toks = " ".join("%s%d=%.17g" % (prefix, i, val + i)
                    for prefix, count in (("q", 4), ("v", 4))
                    for i in range(count))
    return "%s t=%d sub=%d %s%s" % (kind, t, sub, pre, toks)


def _census(n_records: int, diverge_at: int | None = None) -> tuple[bytes, bytes]:
    a_lines, b_lines = [], []
    for i in range(n_records):
        t, sub = i // 4, i % 4
        val = float(i)
        a = _census_line("SUBPRE", t, sub, val, kernel=False)
        b = _census_line("SUBPRE", t, sub, val, kernel=True)
        if diverge_at is not None and i == diverge_at:
            b = _census_line("SUBPRE", t, sub, val + 1e9, kernel=True)
        a_lines.append(a)
        b_lines.append(b)
    return ("\n".join(a_lines) + "\n").encode(), ("\n".join(b_lines) + "\n").encode()


def _state_file(label: int, body: str, count: int = 2) -> bytes:
    return ("".join("FULL t=%d %s\n" % (label, body) for _ in range(count))).encode()


def _fixture_records(**overrides) -> dict:
    # Build the fixture walks first, then derive the frozen state files from them
    # so the fixture is self-consistent under the alignment law (host t == cpp t-1).
    cp45 = _walk_cpp(45)
    hl45 = _walk_host(48)
    host_body = impl.parse_full_states(hl45)[40]
    cpp_body = impl.parse_full_states(cp45)[39]
    records = {
        "R-state-host": _state_file(40, host_body),
        "R-state-gpu": _state_file(40, host_body),
        "R-state-cpp": _state_file(39, cpp_body),
        "R-scene": (impl.SCENE_SHA256 + "\n").encode(),
        "R-cp45": cp45,
        "R-hl45": hl45,
        "R-csub5": _census(20)[0],
        "R-ksub5": _census(20)[0],
        "R-csub41": _census(20)[0],
        "R-ksub41": _census(20)[1],
        "R-hlv2": _walk_host(100),
        "R-hlpre": _walk_host(100),
        "R-gpuv2": _walk_host(43),
        "R-bars": b"{}",
    }
    records.update(overrides)
    return records


def _run_verdicts(records: dict) -> dict:
    checks = impl.verify_records(records, identities={})
    return {c["check"]: c["verdict"] for c in checks}


class TestParsers(unittest.TestCase):
    def test_parse_full_states_extracts_token_stream(self):
        raw = b"reset: x\r\nFULL t=1 q0=1 v0=2\r\nFULL t=2 q0=3 v0=4\r\n"
        self.assertEqual(impl.parse_full_states(raw), {1: "q0=1 v0=2", 2: "q0=3 v0=4"})

    def test_parse_full_states_strips_capture_cr_artifact(self):
        raw = b"FULL t=7 q0=1.5 v0=2.5\r\r\n"
        self.assertEqual(impl.parse_full_states(raw), {7: "q0=1.5 v0=2.5"})

    def test_parse_state_file_requires_identical_bodies(self):
        good = ("FULL t=40 %s\nFULL t=40 %s\n" % (_state_body(2.0), _state_body(2.0))).encode()
        bad = ("FULL t=40 %s\nFULL t=40 %s\n" % (_state_body(2.0), _state_body(3.0))).encode()
        self.assertEqual(impl.parse_state_file(good), (_state_body(2.0), 2))
        self.assertEqual(impl.parse_state_file(bad), (None, 2))

    def test_parse_census_drops_drill_only_prefix_keys(self):
        a, b = _census(4)
        ca, cb = impl.parse_census(a), impl.parse_census(b)
        self.assertEqual(len(ca), 4)
        self.assertEqual(ca[0]["toks"], cb[0]["toks"])
        self.assertNotIn("batpost", cb[0]["toks"])

    def test_census_divergence_reports_first_bad_record_and_keys(self):
        a, b = _census(6, diverge_at=3)
        div, notes = impl.census_divergence(impl.parse_census(a), impl.parse_census(b))
        self.assertIsNotNone(div)
        self.assertEqual(div["index_in_kind"], 3)
        self.assertEqual(div["reason"], "physics")
        self.assertTrue(div["differing_keys"])
        self.assertEqual(notes["per_kind_first_divergence"]["SUBPRE"], div)

    def test_aligned_divergence_none_when_equal(self):
        cp = impl.parse_full_states(_walk_cpp(45))
        hl = impl.parse_full_states(_walk_host(45))
        self.assertIsNone(impl.aligned_divergence(cp, hl, 41))
        self.assertIsNone(impl.aligned_divergence(cp, hl, 45))

    def test_aligned_divergence_finds_break(self):
        cp = impl.parse_full_states(_walk_cpp(45))
        hl = impl.parse_full_states(_walk_host(48, break_at=17))
        self.assertEqual(impl.aligned_divergence(cp, hl, 41), 17)


class TestMutationControls(unittest.TestCase):
    """P10: any single flipped compared byte must flip the verdict."""

    def test_clean_fixture_passes_P2_P3_P8(self):
        verdicts = _run_verdicts(_fixture_records())
        self.assertEqual(verdicts["P2"], "PASS")
        self.assertEqual(verdicts["P3"], "PASS")
        self.assertEqual(verdicts["P8"], "PASS")

    def test_state_gpu_single_byte_flip_fails_P2(self):
        rec = _fixture_records()
        blob = bytearray(rec["R-state-gpu"])
        pos = blob.index(b"q0=") + 3
        blob[pos] = ord("9") if blob[pos] != ord("9") else ord("8")
        rec["R-state-gpu"] = bytes(blob)
        self.assertEqual(_run_verdicts(rec)["P2"], "FAIL")

    def test_scene_sha_flip_fails_P2(self):
        last = impl.SCENE_SHA256[-1]
        flipped = impl.SCENE_SHA256[:-1] + ("0" if last != "0" else "1")
        rec = _fixture_records(R_scene=(flipped + "\n").encode())
        rec["R-scene"] = rec.pop("R_scene")
        self.assertEqual(_run_verdicts(rec)["P2"], "FAIL")

    def test_cpp_host_label_only_difference_still_passes_P2(self):
        rec = _fixture_records()
        self.assertEqual(_run_verdicts(rec)["P2"], "PASS")

    def test_walk_pair_divergence_fails_P3(self):
        rec = _fixture_records(R_hl45=_walk_host(48, break_at=5))
        rec["R-hl45"] = rec.pop("R_hl45")
        self.assertEqual(_run_verdicts(rec)["P3"], "FAIL")

    def test_missing_record_fails_check(self):
        rec = _fixture_records()
        rec["R-hl45"] = None
        self.assertEqual(_run_verdicts(rec)["P3"], "FAIL")

    def test_census_drift_fails_P5(self):
        rec = _fixture_records(R_ksub41=_census(20, diverge_at=11)[1])
        rec["R-ksub41"] = rec.pop("R_ksub41")
        self.assertEqual(_run_verdicts(rec)["P5"], "FAIL")

    def test_census_count_mismatch_fails_P5(self):
        rec = _fixture_records()
        rec["R-csub41"], rec["R-ksub41"] = _census(19)[0], _census(20)[1]
        self.assertEqual(_run_verdicts(rec)["P5"], "FAIL")

    def test_defect_record_P4_requires_SUBPRE_t3_sub3(self):
        rec = _fixture_records()
        rec["R-csub5"], rec["R-ksub5"] = _census(20, diverge_at=15)  # i=15 -> t=3 sub=3
        self.assertEqual(_run_verdicts(rec)["P4"], "PASS")
        rec = _fixture_records()
        rec["R-csub5"], rec["R-ksub5"] = _census(20, diverge_at=7)  # i=7 -> t=1 sub=3
        self.assertEqual(_run_verdicts(rec)["P4"], "FAIL")

    def test_gpu_parity_flip_fails_P8(self):
        rec = _fixture_records(R_gpuv2=_walk_host(43, break_at=40))
        rec["R-gpuv2"] = rec.pop("R_gpuv2")
        self.assertEqual(_run_verdicts(rec)["P8"], "FAIL")

    def test_v2_replay_refusal_fails_P6(self):
        lines = _walk_host(100).decode().splitlines()
        lines.append("REFUSED at tick 41 rc=5 refused=1 adv=2 ticks=40")
        rec = _fixture_records(R_hlv2=("\n".join(lines) + "\n").encode())
        rec["R-hlv2"] = rec.pop("R_hlv2")
        self.assertEqual(_run_verdicts(rec)["P6"], "FAIL")

    def test_p9_rejects_missing_bars(self):
        rec = _fixture_records()
        self.assertEqual(_run_verdicts(rec)["P9"], "FAIL")


class TestVerdictRule(unittest.TestCase):
    def test_verdict_requires_all_predictions(self):
        checks = [{"check": "P1", "verdict": "PASS"}, {"check": "P4", "verdict": "PASS"}]
        verdict, failed = impl.verdict_from_checks(checks)
        self.assertEqual(verdict, "NOT_SATISFIED")
        self.assertIn("P2", failed)

    def test_p4_failure_named_even_when_required_pass(self):
        checks = [{"check": "P%d" % i, "verdict": "PASS"} for i in range(1, 10)]
        checks = [c if c["check"] != "P4" else {"check": "P4", "verdict": "FAIL"} for c in checks]
        verdict, failed = impl.verdict_from_checks(checks)
        self.assertEqual(verdict, "NOT_SATISFIED")
        self.assertIn("P4(defect-record)", failed)

    def test_all_pass_is_satisfied(self):
        checks = [{"check": "P%d" % i, "verdict": "PASS"} for i in range(1, 10)]
        verdict, failed = impl.verdict_from_checks(checks)
        self.assertEqual((verdict, failed), ("SATISFIED_BY_RECORDS", []))


class TestLiveRecords(unittest.TestCase):
    """Read-only checks against the real pinned objects."""

    def test_live_audit_passes(self):
        records = impl.collect_records()
        missing = [n for n, b in records.items() if b is None]
        if missing:
            self.skipTest("pinned records unavailable in this checkout: %s" % missing)
        identities = impl.collect_identities()
        for c in impl.verify_records(records, identities):
            self.assertEqual(c["verdict"], "PASS", "%s failed: %s" % (c["check"], c["detail"]))


if __name__ == "__main__":
    unittest.main()
