"""test_visibility.py — the two-phase lifecycle, CPU-only (gate T2, frozen).

    python tools/product_viewer/test_visibility.py
    python -m unittest discover -s tools/product_viewer -p "test_*.py" -v

No engine, no GPU, no network: the lifecycle law and the composer's
no-overlay-exactness law are tested against synthetic snapshots. PIL is
optional (its absence only skips the compose tests — recorded, never a silent
pass: the module must exist and import either way).
"""
from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from product_viewer.visibility import (          # noqa: E402
    Element, VisibilityBoard, UNVERIFIED, VERIFYING, PROVEN, compose,
)

try:
    from PIL import Image
    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False


def tiny_png() -> bytes:
    img = Image.new("RGB", (64, 48), (10, 10, 10))
    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


class LifecycleTest(unittest.TestCase):
    """P4: the two-phase lifecycle, each transition named in the prereg."""

    def test_01_boot_is_invisible_unverified(self):
        """A fresh product boots with every plane invisible (Law 2's end state)."""
        b = VisibilityBoard()
        for el in b.elements.values():
            self.assertFalse(el.visible)
            self.assertEqual(el.state, UNVERIFIED)
            self.assertFalse(el.proven)

    def test_02_user_toggle_makes_visible(self):
        """Law 2 phase 1: the user's deliberate flip starts VERIFICATION."""
        b = VisibilityBoard()
        r = b.handle_post({"element": "water", "on": True})
        self.assertTrue(r["ok"])
        el = b.elements["water"]
        self.assertTrue(el.visible)
        self.assertEqual(el.state, VERIFYING)

    def test_03_gate_pass_proves_and_reverts(self):
        """Law 2 phase 2: proven -> INVISIBLE, with no user override set."""
        el = Element("water", "test", gate=lambda e: True)
        el.state = VERIFYING
        el.snapshot = {"ok": True, "nc": 10}
        el.history = [{"sum": 5}, {"sum": 7}]
        g = el.run_gate()
        self.assertTrue(g["ok"])
        self.assertTrue(el.proven)
        self.assertEqual(el.state, PROVEN)
        self.assertFalse(el.visible)            # THE AUTO-REVERT

    def test_04_gate_without_data_stays_open(self):
        """A gate that cannot see its data never lies about proof."""
        el = Element("water", "test", gate=lambda e: True)
        el.state = VERIFYING
        el.snapshot = {"ok": False, "error": "no water"}
        g = el.run_gate()
        self.assertFalse(g["ok"])
        self.assertFalse(el.proven)
        self.assertTrue(el.visible)             # still verifying

    def test_05_gate_fail_keeps_verification(self):
        el = Element("water", "test", gate=lambda e: e.snapshot.get("moving"))
        el.state = VERIFYING
        el.snapshot = {"ok": True, "moving": False}
        el.run_gate()
        self.assertFalse(el.proven)
        self.assertEqual(el.state, VERIFYING)
        self.assertTrue(el.visible)

    def test_06_pinned_open_survives_proof(self):
        """The user pinned VISIBLE: proof lands, the pin holds the overlay up."""
        el = Element("water", "test", gate=lambda e: True)
        el.state = VERIFYING
        el.set_override(True)
        el.snapshot = {"ok": True}
        el.run_gate()
        self.assertTrue(el.proven)
        self.assertEqual(el.state, PROVEN)
        self.assertTrue(el.visible)             # the deliberate lesson stays up

    def test_07_clear_pin_returns_to_lifecycle(self):
        el = Element("water", "test", gate=lambda e: True)
        el.state = VERIFYING
        el.set_override(True)
        el.snapshot = {"ok": True}
        el.run_gate()                            # proven, pinned visible
        el.set_override(None)
        self.assertFalse(el.visible)             # lifecycle: proven = invisible
        self.assertTrue(el.proven)

    def test_08_pin_false_hides_even_when_verifying(self):
        el = Element("stride", "test", gate=lambda e: True)
        el.state = VERIFYING
        el.set_override(False)
        self.assertFalse(el.visible)
        el.set_override(None)
        self.assertTrue(el.visible)

    def test_09_reset_is_a_fresh_plane(self):
        el = Element("matter", "test", gate=lambda e: True)
        el.state = VERIFYING
        el.snapshot = {"ok": True}
        el.run_gate()
        el.set_override(True)
        el.reset()
        self.assertEqual((el.state, el.proven, el.user_override, el.visible),
                         (UNVERIFIED, False, None, False))

    def test_10_board_flow_toggle_gate_revert_retoggle(self):
        """The proof-take cycle end to end through the board's own API."""
        b = VisibilityBoard()
        b.auto_prove = False                     # the take paces gates itself
        b.handle_post({"element": "cpg", "on": True})
        self.assertTrue(b.elements["cpg"].visible)
        b.elements["cpg"].snapshot = {"ok": True, "loaded": True, "on": True,
                                      "steps_total": 40, "thetaL": 0.1}
        b.elements["cpg"].history = [{"thetaL": 0.1}, {"thetaL": 0.4}]
        g = b.handle_post({"element": "cpg", "action": "run_gate"})
        self.assertTrue(g["ok"])
        self.assertFalse(b.elements["cpg"].visible)      # reverted (Law 2)
        b.handle_post({"element": "cpg", "on": True})    # the deliberate flip
        self.assertTrue(b.elements["cpg"].visible)       # visible again
        self.assertEqual(b.elements["cpg"].state, VERIFYING)  # re-verification
        b.handle_post({"element": "cpg", "on": False})   # and off again
        self.assertFalse(b.elements["cpg"].visible)
        self.assertEqual(b.elements["cpg"].state, UNVERIFIED)

    def test_11_unknown_element_named_refusal(self):
        b = VisibilityBoard()
        r = b.handle_post({"element": "nope", "on": True})
        self.assertFalse(r["ok"])
        self.assertIn("unknown element", r["error"])

    def test_12_status_json_shape(self):
        b = VisibilityBoard()
        s = b.status()
        self.assertTrue(s["ok"])
        self.assertEqual({e["name"] for e in s["elements"]},
                         {"water", "cpg", "stride", "matter"})
        for e in s["elements"]:
            for k in ("visible", "state", "proven", "override", "plane",
                      "last_gate"):
                self.assertIn(k, e)


