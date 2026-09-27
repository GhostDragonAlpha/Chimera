"""Frame-composition coupon proof (package 2 of the body-export proof battery).

Bounded export proof: two explicitly authored bodies under one authored parent
frame (with nonzero translations and nontrivial proper rotations) export mass,
COM, and full inertia equal to preregistered analytic expectations in the
authored frames, with off-diagonal inertia terms intact. Direct (pre-composed)
and composed (two-step chain) transformations agree with independent oracles.
This proves nothing about anatomical correctness, mechanical qualification, or
dynamics readiness.

Preregistration (frozen before this suite executed):
  Chimera/docs/matter/material_volume_export_proof_prereg_frame_composition.md

Independence: oracles below are implemented in this file in pure Python.
Oracle Q (Hammer-Stroud 4-point degree-3 quadrature) transforms *vertices*
into the target frame and integrates; it never applies a tensor congruence.
Oracle R2 applies the congruence to the frozen hand-derived domain rationals.
Agreement of Q with the exporter's R^T I R path is therefore not shared algebra.

Run: python tools/material_volume_frame_composition_proof.py
"""
from __future__ import annotations

import copy
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

# Frozen fixture tables (preregistration).
CELLS = {"fc-cell-A": ("a0", "a1", "a2", "a3"),
         "fc-cell-B": ("b0", "b1", "b2", "b3")}
CELL_DENSITY = {"fc-cell-A": 12.0, "fc-cell-B": 6.0}
BODY_CELLS = {"fc-body-A": "fc-cell-A", "fc-body-B": "fc-cell-B"}

# Frozen authored-frame chain (contract: x_domain = R * x_body + origin_m).
PARENT = {"R": [[0.8660254037844386, -0.5, 0.0],
                [0.5, 0.8660254037844386, 0.0],
                [0.0, 0.0, 1.0]],
          "t": [1.0, -2.0, 0.5]}
LOCAL_A = {"R": [[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]],
           "t": [0.5, 0.0, 0.25]}
LOCAL_B = {"R": [[0.0, 0.0, 1.0], [0.0, 1.0, 0.0], [-1.0, 0.0, 0.0]],
           "t": [0.0, 0.75, -0.5]}
COMPOSED_A = {"R": [[-0.5, -0.8660254037844386, 0.0],
                    [0.8660254037844386, -0.5, 0.0],
                    [0.0, 0.0, 1.0]],
              "t": [1.4330127018922192, -1.75, 0.75]}
COMPOSED_B = {"R": [[0.0, -0.5, 0.8660254037844386],
                    [0.0, 0.8660254037844386, 0.5],
                    [-1.0, 0.0, 0.0]],
              "t": [0.625, -1.350480947161671, 0.0]}

# Frozen domain expectations (hand-derived exact rationals).
FROZEN_DOMAIN = {
    "fc-cell-A": {
        "mass_kg": 2.0,
        "volume_m3": 0.16666666666666666,
        "com_m": [0.25, 0.25, 0.25],
        "inertia_kg_m2": [[0.15, 0.025, 0.025],
                          [0.025, 0.15, 0.025],
                          [0.025, 0.025, 0.15]]},
    "fc-cell-B": {
        "mass_kg": 1.0,
        "volume_m3": 0.16666666666666666,
        "com_m": [2.25, -0.75, 0.75],
        "inertia_kg_m2": [[0.075, 0.0125, 0.0125],
                          [0.0125, 0.075, 0.0125],
                          [0.0125, 0.0125, 0.075]]},
    "combined": {
        "mass_kg": 3.0,
        "com_m": [0.9166666666666666, -0.08333333333333333, 0.4166666666666667],
        "inertia_kg_m2": [[1.0583333333333333, 1.3708333333333333, -0.6291666666666667],
                          [1.3708333333333333, 3.058333333333333, 0.37083333333333335],
                          [-0.6291666666666667, 0.37083333333333335, 3.558333333333333]]},
}

