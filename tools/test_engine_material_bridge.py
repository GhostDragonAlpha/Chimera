"""test_engine_material_bridge.py -- the material_iface first-consumer tests.

Run from the checkout root:  python -B -m unittest tools.test_engine_material_bridge -v
(or directly: python -B tools/test_engine_material_bridge.py)

No physics claim: these tests prove the PARAMETER PATH (validation, units,
provenance labeling, canonical payload, engine-constant parity at the
float32 bit level). Runtime qualification of the engine tick is the native
gate's receipt, not this file.
"""
from __future__ import annotations

import json
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.engine_material_bridge as bridge  # noqa: E402
from tools.material_iface.parameters import ParameterRefusal  # noqa: E402
from tools.material_iface.units import Quantity  # noqa: E402

PAYLOAD_PATH = (ROOT / "tools" / "monkey_campaign" / "engine_wiring_gate" /
                "engine_material_payload.json")


class EngineMaterialBridgeTest(unittest.TestCase):
    def test_preset_builds_through_the_validated_path(self):
        preset = bridge.build_preset()
        self.assertEqual(preset.model_id, bridge.ENGINE_MODEL_ID)
        self.assertEqual(
            tuple(sorted(preset.values.values)),
            ("press_falloff_radius_m", "sigma_n_per_m",
             "stress_relaxation_time_s"))
        # Values came through ParameterSet validation, unit-tagged.
        self.assertEqual(preset.values.quantity("sigma_n_per_m"),
                         Quantity(4000.0, "N/m"))
        self.assertEqual(preset.values.quantity("press_falloff_radius_m"),
                         Quantity(0.03, "m"))
        self.assertEqual(preset.values.quantity("stress_relaxation_time_s"),
                         Quantity(0.5, "s"))

    def test_provenance_is_auto_labeled_synthetic_with_citations_kept(self):
        # Two distinct source identities (the Yamada-derived working tension
        # and relaxation vs the engine-declared geometric scale) -> the
        # material_iface auto-labeling law refuses "measured" and labels the
        # preset SYNTHETIC while preserving every citation. Relabeling it
        # measured without a single measured source must stay impossible.
        preset = bridge.build_preset()
        self.assertEqual(preset.kind, "synthetic")
        self.assertEqual(
            preset.provenance.citation,
            "synthetic combination of ['engine.membrane.derivation', "
            "'engine.membrane.design']")
        # Every per-parameter citation survives in the note (auditable,
        # never absorbed).
        self.assertIn("Yamada", preset.provenance.note)
        self.assertIn("declared geometric scale", preset.provenance.note)

    def test_payload_values_bit_match_engine_constants(self):
        payload = bridge.emit_payload()
        for name, pin in bridge.ENGINE_CONSTANTS.items():
            emitted = payload["parameters"][name]["value"]
            parsed = float.fromhex(emitted)
            bits_emitted = struct.pack("<f", parsed)
            bits_compiled = struct.pack("<f", pin["value_f32"])
            self.assertEqual(
                bits_emitted, bits_compiled,
                f"{name}: payload {emitted!r} does not bit-match the "
                f"compiled engine constant ({pin['pin']})")

    def test_committed_payload_is_current_and_canonical(self):
        # The payload the native gate consumes must be exactly the bridge's
        # canonical output (drift on either side refuses).
        committed = PAYLOAD_PATH.read_bytes()
        self.assertEqual(committed, bridge.canonical_payload_bytes())
        parsed = json.loads(committed)
        self.assertEqual(parsed["schema"], bridge.SCHEMA)
        self.assertEqual(parsed["preset_kind"], "synthetic")

    def test_refusals(self):
        preset = bridge.build_preset()
        with self.assertRaises(ParameterRefusal):
            preset.values.quantity("no_such_parameter")
        with self.assertRaises(ParameterRefusal):
            bridge.ENGINE_SKIN_MODEL.meta("sigma_n_per_m").accept(
                Quantity(4000.0, "kN/m"))  # stiffness family, wrong unit


if __name__ == "__main__":
    unittest.main(verbosity=2)
