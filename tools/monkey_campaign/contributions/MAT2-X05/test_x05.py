#!/usr/bin/env python3
"""MAT2-X05: the development test battery (the gate-visible suite).

Scene-free unit laws (the certified line is NOT touched here; the sealed
verification battery owns the live predictions):
  - the declared glyph law and the instrument receipt/probe round trip;
  - the instrument string derivation from a row;
  - the palette disjointness assertion (spec-load law, re-executed);
  - the declared landmark geometry (vertex/triangle counts, palette set);
  - the landmark set derivation from an anchor base;
  - the diff-channel machinery on synthetic frames (zero when identical;
    the declared channels when different; the attribution law form);
  - the landmark displacement measure;
  - the coupling determination's structural audit (X-P10) over THIS
    contribution;
  - the coupling determination re-derivation over the pinned sealed records
    (the bytes exist inside the sealed run; the battery refuses rather than
    skips if they are absent).

Run:  python -B test_x05.py   (unittest; also stage 0 of run_all.py)
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import instrument_x05 as ix          # noqa: E402
import landmarks_x05 as lm           # noqa: E402
import state_readout_x05 as srx      # noqa: E402
import diff_channels as dc           # noqa: E402
import coupling_determination as cd  # noqa: E402

CONTRIB = HERE
A12_SHORT = Path("E:/ChimeraWork/task-runner/results/"
                 "ca111cdc917e420eb78c41339d88c41b/artifacts/outputs/"
                 "driver_pair_P01_BRAKE-SHORT.json")
A12_LONG = Path("E:/ChimeraWork/task-runner/results/"
                "ca111cdc917e420eb78c41339d88c41b/artifacts/outputs/"
                "driver_pair_P02_BRAKE-LONG.json")


def blank_frame():
    return np.zeros((540, 960, 3), dtype=np.uint8)


def synth_row(v=0.7465295, tick=4365):
    return {"com_v_m_s": v, "tick": tick}


class InstrumentLaw(unittest.TestCase):
    def test_glyph_table_set(self):
        self.assertEqual(set(ix._GLYPHS),
                         set("V0123456789.="))

    def test_string_derivation(self):
        row = synth_row(0.7465295)
        self.assertEqual(ix.instrument_string(row), "V=0.747")
        row = synth_row(0.6232)
        self.assertEqual(ix.instrument_string(row), "V=0.623")

    def test_expected_metrics(self):
        m = ix.expected_text_metrics("V=0.747")
        self.assertEqual(m["width_px"], (7 * 4 - 1) * 2)
        self.assertEqual(m["height_px"], 10)
        # V=3+2+5+2+5+5+5 on-counts: V=10? recompute independently
        on = sum(ix.GLYPH_ON_COUNT[c] for c in "V=0.747")
        self.assertEqual(m["pixel_count"], on * 4)

    def test_draw_and_probe_round_trip(self):
        colour = [[(0, 0, 0) for _ in range(960)] for _ in range(540)]
        row = synth_row(0.694329)
        receipt = ix.draw_instrument(colour, row)
        arr = np.asarray(colour, dtype=np.uint8)
        findings = ix.probe_instrument(arr, receipt)
        self.assertTrue(findings["ok"], findings)
        self.assertTrue(findings["truthful"])
        self.assertEqual(receipt["text"], "V=0.694")

    def test_probe_refuses_tampered_value(self):
        colour = [[(0, 0, 0) for _ in range(960)] for _ in range(540)]
        row = synth_row(0.694329)
        receipt = ix.draw_instrument(colour, row)
        arr = np.asarray(colour, dtype=np.uint8)
        receipt["com_v_m_s_row"] = 0.747357     # a different claimed value
        findings = ix.probe_instrument(arr, receipt)
        self.assertFalse(findings["truthful"])
        self.assertFalse(findings["ok"])


class PaletteLaw(unittest.TestCase):
    def test_disjointness_executes(self):
        law = srx.assert_palette_disjointness()
        self.assertGreaterEqual(law["checked_colors"], 25)

    def test_x05_colors_absent_from_pinned(self):
        pinned = {c for pal in srx.EXISTING_PALETTES.values()
                  for c in pal}
        for c in srx.X05_ADDED_COLORS:
            self.assertNotIn(c, pinned, repr(c))


class LandmarkLaw(unittest.TestCase):
    def test_declared_geometry_counts(self):
        v = lm.tree_vertices(1.87, -2.5)
        self.assertEqual(len(v[:8]), 8)     # trunk box corners
        self.assertEqual(len(v[8:]), 4)     # canopy tetra
        tris = lm.landmark_triangles("landmark_tree_far", 1.87, -2.5)
        trunks = [t for t, rgb in tris
                  if rgb == lm.LANDMARK_PALETTES["landmark_tree_far"]["trunk"]]
        canopy = [t for t, rgb in tris
                  if rgb == lm.LANDMARK_PALETTES["landmark_tree_far"]["canopy"]]
        self.assertEqual(len(trunks), 8)
        self.assertEqual(len(canopy), 4)
        rock = lm.rock_vertices(1.87, -4.0)
        self.assertEqual(len(rock), 4)
        rtris = lm.landmark_triangles("landmark_rock_far", 1.87, -4.0)
        self.assertEqual(len(rtris), 4)

    def test_declared_offsets(self):
        self.assertEqual(lm.LANDMARK_OFFSETS["landmark_tree_far"],
                         (-6.5, -2.5))
        self.assertEqual(lm.LANDMARK_OFFSETS["landmark_tree_near"],
                         (-3.5, -3.0))
        self.assertEqual(lm.LANDMARK_OFFSETS["landmark_rock_far"],
                         (-6.5, -4.0))
        self.assertEqual(lm.LANDMARK_OFFSETS["landmark_rock_near"],
                         (-3.5, -5.0))

    def test_set_derivation_from_anchor(self):
        s = lm.build_landmark_set(8.374762475071417)
        self.assertEqual(sorted(s), sorted(lm.LANDMARK_ORDER))
        self.assertAlmostEqual(s["landmark_tree_far"]["base"][0],
                               8.374762475071417 - 6.5)
        self.assertAlmostEqual(s["landmark_rock_near"]["base"][1], -5.0)

    def test_declared_palettes_one_per_object(self):
        self.assertEqual(lm.LANDMARK_PALETTES["landmark_tree_far"],
                         {"trunk": (94, 61, 38), "canopy": (34, 94, 44)})
        self.assertEqual(lm.LANDMARK_PALETTES["landmark_rock_near"],
                         {"rock": (108, 108, 102)})


class DiffChannelLaw(unittest.TestCase):
    def test_zero_when_identical(self):
        a = blank_frame()
        a[:, :] = (168, 198, 150)
        series = dc.pair_series([a] * 3, [a.copy() for _ in range(3)],
                                [4365, 4380, 4395], 4366)
        self.assertTrue(series["pre_lawful_all_zero"])
        self.assertEqual(series["first_lawful_whole_frame_diff"], 0)
        self.assertTrue(series["no_pixel_reflection_in_window_persists"])

    def test_channels_on_synthetic_divergence(self):
        a = blank_frame()
        a[:, :] = (168, 198, 150)
        b = a.copy()
        # b repaints one landmark color and one instrument pixel
        b[100, 100] = (94, 61, 38)      # tree_far trunk color
        b[20, 20] = (10, 82, 10)        # instrument ink color
        b[300, 500] = (120, 80, 60)     # body color
        series = dc.pair_series([a, a], [b, b], [4365, 4380], 4366)
        self.assertFalse(series["rows"][0]["lawful"])
        r = series["rows"][1]
        self.assertEqual(r["whole_frame_diff"], 3)
        self.assertEqual(r["landmark_channel_diff"], 1)
        self.assertEqual(r["instrument_channel_diff"], 1)
        self.assertEqual(r["body_channel_diff"], 1)
        self.assertFalse(series["no_pixel_reflection_in_window_persists"])

    def test_attribution_law_form(self):
        a = blank_frame()
        b_pre = a.copy()                 # prefix-identical (the certified
        b_lawful = a.copy()              # law: zero before consumption)
        b_lawful[10, 10] = (1, 2, 3)
        series = dc.pair_series([a, a], [b_pre, b_lawful], [4365, 4380],
                                4380)
        # presented 4365 < consumed 4380: pre-lawful slot
        self.assertFalse(series["rows"][0]["lawful"])
        self.assertTrue(series["rows"][1]["lawful"])
        self.assertEqual(series["pre_lawful_all_zero"], True)
        self.assertEqual(series["first_lawful_whole_frame_diff"], 1)


class CouplingLaw(unittest.TestCase):
    def test_structural_audit_passes_own_contribution(self):
        audit = cd.audit_no_velocity_to_stride(CONTRIB)
        self.assertEqual(audit["refusals"], [])
        self.assertIn("render_x05.py", audit["files_audited"])

    def test_derivation_over_pinned_records(self):
        if not (A12_SHORT.exists() and A12_LONG.exists()):
            self.fail("coupling_input_pin_missing:sealed a12 driver records "
                      "absent (the battery refuses rather than skips)")
        recs = {"SHORT": __import__("json").loads(
                    A12_SHORT.read_bytes()),
                "LONG": __import__("json").loads(A12_LONG.read_bytes())}
        det = cd.derive(recs)
        self.assertEqual(det["phase_identity"], "42/42")
        self.assertEqual(det["com_v_divergence"], "40/42")
        self.assertEqual(det["disposition"],
                         "DECLARED_ABSENT_IN_THE_A12_LINE_REGIME")
        self.assertAlmostEqual(det["per_depth"]["SHORT"]["com_v_first_A"],
                               0.746530, places=5)
        self.assertAlmostEqual(det["per_depth"]["SHORT"]["com_v_last_A"],
                               0.694329, places=5)
        self.assertAlmostEqual(det["per_depth"]["LONG"]["com_v_last_A"],
                               0.623221, places=5)
        self.assertAlmostEqual(det["per_depth"]["SHORT"]["com_x_travel_A"],
                               0.7004, places=3)
        self.assertAlmostEqual(det["per_depth"]["LONG"]["com_x_travel_A"],
                               0.6787, places=3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
