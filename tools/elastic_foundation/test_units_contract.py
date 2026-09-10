"""Tests for the proposed elastic-physical-cpu/v1 boundary.

Standalone evidence run:
  $env:CHIMERA_UNITS_REPO='E:/ChimeraWork/slot-03'
  $env:CHIMERA_UNITS_CANDIDATE='<this-dir>/PROPOSED_units_contract.py'
  python PROPOSED_test_units_contract.py -v

After paste-back as tools/elastic_foundation/units_contract.py, the environment
variables are unnecessary and normal package discovery imports the same code.
"""
from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
import hashlib
import importlib.util
import math
import os
from pathlib import Path
import sys
import unittest
from unittest import mock

import numpy as np


REPO = Path(os.environ.get("CHIMERA_UNITS_REPO", Path(__file__).resolve().parents[2]))
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tools.elastic_foundation.geometry import build_rest_geometry  # noqa: E402
from tools.elastic_foundation.law import evaluate_elastic  # noqa: E402
from tools.elastic_foundation.materials import synthetic  # noqa: E402


candidate = os.environ.get("CHIMERA_UNITS_CANDIDATE")
if candidate:
    module_name = "tools.elastic_foundation._units_contract_v1_proposal"
    spec = importlib.util.spec_from_file_location(module_name, candidate)
    U = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = U
    assert spec.loader is not None
    spec.loader.exec_module(U)
else:
    from tools.elastic_foundation import units_contract as U  # type: ignore


EPS64 = 2.0 ** -52
GAMMA64 = (64.0 * EPS64) / (1.0 - 64.0 * EPS64)


def _fraction_array(rows):
    return np.asarray(
        [[float(x) if isinstance(x, Fraction) else float(x) for x in row] for row in rows],
        dtype=np.float64,
    )


ORACLE_ENERGY_J = float(Fraction(713, 22750))
ORACLE_WVOL_J_PER_M3 = np.array([float(Fraction(2852, 91))])
ORACLE_VERTEX_N = _fraction_array(
    [
        [Fraction(498, 2275), Fraction(-228, 2275), 0],
        [Fraction(-498, 2275), 0, 0],
        [0, Fraction(228, 2275), 0],
    ]
)


