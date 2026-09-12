"""Battery-0 tests: the definition format refuses and accepts correctly.
Run: python -m unittest tools.matter_kernel.test_definition"""
from __future__ import annotations

import json
import struct
import tempfile
import unittest
from pathlib import Path

from tools.matter_kernel import definition
from tools.matter_kernel.constants import MATERIALS, scratch_winner


def tri(p0, p1, p2) -> bytes:
    return struct.pack("<9f", *p0, *p1, *p2)


def valid_body() -> dict:
    return {
        "materials": {
            "mat.steel": MATERIALS["mat.steel_mild"],
            "mat.wood": MATERIALS["mat.oak"],
            "mat.glue": MATERIALS["mat.wood_glue"],
        },
        "membranes": [
            {"id": "mem.plateA", "material": "mat.steel",
             "triangles": tri((0, 0, 0), (1, 0, 0), (0, 1, 0)),
             "thickness": 0.01},
            {"id": "mem.plateB", "material": "mat.wood",
             "triangles": tri((0, 0, 1), (1, 0, 1), (0, 1, 1)) + tri((1, 0, 1), (1, 1, 1), (0, 1, 1)),
             "thickness": 0.02},
        ],
        "bonds": [
            {"id": "bond.seam", "material": "mat.glue",
             "members": ["mem.plateA", "mem.plateB"],
             "cure_strength": 30e6},
        ],
    }


class DefinitionTests(unittest.TestCase):
    def write(self, body: dict) -> str:
        d = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: [p.unlink() for p in d.iterdir()] and d.rmdir())
        # membranes reference sidecar triangle files (binary refs per spec)
        for i, mem in enumerate(body.get("membranes", [])):
            if isinstance(mem.get("triangles"), (bytes, bytearray)):
                side = d / f"tris{i}.bin"
                side.write_bytes(mem["triangles"])
                mem["triangles"] = side.name
        f = d / "body.json"
        f.write_text(json.dumps(body), encoding="utf-8")
        return str(f)

    def test_valid_body_parses_and_derives_mass(self):
        body = definition.parse_body(self.write(valid_body()))
        self.assertAlmostEqual(body["membranes"][0]["mass_derived"],
                               0.5 * 7850.0 * 0.01, places=6)
        self.assertAlmostEqual(body["membranes"][1]["mass_derived"],
                               2 * 0.5 * 700.0 * 0.02, places=6)

    def test_unknown_material_refused(self):
        body = valid_body()
        body["membranes"][0]["material"] = "mat.unobtanium"
        with self.assertRaisesRegex(definition.DefinitionError, "unknown material"):
            definition.parse_body(self.write(body))

    def test_missing_source_refused(self):
        body = valid_body()
        body["materials"]["mat.steel"] = {k: v for k, v in
                                          MATERIALS["mat.steel_mild"].items()
                                          if k != "source"}
        with self.assertRaisesRegex(definition.DefinitionError, "cite a source"):
            definition.parse_body(self.write(body))

    def test_bad_triangle_blob_refused(self):
        body = valid_body()
        body["membranes"][0]["triangles"] = b"\x00" * 20  # not a 36 multiple
        with self.assertRaisesRegex(definition.DefinitionError, "multiple of 36"):
            definition.parse_body(self.write(body))

    def test_bond_member_must_exist(self):
        body = valid_body()
        body["bonds"][0]["members"] = ["mem.plateA", "mem.ghost"]
        with self.assertRaisesRegex(definition.DefinitionError, "not a membrane"):
            definition.parse_body(self.write(body))

    def test_stated_mass_beyond_tolerance_refused(self):
        body = valid_body()
        body["membranes"][0]["mass"] = 999.0  # wildly wrong
        with self.assertRaisesRegex(definition.DefinitionError, "tolerance"):
            definition.parse_body(self.write(body))

    def test_stated_mass_within_tolerance_accepted(self):
        body = valid_body()
        good = 0.5 * 7850.0 * 0.01
        body["membranes"][0]["mass"] = good * 1.03  # 3%, inside 5%
        definition.parse_body(self.write(body))

    def test_scratch_law_winner_is_softer(self):
        self.assertEqual(scratch_winner("mat.steel_mild", "mat.oak"), "mat.oak")
        self.assertEqual(scratch_winner("mat.oak", "mat.steel_mild"), "mat.oak")
        self.assertEqual(scratch_winner("mat.glass_soda", "mat.rubber"), "mat.rubber")

    def test_duplicate_membrane_id_refused(self):
        body = valid_body()
        body["membranes"][1]["id"] = "mem.plateA"
        with self.assertRaisesRegex(definition.DefinitionError, "duplicate"):
            definition.parse_body(self.write(body))


if __name__ == "__main__":
    unittest.main()
