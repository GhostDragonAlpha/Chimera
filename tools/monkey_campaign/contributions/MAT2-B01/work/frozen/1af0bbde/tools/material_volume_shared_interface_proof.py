"""Shared-interface coupon proof (package 1 of the body-export proof battery).

Bounded export proof: two explicitly authored body groups sharing one internal
triangular interface export mass, COM, and full inertia equal to preregistered
analytic expectations, and the internal face contributes no material. This
proves nothing about anatomical correctness, mechanical qualification, or
dynamics readiness.

Preregistration (frozen before this suite executed):
  Chimera/docs/matter/material_volume_export_proof_prereg_shared_interface.md

Independence: oracles below are implemented in this file in pure Python and do
not reuse the exporter's moment algebra. Oracle Q (Hammer-Stroud 4-point
degree-3 quadrature) transforms vertices and integrates; the frozen literals
come from an exact rational hand derivation. The exporter's own centroid-
relative vertex moments and any tensor congruence are what these oracles pin.

Run: python tools/material_volume_shared_interface_proof.py
"""
from __future__ import annotations

import json
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import material_volume_body_export as exporter

ROOT = Path(__file__).resolve().parent

# Frozen tolerances (preregistration).
TOL = 1e-12
T_PROTECTED = 0.002

# Frozen fixture tables (preregistration; the fixture documents are validated
# against these).
CELLS = {"cell-upper": ("v0", "v1", "v2", "v3"),
         "cell-lower": ("v0", "v2", "v1", "v4")}
CELL_DENSITY = {"cell-upper": 12.0, "cell-lower": 6.0}
BODY_CELLS = {"si-body-A": "cell-upper", "si-body-B": "cell-lower"}
MATERIAL_BY_REGION = {"si-region-A": "si-tissue-A", "si-region-B": "si-tissue-B"}
DENSITY_BY_MATERIAL = {"si-tissue-A": 12.0, "si-tissue-B": 6.0}

# Frozen analytic expectations (exact rationals: masses 2 and 1; COMs
# (1/4,1/4,+-1/4); I_A = 3/20 diag, 1/40 off; I_B = 3/40 diag, +1/80 xy,
# -1/80 xz/yz; combined m=3, COM (1/4,1/4,1/12), I = [[47/120, 3/80, 1/80],
# [3/80, 47/120, 1/80], [1/80, 1/80, 9/40]]).
FROZEN = {
    "si-body-A": {
        "mass_kg": 2.0,
        "volume_m3": 0.16666666666666666,
        "com_m": [0.25, 0.25, 0.25],
        "inertia_kg_m2": [[0.15, 0.025, 0.025],
                          [0.025, 0.15, 0.025],
                          [0.025, 0.025, 0.15]]},
    "si-body-B": {
        "mass_kg": 1.0,
        "volume_m3": 0.16666666666666666,
        "com_m": [0.25, 0.25, -0.25],
        "inertia_kg_m2": [[0.075, 0.0125, -0.0125],
                          [0.0125, 0.075, -0.0125],
                          [-0.0125, -0.0125, 0.075]]},
    "combined": {
        "mass_kg": 3.0,
        "volume_m3": 0.3333333333333333,
        "com_m": [0.25, 0.25, 0.08333333333333333],
        "inertia_kg_m2": [[0.39166666666666666, 0.0375, 0.0125],
                          [0.0375, 0.39166666666666666, 0.0125],
                          [0.0125, 0.0125, 0.225]]},
    "interfaces": [{"face": ["v0", "v1", "v2"], "area_m2": 0.5}],
}


# --------------------------------------------------------------------------
# Oracle Q: Hammer-Stroud 4-point degree-3 tetrahedron quadrature (file-local,
# pure Python; irrational barycentric points; exact for degree <= 3).
# --------------------------------------------------------------------------