class UnitsContractV1Tests(unittest.TestCase):
    def setUp(self):
        self.rest_pos = np.array(
            [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
            dtype=np.float64,
        )
        self.faces = np.array([[0, 1, 2]], dtype=np.int64)
        self.rest = build_rest_geometry(self.rest_pos, self.faces)
        self.current = np.array(
            [[0.0, 0.0, 0.0], [6.0 / 5.0, 0.0, 0.0], [0.0, 4.0 / 5.0, 0.0]],
            dtype=np.float64,
        )
        self.synthetic_provenance = U.SyntheticCoefficientProvenance(
            declaration_id="elastic-units-v1-rational-oracle",
            purpose="dimension-only CPU contract test",
        )

    def assertDerivedClose(self, actual, expected, message=""):
        actual = np.asarray(actual, dtype=np.float64)
        expected = np.asarray(expected, dtype=np.float64)
        self.assertEqual(actual.shape, expected.shape, message)
        nonzero = np.abs(expected.reshape(-1)[np.nonzero(expected.reshape(-1))])
        if not nonzero.size:
            self.assertTrue(
                np.array_equal(actual, expected),
                f"{message}: an all-zero oracle requires exact zero output",
            )
            return
        zero_scale = float(np.max(nonzero))
        scale = np.where(expected == 0.0, zero_scale, np.abs(expected))
        error = np.abs(actual - expected)
        self.assertTrue(
            np.all(error <= GAMMA64 * scale),
            f"{message}: max error {float(np.max(error))} exceeds derived "
            f"gamma(64) component budget {float(np.max(GAMMA64 * scale))}",
        )

    def volumetric(self, thickness=1.0 / 500.0):
        return U.admit_volumetric_v1(
            1000.0,
            thickness,
            3.0 / 10.0,
            provenance=self.synthetic_provenance,
        )

    def evaluate(self, material=None):
        return U.evaluate_physical_v1(
            self.rest, material or self.volumetric(), self.current
        )

    def assertRationalOracle(self, result):
        self.assertDerivedClose(result.energy_j, ORACLE_ENERGY_J, "U [J]")
        self.assertDerivedClose(result.vertex_forces_n, ORACLE_VERTEX_N, "vertex force [N]")
        self.assertDerivedClose(
            result.corner_forces_n, ORACLE_VERTEX_N[None, :, :], "corner force [N]"
        )
        self.assertDerivedClose(
            result.volume_energy_j_per_m3,
            ORACLE_WVOL_J_PER_M3,
            "w_vol [J/m3]",
        )
        # A0=1/2 exactly, hence Wbar=2U for this one-face fixture.
        self.assertDerivedClose(
            result.surface_energy_j_per_m2,
            np.array([2.0 * ORACLE_ENERGY_J]),
            "Wbar [J/m2]",
        )

    def test_nonunit_thickness_full_closed_form_oracle(self):
        result = self.evaluate()
        self.assertRationalOracle(result)
        self.assertEqual(result.material.input_modulus_unit, "Pa")
        self.assertEqual(result.material.surface_young_modulus_n_per_m, 2.0)
        self.assertEqual(result.material.thickness_m, 1.0 / 500.0)
        self.assertDerivedClose(
            result.material.lambda_surface_n_per_m, float(Fraction(60, 91)), "lambda2 [N/m]"
        )
        self.assertDerivedClose(
            result.material.mu_surface_n_per_m, float(Fraction(10, 13)), "mu2 [N/m]"
        )
        self.assertDerivedClose(
            result.material.bulk_surface_n_per_m, float(Fraction(130, 91)),
            "lambda2+mu2 [N/m]",
        )
        self.assertIs(result.material.provenance, self.synthetic_provenance)

    def test_volumetric_and_explicit_surface_representations_are_identical(self):
        volumetric = self.volumetric()
        surface = U.admit_surface_v1(
            volumetric.surface_young_modulus_n_per_m,
            volumetric.thickness_m,
            volumetric.poisson_ratio,
            provenance=self.synthetic_provenance,
        )
        a = self.evaluate(volumetric)
        b = self.evaluate(surface)
        self.assertEqual(surface.input_modulus_unit, "N/m")
        self.assertEqual(surface.representation, "explicit_surface_E2")
        for field in ("energy", "max_abs_vertex_force", "energy_scale"):
            self.assertEqual(getattr(a.evaluation, field), getattr(b.evaluation, field))
        for field in ("corner_forces", "vertex_forces"):
            self.assertTrue(
                np.array_equal(getattr(a.evaluation, field), getattr(b.evaluation, field)), field
            )
        for field in (
            "F", "C", "E", "S", "P", "Wbar", "w_vol", "detF", "area_cur",
            "inverted", "normals_cur",
        ):
            self.assertTrue(
                np.array_equal(
                    getattr(a.evaluation.per_face, field),
                    getattr(b.evaluation.per_face, field),
                ),
                field,
            )

    def test_thickness_occurs_once_in_full_outputs(self):
        a = self.evaluate(self.volumetric(1.0 / 500.0))
        b = self.evaluate(self.volumetric(1.0 / 250.0))
        for field in ("energy", "max_abs_vertex_force", "energy_scale"):
            self.assertDerivedClose(
                getattr(b.evaluation, field), 2.0 * getattr(a.evaluation, field), field
            )
        for field in ("corner_forces", "vertex_forces"):
            self.assertDerivedClose(
                getattr(b.evaluation, field), 2.0 * getattr(a.evaluation, field), field
            )
        for field in ("S", "P", "Wbar"):
            self.assertDerivedClose(
                getattr(b.evaluation.per_face, field),
                2.0 * getattr(a.evaluation.per_face, field),
                field,
            )
        self.assertDerivedClose(
            b.volume_energy_j_per_m3, a.volume_energy_j_per_m3, "w_vol"
        )
        for field in ("F", "C", "E", "detF", "area_cur", "inverted", "normals_cur"):
            self.assertTrue(
                np.array_equal(
                    getattr(a.evaluation.per_face, field),
                    getattr(b.evaluation.per_face, field),
                ),
                field,
            )

    def test_sourced_provenance_is_structured_and_retained_without_certifying_it(self):
        source = U.SourceReference
        provenance = U.SourcedCoefficientProvenance(
            modulus=source("doi:example-modulus", "Table 2, E column"),
            poisson_ratio=source("doi:example-poisson", "Table 1, nu row"),
            thickness=source("repo:synthetic-coupon", "coupon-7 thickness_m"),
        )
        admitted = U.admit_surface_v1(2.0, 1.0 / 500.0, 0.3, provenance=provenance)
        result = self.evaluate(admitted)
        self.assertIs(result.material, admitted)
        self.assertIs(result.material.provenance, provenance)
        self.assertEqual(result.material.provenance.modulus.locator, "Table 2, E column")

    def assertReason(self, reason, call):
        with self.assertRaises(U.UnitsRefusal) as caught:
            call()
        self.assertEqual(caught.exception.reason, reason)

    def test_named_input_and_provenance_refusals(self):
        p = self.synthetic_provenance
        cases = (
            (U.UnitsReason.NUMERIC_MATERIAL_REQUIRED,
             lambda: U.admit_volumetric_v1(True, 0.002, 0.3, provenance=p)),
            (U.UnitsReason.NUMERIC_MATERIAL_REQUIRED,
             lambda: U.admit_volumetric_v1("1000", 0.002, 0.3, provenance=p)),
            (U.UnitsReason.NONFINITE_MATERIAL,
             lambda: U.admit_volumetric_v1(math.inf, 0.002, 0.3, provenance=p)),
            (U.UnitsReason.NONFINITE_MATERIAL,
             lambda: U.admit_volumetric_v1(1000, math.nan, 0.3, provenance=p)),
            (U.UnitsReason.NONPOSITIVE_YOUNG_MODULUS,
             lambda: U.admit_volumetric_v1(0.0, 0.002, 0.3, provenance=p)),
            (U.UnitsReason.NONPOSITIVE_SURFACE_MODULUS,
             lambda: U.admit_surface_v1(0.0, 0.002, 0.3, provenance=p)),
            (U.UnitsReason.NONPOSITIVE_THICKNESS,
             lambda: U.admit_volumetric_v1(1000, 0.0, 0.3, provenance=p)),
            (U.UnitsReason.POISSON_OUT_OF_RANGE,
             lambda: U.admit_volumetric_v1(1000, 0.002, -1.0, provenance=p)),
            (U.UnitsReason.POISSON_OUT_OF_RANGE,
             lambda: U.admit_volumetric_v1(1000, 0.002, 0.5, provenance=p)),
            (U.UnitsReason.STRUCTURED_PROVENANCE_REQUIRED,
             lambda: U.admit_volumetric_v1(1000, 0.002, 0.3,
                                            provenance={"kind": "sourced"})),
            (U.UnitsReason.STRUCTURED_PROVENANCE_REQUIRED,
             lambda: U.admit_volumetric_v1(1000, 0.002, 0.3)),
            (U.UnitsReason.STRUCTURED_PROVENANCE_REQUIRED,
             lambda: U.SourceReference("", "Table 1")),
            (U.UnitsReason.MATERIAL_NOT_ADMITTED,
             lambda: U.evaluate_physical_v1(
                 self.rest, synthetic(E=2.0, nu=0.3, h=0.002), self.current)),
        )
        for reason, call in cases:
            with self.subTest(reason=reason):
                self.assertReason(reason, call)

    def test_named_product_lame_and_precision_refusals(self):
        p = self.synthetic_provenance
        min_subnormal = math.ulp(0.0)
        cases = (
            (U.UnitsReason.SURFACE_MODULUS_OVERFLOW,
             lambda: U.admit_volumetric_v1(sys.float_info.max, 2.0, 0.3,
                                            provenance=p)),
            (U.UnitsReason.SURFACE_MODULUS_UNDERFLOW,
             lambda: U.admit_volumetric_v1(min_subnormal, 0.5, 0.3,
                                            provenance=p)),
            (U.UnitsReason.LAME_COEFFICIENT_OVERFLOW,
             lambda: U.admit_surface_v1(sys.float_info.max, 1.0,
                                        math.nextafter(-1.0, 0.0), provenance=p)),
            (U.UnitsReason.LAME_COEFFICIENT_UNDERFLOW,
             lambda: U.admit_surface_v1(min_subnormal, 1.0, 0.25,
                                        provenance=p)),
            (U.UnitsReason.LAME_COEFFICIENT_UNDERFLOW,
             lambda: U.admit_surface_v1(1.0, 1.0, min_subnormal,
                                        provenance=p)),
            (U.UnitsReason.LAME_PRECISION_LOSS,
             lambda: U.admit_surface_v1(1.0, 1.0,
                                        math.nextafter(-1.0, 0.0), provenance=p)),
        )
        for reason, call in cases:
            with self.subTest(reason=reason):
                self.assertReason(reason, call)

    def test_direct_construction_is_refused(self):
        m = self.volumetric()
        kwargs = {
            name: getattr(m, name)
            for name in (
                "representation", "input_modulus_value", "input_modulus_unit",
                "thickness_m", "poisson_ratio", "surface_young_modulus_n_per_m",
                "lambda_surface_n_per_m", "mu_surface_n_per_m",
                "bulk_surface_n_per_m", "provenance", "contract_version",
            )
        }
        self.assertReason(
            U.UnitsReason.DIRECT_CONSTRUCTION_FORBIDDEN,
            lambda: U.AdmittedMaterialV1(**kwargs),
        )

    def test_output_nonfinite_shape_and_wrong_volume_density_refuse(self):
        admitted = self.volumetric()
        good = self.evaluate(admitted).evaluation

        bad_nonfinite = replace(good, energy=math.nan)
        with mock.patch.object(U, "_evaluate_kernel", return_value=bad_nonfinite):
            self.assertReason(
                U.UnitsReason.OUTPUT_NONFINITE,
                lambda: self.evaluate(admitted),
            )

        bad_shape = replace(good, vertex_forces=good.vertex_forces[:-1])
        with mock.patch.object(U, "_evaluate_kernel", return_value=bad_shape):
            self.assertReason(
                U.UnitsReason.OUTPUT_MALFORMED,
                lambda: self.evaluate(admitted),
            )

        wrong_face = replace(
            good.per_face, w_vol=np.zeros_like(good.per_face.w_vol)
        )
        wrong_wvol = replace(good, per_face=wrong_face)
        with mock.patch.object(U, "_evaluate_kernel", return_value=wrong_wvol):
            self.assertReason(
                U.UnitsReason.OUTPUT_DIMENSION_MISMATCH,
                lambda: self.evaluate(admitted),
            )

        missing_face = replace(good, per_face=None)
        with mock.patch.object(U, "_evaluate_kernel", return_value=missing_face):
            self.assertReason(
                U.UnitsReason.OUTPUT_MALFORMED,
                lambda: self.evaluate(admitted),
            )

        # Every supplied field remains finite, but the derived Wbar/h operation
        # overflows.  This must refuse rather than make `inf <= gamma*inf` pass.
        huge_face = replace(
            good.per_face,
            Wbar=np.full_like(good.per_face.Wbar, sys.float_info.max),
            w_vol=np.full_like(good.per_face.w_vol, sys.float_info.max),
        )
        huge_output = replace(good, per_face=huge_face)
        with mock.patch.object(U, "_evaluate_kernel", return_value=huge_output):
            self.assertReason(
                U.UnitsReason.OUTPUT_NONFINITE,
                lambda: self.evaluate(admitted),
            )

    def test_actual_seam_mutants_omit_and_double_thickness_are_killed(self):
        admitted = self.volumetric()

        def assert_killed(view):
            with mock.patch.object(U, "_kernel_view", return_value=view):
                try:
                    result = self.evaluate(admitted)
                except U.UnitsRefusal as refusal:
                    self.assertEqual(
                        refusal.reason, U.UnitsReason.OUTPUT_DIMENSION_MISMATCH
                    )
                else:
                    with self.assertRaises(AssertionError):
                        self.assertRationalOracle(result)

        # Omitted h: send E3d itself as the surface coefficient.
        assert_killed(U._KernelMaterialView(E=1000.0, nu=0.3, h=0.002))
        # Applied h twice: send (E3d*h)*h as the surface coefficient.
        assert_killed(U._KernelMaterialView(E=2.0 * 0.002, nu=0.3, h=0.002))

    def test_actual_dropped_provenance_mutant_is_killed(self):
        admitted = self.volumetric()
        object.__setattr__(admitted, "provenance", None)
        self.assertReason(
            U.UnitsReason.STRUCTURED_PROVENANCE_REQUIRED,
            lambda: self.evaluate(admitted),
        )

    def test_parent_zero_force_and_wvol_mutant_is_killed(self):
        """Reproduce the retained mutant that passed the superseded 2/2 gate."""
        admitted = self.volumetric()
        good = self.evaluate(admitted).evaluation
        zero_face = replace(
            good.per_face, w_vol=np.zeros_like(good.per_face.w_vol)
        )
        zero_output = replace(
            good,
            per_face=zero_face,
            vertex_forces=np.zeros_like(good.vertex_forces),
        )
        with mock.patch.object(U, "_evaluate_kernel", return_value=zero_output):
            self.assertReason(
                U.UnitsReason.OUTPUT_DIMENSION_MISMATCH,
                lambda: self.evaluate(admitted),
            )

    def test_frozen_fixture_bytes_and_legacy_numerics_are_unchanged(self):
        run = (
            REPO / "docs" / "evidence" / "elastic_foundation" / "fixtures" / "v1"
            / "run_20260908T231140Z"
        )
        expected_hashes = {
            "trisingle_stretch.npz":
                "2cb83077485447909e22e4322152bdfd8baa835f43dea973604a111024035ded",
            "patch_8x4_shear.npz":
                "73aaad4a030e7a60b418b07f819a61abe6ac4344c97fee64e23aaa35e7533fd7",
        }
        for name, expected_hash in expected_hashes.items():
            with self.subTest(fixture=name):
                path = run / name
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected_hash)
                with np.load(path) as z:
                    rest = build_rest_geometry(
                        z["rest_pos"].astype(np.float64),
                        z["faces_int32"].astype(np.int64),
                    )
                    material = synthetic(
                        E=float(z["E_f64"]), nu=float(z["nu_f64"]), h=float(z["h_f64"])
                    )
                    legacy = evaluate_elastic(rest, material, z["cur_pos"].astype(np.float64))
                    self.assertEqual(legacy.energy, float(z["exp_energy_f64"]))
                    self.assertTrue(
                        np.array_equal(legacy.vertex_forces, z["exp_vertex_f64"]),
                        "legacy full force array changed",
                    )


if __name__ == "__main__":
    unittest.main()