@unittest.skipUnless(HAVE_PIL, "PIL not importable: compose tests skipped (recorded)")
class ComposerTest(unittest.TestCase):
    """Nothing visible -> the engine's bytes are returned EXACTLY."""

    def test_13_invisible_board_leaves_glass_untouched(self):
        b = VisibilityBoard()
        base = tiny_png()
        out, drawn = compose(b, base)
        self.assertEqual(out, base)              # byte-identical
        self.assertEqual(drawn, [])

    def test_14_visible_element_draws_something(self):
        b = VisibilityBoard()
        b.handle_post({"element": "water", "on": True})
        b.elements["water"].snapshot = {"ok": True, "nc": 8, "vmax": 4,
                                        "vols": (4, 4, 4, 4, 0, 0, 0, 0)}
        out, drawn = compose(b, tiny_png())
        self.assertEqual(drawn, ["water"])
        self.assertNotEqual(out, tiny_png())     # pixels changed

    def test_15_proven_board_is_byte_identical_again(self):
        b = VisibilityBoard()
        b.handle_post({"element": "water", "on": True})
        el = b.elements["water"]
        el.snapshot = {"ok": True, "nc": 8, "vmax": 4,
                       "vols": (4, 4, 4, 4, 0, 0, 0, 0)}
        el.history = [{"sum": 5}, {"sum": 7}]
        base = tiny_png()
        out1, drawn1 = compose(b, base)
        self.assertEqual(drawn1, ["water"])
        el.snapshot = {"ok": True, "nc": 8, "vmax": 4,
                       "vols": (4, 4, 4, 4, 0, 0, 0, 0)}
        el.history = [{"sum": 5}, {"sum": 7}]
        el.run_gate()                            # prove it (motion seen)
        out2, drawn2 = compose(b, base)
        self.assertEqual(drawn2, [])
        self.assertEqual(out2, base)             # Law 2, in pixels


if __name__ == "__main__":
    unittest.main(verbosity=2)