_HS_A = (5.0 + 3.0 * math.sqrt(5.0)) / 20.0
_HS_B = (5.0 - math.sqrt(5.0)) / 20.0
_HS_POINTS = (
    (_HS_A, _HS_B, _HS_B, _HS_B),
    (_HS_B, _HS_A, _HS_B, _HS_B),
    (_HS_B, _HS_B, _HS_A, _HS_B),
    (_HS_B, _HS_B, _HS_B, _HS_A),
)


def quadrature_tet_properties(points4, density):
    p0, p1, p2, p3 = points4
    e1 = [p1[k] - p0[k] for k in range(3)]
    e2 = [p2[k] - p0[k] for k in range(3)]
    e3 = [p3[k] - p0[k] for k in range(3)]
    cross = [e2[1] * e3[2] - e2[2] * e3[1],
             e2[2] * e3[0] - e2[0] * e3[2],
             e2[0] * e3[1] - e2[1] * e3[0]]
    det = sum(e1[k] * cross[k] for k in range(3))
    if det <= 0.0:
        raise AssertionError("fixture tet must be positively oriented")
    volume = det / 6.0
    mass = density * volume
    nodes = [[lam[0] * p0[k] + lam[1] * p1[k] + lam[2] * p2[k] + lam[3] * p3[k]
              for k in range(3)] for lam in _HS_POINTS]
    first = [mass * 0.25 * sum(x[a] for x in nodes) for a in range(3)]
    second = [[mass * 0.25 * sum(x[a] * x[b] for x in nodes) for b in range(3)]
              for a in range(3)]
    return {"mass": mass, "volume": volume, "first": first, "second": second}


def combine_raw(parts):
    """Total properties by summing raw moments (no parallel axis)."""
    mass = sum(p["mass"] for p in parts)
    first = [sum(p["first"][a] for p in parts) for a in range(3)]
    second = [[sum(p["second"][a][b] for p in parts) for b in range(3)]
              for a in range(3)]
    com = [first[a] / mass for a in range(3)]
    central = [[second[a][b] - mass * com[a] * com[b] for b in range(3)]
               for a in range(3)]
    trace = central[0][0] + central[1][1] + central[2][2]
    inertia = [[(trace if a == b else 0.0) - central[a][b] for b in range(3)]
               for a in range(3)]
    return {"mass_kg": mass, "volume_m3": sum(p["volume"] for p in parts),
            "com_m": com, "inertia_kg_m2": inertia}


# --------------------------------------------------------------------------
# Oracle A: face-adjacency interface facts (file-local, pure Python).
# --------------------------------------------------------------------------


def shared_face_facts(positions, cell_vertices):
    faces = {}
    for cell_id, vids in cell_vertices.items():
        for omit in range(4):
            key = tuple(sorted(v for i, v in enumerate(vids) if i != omit))
            faces.setdefault(key, []).append(cell_id)
    out = []
    for key in sorted(faces):
        if len(faces[key]) == 2:
            p = [positions[v] for v in key]
            e1 = [p[1][k] - p[0][k] for k in range(3)]
            e2 = [p[2][k] - p[0][k] for k in range(3)]
            cross = [e1[1] * e2[2] - e1[2] * e2[1],
                     e1[2] * e2[0] - e1[0] * e2[2],
                     e1[0] * e2[1] - e1[1] * e2[0]]
            area = 0.5 * math.sqrt(sum(c * c for c in cross))
            out.append({"face": list(key), "area_m2": area})
    return out


# --------------------------------------------------------------------------
# Recombination of exported body tensors (parallel axis, file-local).
# --------------------------------------------------------------------------


def recombine(bodies):
    mass = sum(b["mass_kg"] for b in bodies)
    com = [sum(b["mass_kg"] * b["com_m"][a] for b in bodies) / mass
           for a in range(3)]
    inertia = [[0.0] * 3 for _ in range(3)]
    for b in bodies:
        d = [b["com_m"][a] - com[a] for a in range(3)]
        dd = sum(x * x for x in d)
        for a in range(3):
            for c in range(3):
                inertia[a][c] += b["inertia_kg_m2"][a][c] + b["mass_kg"] * (
                    (dd if a == c else 0.0) - d[a] * d[c])
    return {"mass_kg": mass, "com_m": com, "inertia_kg_m2": inertia}