# Frozen run expectations (route 1: vertex transform + quadrature; decimals).
FROZEN_RUNS = {
    "shared": {
        "fc-body-A": {
            "mass_kg": 2.0,
            "volume_m3": 0.16666666666666666,
            "com_m": [0.4754809471616711, 2.323557158514987, -0.25],
            "inertia_kg_m2": [[0.17165063509461018, 0.012500000000000178, 0.03415063509461097],
                              [0.012500000000000178, 0.12834936490538898, 0.009150635094610893],
                              [0.03415063509461097, 0.009150635094610893, 0.14999999999999908]]},
        "fc-body-B": {
            "mass_kg": 1.0,
            "volume_m3": 0.16666666666666666,
            "com_m": [1.7075317547305482, 0.45753175473054825, 0.25],
            "inertia_kg_m2": [[0.0858253175473055, 0.006249999999999978, 0.017075317547305402],
                              [0.006249999999999978, 0.06417468245269468, 0.004575317547305488],
                              [0.017075317547305402, 0.004575317547305488, 0.07500000000000015]]},
    },
    "composed": {
        "fc-body-A": {
            "mass_kg": 2.0,
            "volume_m3": 0.16666666666666666,
            "com_m": [2.323557158514987, 0.02451905283832875, -0.5],
            "inertia_kg_m2": [[0.128349364905389, -0.012499999999999997, 0.00915063509461067],
                              [-0.012499999999999997, 0.1716506350946101, -0.03415063509461097],
                              [0.00915063509461067, -0.03415063509461097, 0.1499999999999992]]},
        "fc-body-B": {
            "mass_kg": 1.0,
            "volume_m3": 0.16666666666666666,
            "com_m": [-0.75, -0.29246824526945175, 1.7075317547305482],
            "inertia_kg_m2": [[0.07500000000000019, -0.004575317547305502, -0.017075317547305513],
                              [-0.004575317547305502, 0.06417468245269464, 0.006250000000000033],
                              [-0.017075317547305513, 0.006250000000000033, 0.0858253175473055]]},
    },
}


# --------------------------------------------------------------------------
# Pure-Python linear algebra (file-local).
# --------------------------------------------------------------------------


def mat_vec(a, v):
    return tuple(sum(a[i][k] * v[k] for k in range(3)) for i in range(3))


def mat_mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)]
            for i in range(3)]


def mat_t(a):
    return [[a[j][i] for j in range(3)] for i in range(3)]


def vsub(a, b):
    return tuple(a[k] - b[k] for k in range(3))


def transform_points_single(frame, points):
    """x_body = R^T (x_domain - origin)."""
    rt = mat_t(frame["R"])
    return [mat_vec(rt, vsub(p, frame["t"])) for p in points]


def transform_points_chain(parent, local, points):
    """Two-step chain: domain -> parent -> body-local (composed alternative)."""
    parent_coords = transform_points_single(parent, points)
    return transform_points_single(local, parent_coords)


def congruence_props(frame, domain_props):
    """Oracle R2: c_body = R^T (c - t), I_body = R^T I R on reference values."""
    rt = mat_t(frame["R"])
    com = mat_vec(rt, vsub(domain_props["com_m"], frame["t"]))
    inertia = mat_mul(mat_mul(rt, domain_props["inertia_kg_m2"]), frame["R"])
    return {"mass_kg": domain_props["mass_kg"],
            "volume_m3": domain_props["volume_m3"],
            "com_m": list(com),
            "inertia_kg_m2": inertia}


# --------------------------------------------------------------------------
# Oracle Q: Hammer-Stroud 4-point degree-3 quadrature (file-local, pure
# Python; irrational barycentric points; exact for degree <= 3).
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
        raise AssertionError("fixture tet must stay positively oriented in frame")
    volume = det / 6.0
    mass = density * volume
    nodes = [[lam[0] * p0[k] + lam[1] * p1[k] + lam[2] * p2[k] + lam[3] * p3[k]
              for k in range(3)] for lam in _HS_POINTS]
    first = [mass * 0.25 * sum(x[a] for x in nodes) for a in range(3)]
    second = [[mass * 0.25 * sum(x[a] * x[b] for x in nodes) for b in range(3)]
              for a in range(3)]
    com = [first[a] / mass for a in range(3)]
    central = [[second[a][b] - mass * com[a] * com[b] for b in range(3)]
               for a in range(3)]
    trace = central[0][0] + central[1][1] + central[2][2]
    inertia = [[(trace if a == b else 0.0) - central[a][b] for b in range(3)]
               for a in range(3)]
    return {"mass_kg": mass, "volume_m3": volume,
            "com_m": com, "inertia_kg_m2": inertia}


def load_fixtures(groups_name):
    manifest = json.loads(
        (ROOT / "material_volume_frame_composition_manifest_example.json")
        .read_text(encoding="utf-8"))
    partition = json.loads(
        (ROOT / "material_volume_frame_composition_partition_example.json")
        .read_text(encoding="utf-8"))
    groups = json.loads((ROOT / groups_name).read_text(encoding="utf-8"))
    return manifest, partition, groups


