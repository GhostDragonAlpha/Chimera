"""B5 battery: the preregistered bars (67aa80de).
judge() is pure and runs offline; the live measurement is run separately
(see module __main__) and its actuals are recorded as evidence.
Run: python -m unittest tools.matter_kernel.test_residency"""
from __future__ import annotations

import unittest

from tools.matter_kernel.residency import (BUDGET_MS, FLOOR_FPS,
                                           ResidencyRefused, judge)


def sample(pushes, fps=250.0, ft_avg=3.0, rec_calls=None, rec_draws=None):
    # rec counters default to tracking pushes (one recorder call and
    # one draw per frame); explicit values override for stall mutants
    return {"pushes": pushes, "fps": fps, "ft_avg": ft_avg,
            "rec_calls": pushes if rec_calls is None else rec_calls,
            "rec_draws": pushes if rec_draws is None else rec_draws}


class ResidencyBars(unittest.TestCase):
    def test_p1_liveness_silent_window(self):
        """P1: 250 fps for 10 s of silence -> ~2500 frames advance;
        the judge passes with the derived minimum noted."""
        out = judge(sample(1000), sample(1000 + 2500), 10.0)
        self.assertTrue(out["resident"])
        self.assertEqual(out["frames_advanced"], 2500)
        self.assertGreaterEqual(out["frames_advanced"],
                                FLOOR_FPS * 10.0)

    def test_p2_recorder_keeps_drawing(self):
        """P2: rec.calls and rec.draws must advance — the resident
        scene keeps being drawn, nothing was re-uploaded."""
        with self.assertRaisesRegex(ResidencyRefused, "recorder_stalled"):
            judge(sample(1000, rec_calls=100),
                  sample(2500, rec_calls=100), 10.0)
        out = judge(sample(1000, rec_calls=100),
                    sample(2500, rec_calls=3600), 10.0)
        self.assertEqual(out["rec_calls"], 3500)

    def test_p3_budget_band(self):
        """P3: rate and budget derive from the COUNTER (amendment):
        frames/window >= 100 and window_ms/frames <= 10 ms; the smoothed
        served fields are recorded, never judged. The 22 fps per-frame
        incident reproduces as a counter at 22/s: band AND budget fail."""
        out = judge(sample(1000), sample(3800), 10.0)
        self.assertAlmostEqual(out["fps_counter"], 280.0)
        self.assertAlmostEqual(out["mean_frame_ms"], 10000.0 / 2800.0)
        self.assertTrue(out["fps_floor_ok"])
        self.assertTrue(out["budget_ok"])
        out = judge(sample(1000), sample(1000 + 220), 10.0)
        self.assertFalse(out["fps_floor_ok"])
        self.assertAlmostEqual(out["mean_frame_ms"], 10000.0 / 220.0)
        self.assertFalse(out["budget_ok"])
        self.assertAlmostEqual(out["fps_counter"], 22.0)

    def test_p3b_stall_refusal(self):
        """P1 mutation: zero frame advance is a named refusal."""
        with self.assertRaisesRegex(ResidencyRefused, "stalled_frames"):
            judge(sample(5000), sample(5000), 10.0)
        with self.assertRaisesRegex(ResidencyRefused, "stalled_frames"):
            judge(sample(5000), sample(4999), 10.0)

    def test_p4_band_floor_values(self):
        """P3 derivation pinned: floor 100 fps (5x the 22 fps
        incident), budget 10 ms."""
        self.assertEqual(FLOOR_FPS, 100.0)
        self.assertEqual(BUDGET_MS, 10.0)
        self.assertFalse(judge(sample(0, fps=99.9),
                               sample(999, fps=99.9), 10.0)["fps_floor_ok"])
        self.assertFalse(judge(sample(0),
                               sample(500), 10.0)["budget_ok"])

    def test_p5_named_refusals(self):
        """P5: bad window, missing fields, dead engine (read_chrome
        refuses before any judging)."""
        with self.assertRaisesRegex(ResidencyRefused, "invalid_window"):
            judge(sample(0), sample(1000), 0.0)
        with self.assertRaisesRegex(ResidencyRefused, "invalid_window"):
            judge(sample(0), sample(1000), None)
        with self.assertRaisesRegex(ResidencyRefused, "invalid_sample"):
            judge({"pushes": 1}, sample(1000), 10.0)
        from tools.matter_kernel.residency import read_chrome
        with self.assertRaisesRegex(ResidencyRefused, "engine_down"):
            read_chrome("http://127.0.0.1:1", timeout_s=2.0)


if __name__ == "__main__":
    unittest.main()