def load_fixtures():
    manifest = json.loads((ROOT / "material_volume_shared_interface_manifest_example.json")
                          .read_text(encoding="utf-8"))
    partition = json.loads((ROOT / "material_volume_shared_interface_partition_example.json")
                           .read_text(encoding="utf-8"))
    groups = json.loads((ROOT / "material_volume_shared_interface_groups_example.json")
                        .read_text(encoding="utf-8"))
    return manifest, partition, groups


def run_export():
    manifest, partition, groups = load_fixtures()
    return exporter.build_export_report(manifest, partition, groups)


def exported_group(report, body_id):
    return next(row for row in report["body_groups"] if row["body_id"] == body_id)


def body_values(row):
    props = row["mass_properties"]
    return {"mass_kg": props["mass"]["value"],
            "volume_m3": props["volume"]["value"],
            "com_m": list(props["center_of_mass"]["value"]),
            "inertia_kg_m2": [list(r) for r in
                              props["inertia_tensor_about_com"]["value"]]}


class SharedInterfaceCouponProof(unittest.TestCase):
    maxDiff = None

    def assert_close(self, observed, expected, label):
        self.assertLessEqual(abs(observed - expected), TOL,
                             f"{label}: observed {observed!r} vs expected {expected!r}")

    def assert_props_close(self, observed, expected, label):
        self.assert_close(observed["mass_kg"], expected["mass_kg"], label + " mass")
        self.assert_close(observed["volume_m3"], expected["volume_m3"], label + " volume")
        for a in range(3):
            self.assert_close(observed["com_m"][a], expected["com_m"][a],
                              f"{label} com[{a}]")
            for b in range(3):
                self.assert_close(observed["inertia_kg_m2"][a][b],
                                  expected["inertia_kg_m2"][a][b],
                                  f"{label} inertia[{a}][{b}]")

    def test_F1_exported_bodies_match_frozen_mass_com_and_inertia(self):
        report = run_export()
        self.assertEqual(report["export_status"], "complete")
        self.assertEqual(report["admission_status"], "validation_only_admissible")
        for body_id in ("si-body-A", "si-body-B"):
            row = exported_group(report, body_id)
            self.assertEqual(row["export_status"], "exported")
            self.assert_props_close(body_values(row), FROZEN[body_id], body_id)

    def test_F1_recombination_matches_partition_total(self):
        report = run_export()
        recombined = recombine([body_values(exported_group(report, b))
                                for b in ("si-body-A", "si-body-B")])
        expected = FROZEN["combined"]
        self.assert_close(recombined["mass_kg"], expected["mass_kg"], "recombined mass")
        for a in range(3):
            self.assert_close(recombined["com_m"][a], expected["com_m"][a],
                              f"recombined com[{a}]")
            for b in range(3):
                self.assert_close(recombined["inertia_kg_m2"][a][b],
                                  expected["inertia_kg_m2"][a][b],
                                  f"recombined inertia[{a}][{b}]")

    def test_F2_internal_interface_contributes_no_duplicate_material(self):
        manifest, partition, groups = load_fixtures()
        positions = {row["vertex_id"]: tuple(row["position"])
                     for row in partition["vertices"]}
        facts = shared_face_facts(positions, CELLS)
        self.assertEqual(facts, FROZEN["interfaces"])
        report = run_export()
        values = {b: body_values(exported_group(report, b))
                  for b in ("si-body-A", "si-body-B")}
        # Mass additivity through the shared face: no interface mass appears,
        # disappears, or is double-counted.
        self.assert_close(values["si-body-A"]["mass_kg"], 12.0 / 6.0, "body A rho*V")
        self.assert_close(values["si-body-B"]["mass_kg"], 6.0 / 6.0, "body B rho*V")
        self.assert_close(values["si-body-A"]["mass_kg"] + values["si-body-B"]["mass_kg"],
                          FROZEN["combined"]["mass_kg"], "sum of body masses")
        # Provenance flags: no membrane overlay and no source payloads.
        self.assertFalse(report["surface_mass_overlay_generated"])
        self.assertFalse(report["source_effective_segment_payloads_consumed"])
        for body_id, row in (("si-body-A", exported_group(report, "si-body-A")),
                             ("si-body-B", exported_group(report, "si-body-B"))):
            prov = row["material_mass_source_provenance"]
            self.assertFalse(prov["surface_mass_overlay_generated"], body_id)
            self.assertFalse(prov["surface_mass_overlay_consumed"], body_id)
            self.assertFalse(prov["source_effective_segment_payloads_consumed"], body_id)
            self.assertEqual(prov["mass_source_kind"], "reconstructed_material_volume",
                             body_id)

    def test_F4_off_diagonal_inertia_terms_retained(self):
        report = run_export()
        for body_id in ("si-body-A", "si-body-B"):
            row = exported_group(report, body_id)
            tensor = row["mass_properties"]["inertia_tensor_about_com"]
            self.assertTrue(tensor["full_symmetric_tensor"], body_id)
            self.assertTrue(tensor["off_diagonal_terms_preserved"], body_id)
            self.assertFalse(tensor["principal_axis_transform_applied"], body_id)
            value = tensor["value"]
            for a in range(3):
                for b in range(3):
                    self.assert_close(value[a][b], value[b][a], f"{body_id} symmetry")
            expected = FROZEN[body_id]["inertia_kg_m2"]
            for a in range(3):
                for b in range(3):
                    if a == b:
                        continue
                    if abs(expected[a][b]) > T_PROTECTED:
                        self.assertGreater(abs(value[a][b]), 1e-9,
                                           f"{body_id} off-diagonal [{a}][{b}] lost")
                        self.assertEqual(math.copysign(1.0, value[a][b]),
                                         math.copysign(1.0, expected[a][b]),
                                         f"{body_id} off-diagonal [{a}][{b}] sign")

    def test_F5_independent_quadrature_agrees_with_frozen_rationals(self):
        manifest, partition, groups = load_fixtures()
        positions = {row["vertex_id"]: tuple(row["position"])
                     for row in partition["vertices"]}
        # Fixture integrity: the frozen density table matches the documents.
        self.assertEqual({m["material_id"]: m["density_kg_m3"]
                          for m in partition["materials"]}, DENSITY_BY_MATERIAL)
        self.assertEqual({r["region_id"]: r["material_id"]
                          for r in partition["regions"]}, MATERIAL_BY_REGION)
        parts = []
        for cell_id, vids in CELLS.items():
            q = quadrature_tet_properties([positions[v] for v in vids],
                                          CELL_DENSITY[cell_id])
            parts.append(q)
            expected = FROZEN["si-body-A" if cell_id == "cell-upper" else "si-body-B"]
            observed = combine_raw([q])
            self.assert_props_close(observed, expected, f"quadrature {cell_id}")
        total = combine_raw(parts)
        self.assert_props_close(total, FROZEN["combined"], "quadrature combined")


def observed_values():
    report = run_export()
    out = {}
    for body_id in ("si-body-A", "si-body-B"):
        out[body_id] = body_values(exported_group(report, body_id))
    out["combined_recombined"] = recombine([out[b] for b in
                                            ("si-body-A", "si-body-B")])
    return out


if __name__ == "__main__":
    if "--dump-observed" in sys.argv:
        print(json.dumps(observed_values(), indent=2, sort_keys=True))
    else:
        unittest.main()