def run_export(groups_name):
    manifest, partition, groups = load_fixtures(groups_name)
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


class FrameCompositionCouponProof(unittest.TestCase):
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

    def run_values(self, groups_name):
        report = run_export(groups_name)
        self.assertEqual(report["export_status"], "complete")
        self.assertEqual(report["admission_status"], "validation_only_admissible")
        return {body_id: body_values(exported_group(report, body_id))
                for body_id in ("fc-body-A", "fc-body-B")}

    def test_F1_run_masses_match_frozen(self):
        for run, groups_name in (
                ("shared", "material_volume_frame_composition_groups_shared_example.json"),
                ("composed", "material_volume_frame_composition_groups_composed_example.json")):
            values = self.run_values(groups_name)
            for body_id in ("fc-body-A", "fc-body-B"):
                self.assert_close(values[body_id]["mass_kg"],
                                  FROZEN_RUNS[run][body_id]["mass_kg"],
                                  f"{run} {body_id} mass")

    def test_F3_shared_run_com_and_full_inertia_match_frozen(self):
        values = self.run_values(
            "material_volume_frame_composition_groups_shared_example.json")
        for body_id in ("fc-body-A", "fc-body-B"):
            self.assert_props_close(values[body_id], FROZEN_RUNS["shared"][body_id],
                                    f"shared {body_id}")

    def test_F3_composed_run_com_and_full_inertia_match_frozen(self):
        values = self.run_values(
            "material_volume_frame_composition_groups_composed_example.json")
        for body_id in ("fc-body-A", "fc-body-B"):
            self.assert_props_close(values[body_id], FROZEN_RUNS["composed"][body_id],
                                    f"composed {body_id}")

    def test_F3_direct_and_composed_oracle_routes_agree(self):
        # The frozen fixture matrices really are the composed products.
        for local, composed in ((LOCAL_A, COMPOSED_A), (LOCAL_B, COMPOSED_B)):
            product_r = mat_mul(PARENT["R"], local["R"])
            product_t = list(mat_vec(PARENT["R"], local["t"]))
            for i in range(3):
                for j in range(3):
                    self.assert_close(product_r[i][j], composed["R"][i][j],
                                      f"composed rotation [{i}][{j}]")
                self.assert_close(product_t[i] + PARENT["t"][i], composed["t"][i],
                                  f"composed origin [{i}]")
        manifest, partition, groups = load_fixtures(
            "material_volume_frame_composition_groups_composed_example.json")
        positions = {row["vertex_id"]: tuple(row["position"])
                     for row in partition["vertices"]}
        for body_id, cell_id, local, composed in (
                ("fc-body-A", "fc-cell-A", LOCAL_A, COMPOSED_A),
                ("fc-body-B", "fc-cell-B", LOCAL_B, COMPOSED_B)):
            points = [positions[v] for v in CELLS[cell_id]]
            direct = quadrature_tet_properties(
                transform_points_single(composed, points), CELL_DENSITY[cell_id])
            composed_q = quadrature_tet_properties(
                transform_points_chain(PARENT, local, points),
                CELL_DENSITY[cell_id])
            route2 = congruence_props(composed, FROZEN_DOMAIN[cell_id])
            self.assert_props_close(direct, composed_q,
                                    f"{body_id} direct vs composed chain")
            self.assert_props_close(direct, route2,
                                    f"{body_id} direct vs congruence route")
            self.assert_props_close(direct, FROZEN_RUNS["composed"][body_id],
                                    f"{body_id} direct vs frozen")

    def test_F3_cross_run_domain_recovery_matches_frozen(self):
        frames = {"shared": {"fc-body-A": PARENT, "fc-body-B": PARENT},
                  "composed": {"fc-body-A": COMPOSED_A, "fc-body-B": COMPOSED_B}}
        recovered = {}
        for run, groups_name in (
                ("shared", "material_volume_frame_composition_groups_shared_example.json"),
                ("composed", "material_volume_frame_composition_groups_composed_example.json")):
            values = self.run_values(groups_name)
            for body_id in ("fc-body-A", "fc-body-B"):
                frame = frames[run][body_id]
                com_domain = list(mat_vec(frame["R"], values[body_id]["com_m"]))
                com_domain = [com_domain[k] + frame["t"][k] for k in range(3)]
                inertia_domain = mat_mul(
                    mat_mul(frame["R"], values[body_id]["inertia_kg_m2"]),
                    mat_t(frame["R"]))
                recovered.setdefault(body_id, []).append(
                    {"mass_kg": values[body_id]["mass_kg"],
                     "volume_m3": values[body_id]["volume_m3"],
                     "com_m": com_domain,
                     "inertia_kg_m2": inertia_domain})
        for body_id, cell_id in (("fc-body-A", "fc-cell-A"),
                                 ("fc-body-B", "fc-cell-B")):
            from_shared, from_composed = recovered[body_id]
            self.assert_props_close(from_shared, from_composed,
                                    f"{body_id} cross-run domain recovery")
            self.assert_props_close(from_shared, FROZEN_DOMAIN[cell_id],
                                    f"{body_id} recovered domain")

    def test_F4_off_diagonal_inertia_terms_retained(self):
        for run, groups_name in (
                ("shared", "material_volume_frame_composition_groups_shared_example.json"),
                ("composed", "material_volume_frame_composition_groups_composed_example.json")):
            report = run_export(groups_name)
            for body_id in ("fc-body-A", "fc-body-B"):
                row = exported_group(report, body_id)
                tensor = row["mass_properties"]["inertia_tensor_about_com"]
                self.assertTrue(tensor["full_symmetric_tensor"], body_id)
                self.assertTrue(tensor["off_diagonal_terms_preserved"], body_id)
                self.assertFalse(tensor["principal_axis_transform_applied"], body_id)
                value = tensor["value"]
                expected = FROZEN_RUNS[run][body_id]["inertia_kg_m2"]
                for a in range(3):
                    for b in range(3):
                        self.assert_close(value[a][b], value[b][a],
                                          f"{run} {body_id} symmetry")
                        if a == b:
                            continue
                        if abs(expected[a][b]) > T_PROTECTED:
                            self.assertGreater(abs(value[a][b]), 1e-9,
                                               f"{run} {body_id} off-diagonal "
                                               f"[{a}][{b}] lost")
                            self.assertEqual(math.copysign(1.0, value[a][b]),
                                             math.copysign(1.0, expected[a][b]),
                                             f"{run} {body_id} off-diagonal "
                                             f"[{a}][{b}] sign")

    def test_F5_independent_quadrature_agrees_with_frozen_domain(self):
        manifest, partition, groups = load_fixtures(
            "material_volume_frame_composition_groups_shared_example.json")
        positions = {row["vertex_id"]: tuple(row["position"])
                     for row in partition["vertices"]}
        for cell_id in ("fc-cell-A", "fc-cell-B"):
            q = quadrature_tet_properties([positions[v] for v in CELLS[cell_id]],
                                          CELL_DENSITY[cell_id])
            self.assert_props_close(q, FROZEN_DOMAIN[cell_id],
                                    f"quadrature domain {cell_id}")

    def test_F7_schema_blocker_parent_composition_not_silently_extended(self):
        schema = json.loads((ROOT / "material_volume_body_export_schema.json")
                            .read_text(encoding="utf-8"))
        body_frame = schema["$defs"]["bodyFrame"]["properties"]
        self.assertEqual(set(body_frame), {"frame_id", "handedness",
                                           "coordinate_unit", "domain_from_body"})
        self.assertEqual(set(body_frame["domain_from_body"]["properties"]),
                         {"rotation", "origin_m"})
        # The architectural blocker stands while v1 is flat: any parent or
        # composition field must fail loudly instead of being accepted.
        manifest, partition, groups = load_fixtures(
            "material_volume_frame_composition_groups_composed_example.json")
        smuggled = copy.deepcopy(groups)
        smuggled["body_groups"][0]["body_frame"]["parent_frame"] = {
            "frame_id": "fc-parent-P",
            "domain_from_parent": {"rotation": PARENT["R"], "origin_m": PARENT["t"]}}
        report = exporter.build_export_report(manifest, partition, smuggled)
        self.assertEqual(report["export_status"], "refused")
        self.assertEqual(report["reason_codes"], ["bad_schema"])
        self.assertIn("parent_frame", report["detail"])
        self.assertEqual(report["body_groups"], [])


def observed_values():
    out = {}
    for run, groups_name in (
            ("shared", "material_volume_frame_composition_groups_shared_example.json"),
            ("composed", "material_volume_frame_composition_groups_composed_example.json")):
        report = run_export(groups_name)
        out[run] = {body_id: body_values(exported_group(report, body_id))
                    for body_id in ("fc-body-A", "fc-body-B")}
    return out


if __name__ == "__main__":
    if "--dump-observed" in sys.argv:
        print(json.dumps(observed_values(), indent=2, sort_keys=True))
    else:
        unittest.main()
