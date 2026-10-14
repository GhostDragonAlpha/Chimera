"""Deterministic unit suite for the material-iface lane.

Run via the campaign runner:
    python -B tools/material_iface/tests/test_material_iface.py

Covers, with pinned seeds and no wall-clock dependence:
  - separation of the five record concepts (no god object)
  - metadata-generated controls + the consistency self-test (tamper cases)
  - the mechanism protocol over the reference adapter of the EXISTING STVK law
  - combination validation: unresolved dependencies, incompatible
    formulations, and PLANTED DUPLICATE contributions (flagged, never summed)
  - synthetic auto-labeling of arbitrary preset combinations
  - the runtime parameter-change stored-energy attribution hook
  - integrator sole ownership of physical state
  - end-to-end determinism (identical state hashes across runs)
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import random
import sys
import unittest
from pathlib import Path

# The runner executes this file with cwd = package root; make both the lane
# package (tools.material_iface) and the pinned law copy
# (tools.elastic_foundation) importable regardless of sys.path[0].
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.material_iface import (  # noqa: E402
    DECLARATION_ONLY_MODEL, STVK_MODEL, Assembly, CitedValue,
    CombinationRefusal, CombinationValidator, ContactModel, Control,
    Geometry, Integrator, IntegratorRefusal, MaterialPreset,
    Mechanism, MechanismContribution, MechanismRefusal, ModelRefusal,
    ParameterMeta, ParameterRefusal, ParameterSet, POLICY_FLAG, POLICY_REJECT,
    Quantity, StateProposal, StvkMembraneMechanism,
    SyntheticPenaltyContactMechanism, ValidityRange, bind_surface_to_stvk,
    controls_self_test, convert, generate_controls, verify_controls,
)

SEED = 20260929  # pinned
BASE_SHA = os.environ.get("CHIMERA_BASE_SHA", "unknown-at-dev-time")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# fixtures

def make_surface_geometry():
    positions = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0),
                 (0.0, 1.0, 0.0), (1.0, 1.0, 0.0)]
    faces = [(0, 1, 2), (1, 3, 2)]
    geometry = Geometry.surface("quad-2tri", positions, faces,
                                masses=(1.0, 1.0, 1.0, 1.0))
    bind_surface_to_stvk(geometry)
    return geometry


def make_preset(e_pa: float = 100.0) -> MaterialPreset:
    return MaterialPreset.synthetic(
        "preset-synthetic-sheet",
        STVK_MODEL,
        {"young_modulus": Quantity(e_pa, "Pa"),
         "poisson_ratio": Quantity(0.3, "1"),
         "thickness": Quantity(1.0, "m")},
        note="declared synthetic sheet for interface exercise",
        validity=ValidityRange(unit="K", lo=250.0, hi=350.0,
                               dimension="temperature"))


def make_mechanisms():
    return (StvkMembraneMechanism(),)


def make_integrator(mechanisms=None, dt_s=1e-3, deformed=True):
    geometry = make_surface_geometry()
    initial = None
    if deformed:
        rng = random.Random(SEED)
        initial = tuple(
            (x + rng.uniform(-0.02, 0.02), y + rng.uniform(-0.02, 0.02), z)
            for (x, y, z) in geometry.binding["rest_positions"])
    return Integrator(
        models={STVK_MODEL.model_id: STVK_MODEL},
        geometry=geometry,
        presets={STVK_MODEL.model_id: make_preset()},
        mechanisms=mechanisms or make_mechanisms(),
        dt_s=dt_s, seed=SEED, policy=POLICY_REJECT,
        initial_positions=initial)


# ---------------------------------------------------------------------------
# test doubles (clearly synthetic, used ONLY to exercise protocol rules)

class ProposalMechanism(Mechanism):
    """Synthetic test double proposing an internal-state update."""

    def __init__(self, var: str = "viscous_strain", mode: str = "add",
                 value: float = 0.01, model_id=DECLARATION_ONLY_MODEL.model_id,
                 declares=("positions",)):
        super().__init__(mechanism_id="test.double_proposal", model_id=model_id,
                         declares=tuple(declares))
        self.proposal = StateProposal(model_id=model_id, var=var, mode=mode,
                                      value=value, unit="1")

    def evaluate(self, inputs):
        self.require_inputs(inputs)
        return (MechanismContribution(
            mechanism_id=self.mechanism_id, channel="dissipation",
            point="p0", force=None, stress_voigt=None,
            heat_flux_w_per_m2=0.0, stored_energy_j=0.0,
            dissipated_power_w=0.001, state_proposal=self.proposal,
            solver=None, applicable=True),)


class HostileMechanism(Mechanism):
    """Attempts to mutate the frozen snapshot it is handed."""

    def __init__(self):
        super().__init__(mechanism_id="test.double_hostile",
                         model_id=STVK_MODEL.model_id,
                         declares=("positions",))

    def evaluate(self, inputs):
        self.require_inputs(inputs)
        inputs["positions"][0] = (9.0, 9.0, 9.0)   # must raise TypeError
        raise AssertionError("hostile mutation unexpectedly succeeded")


# ---------------------------------------------------------------------------
# suites

class TestUnits(unittest.TestCase):
    def test_conversion_within_family(self):
        q = Quantity(2.0, "MPa")
        self.assertAlmostEqual(q.in_unit("Pa"), 2.0e6)
        self.assertAlmostEqual(convert(1.0, "GPa", "MPa"), 1000.0)

    def test_temperature_offset(self):
        self.assertAlmostEqual(convert(0.0, "degC", "K"), 273.15)
        self.assertAlmostEqual(convert(273.15, "K", "degC"), 0.0)

    def test_cross_family_refused(self):
        with self.assertRaises(Exception) as ctx:
            convert(1.0, "Pa", "m")
        self.assertIn("dimension_mismatch", str(ctx.exception))

    def test_unknown_unit_refused(self):
        with self.assertRaises(Exception) as ctx:
            Quantity(1.0, "handbreadth")
        self.assertIn("unknown_unit", str(ctx.exception))

    def test_nonfinite_refused(self):
        with self.assertRaises(Exception):
            Quantity(float("nan"), "Pa")


class TestSeparationOfConcepts(unittest.TestCase):
    def test_five_distinct_record_types(self):
        model = STVK_MODEL
        preset = make_preset()
        geometry = make_surface_geometry()
        contact = ContactModel(
            "c1", STVK_MODEL.model_id, STVK_MODEL.model_id,
            metas=(ParameterMeta("penalty_stiffness", "N/m", "elasticity",
                                 "penalty", 1e0, 1e9, 5e2, "log"),
                   ParameterMeta("normal_damping", "N*s/m", "viscosity",
                                 "damping", 1e-3, 1e6, 1.0, "log")),
            quantities={"penalty_stiffness": Quantity(5e2, "N/m"),
                        "normal_damping": Quantity(1.0, "N*s/m")},
            provenance="synthetic-interface-demo")
        integrator = make_integrator()
        types = (type(model), type(preset), type(geometry), type(contact),
                 type(integrator))
        # five DISTINCT types; no shared inheritance chain beyond object
        self.assertEqual(len(set(types)), 5)
        # the model record carries NO numeric parameter values
        self.assertFalse(hasattr(model, "values"))
        # values live only in the preset's ParameterSet
        self.assertIsInstance(preset.values, ParameterSet)
        self.assertAlmostEqual(preset.values.value("young_modulus"), 100.0)
        # contact is PAIR-level, distinct from either bulk model id
        self.assertEqual(contact.pair_key(),
                         (STVK_MODEL.model_id, STVK_MODEL.model_id))
        # integrator owns state; geometry binding is opaque and separate
        self.assertIn("rest", geometry.binding)
        self.assertEqual(len(integrator.snapshot().positions),
                         geometry.n_points)

    def test_model_record_distinct_from_preset_record(self):
        self.assertIsNot(STVK_MODEL.model_id, make_preset().preset_id)
        self.assertEqual(make_preset().model_id, STVK_MODEL.model_id)


class TestGeneratedControls(unittest.TestCase):
    def test_stvk_controls_generated_and_consistent(self):
        summary = controls_self_test(STVK_MODEL)
        self.assertEqual(summary["parameters"], 3)
        self.assertEqual(summary["controls_generated"], 3)
        self.assertEqual(summary["families"],
                         ["bending", "compression", "elasticity"])
        self.assertTrue(summary["consistent"])

    def test_all_eight_families_covered_by_metadata(self):
        controls = generate_controls(DECLARATION_ONLY_MODEL)
        verify_controls(DECLARATION_ONLY_MODEL, controls)
        families = {c.family for c in controls}
        from tools.material_iface import CONTROL_FAMILIES
        self.assertEqual(families, set(CONTROL_FAMILIES))
        kinds = {c.kind for c in controls}
        self.assertIn("log_slider", kinds)
        self.assertIn("linear_slider", kinds)  # specific_heat is linear

    def test_declaration_only_model_refuses_evaluation(self):
        with self.assertRaises(ModelRefusal) as ctx:
            DECLARATION_ONLY_MODEL.require_implemented()
        self.assertIn("declaration_only", str(ctx.exception))

    def test_tamper_missing_control_detected(self):
        controls = generate_controls(STVK_MODEL)
        with self.assertRaises(Exception) as ctx:
            verify_controls(STVK_MODEL, controls[1:])
        self.assertIn("parameter_without_control", str(ctx.exception))

    def test_tamper_orphan_control_detected(self):
        controls = list(generate_controls(STVK_MODEL))
        orphan = Control("mystery_dial", "elasticity", "log_slider", "Pa",
                         1.0, 1e12, 1e2, "rogue.source", "hand-maintained")
        with self.assertRaises(Exception) as ctx:
            verify_controls(STVK_MODEL, tuple(controls) + (orphan,))
        self.assertIn("control_without_parameter", str(ctx.exception))

    def test_tamper_default_mismatch_detected(self):
        controls = list(generate_controls(STVK_MODEL))
        bad = controls[0]
        tampered = Control(bad.name, bad.family, bad.kind, bad.unit, bad.lo,
                           bad.hi, bad.default * 7.0, bad.source_model_id,
                           bad.source_description)
        replaced = tuple(tampered if c.name == bad.name else c
                         for c in controls)
        with self.assertRaises(Exception) as ctx:
            verify_controls(STVK_MODEL, replaced)
        self.assertIn("control_default_mismatch", str(ctx.exception))


class TestParameters(unittest.TestCase):
    def test_unknown_and_missing_refused(self):
        with self.assertRaises(ParameterRefusal) as ctx:
            MaterialPreset.synthetic("p", STVK_MODEL,
                                     {"young_modulus": Quantity(1.0, "Pa"),
                                      "poisson_ratio": Quantity(0.3, "1"),
                                      "thickness": Quantity(1.0, "m"),
                                      "mystery": Quantity(1.0, "Pa")})
        self.assertIn("unknown_parameter", str(ctx.exception))
        with self.assertRaises(ParameterRefusal) as ctx:
            MaterialPreset.synthetic("p", STVK_MODEL,
                                     {"young_modulus": Quantity(1.0, "Pa")})
        self.assertIn("missing_parameter", str(ctx.exception))

    def test_unit_family_mismatch_refused(self):
        with self.assertRaises(ParameterRefusal) as ctx:
            MaterialPreset.synthetic("p", STVK_MODEL,
                                     {"young_modulus": Quantity(1.0, "Pa"),
                                      "poisson_ratio": Quantity(0.3, "1"),
                                      "thickness": Quantity(1.0, "s")})
        self.assertIn("parameter_unit_mismatch", str(ctx.exception))

    def test_range_violation_refused(self):
        with self.assertRaises(ParameterRefusal) as ctx:
            make_preset(e_pa=1e15)  # beyond declared hi=1e12
        self.assertIn("parameter_out_of_range", str(ctx.exception))


class TestMechanismProtocol(unittest.TestCase):
    def setUp(self):
        self.geometry = make_surface_geometry()
        self.preset = make_preset()
        self.mech = StvkMembraneMechanism()

    def displaced_inputs(self):
        positions = list(self.geometry.binding["rest_positions"])
        rng = random.Random(SEED)
        displaced = []
        for p in positions:
            displaced.append((p[0] + rng.uniform(-0.02, 0.02),
                              p[1] + rng.uniform(-0.02, 0.02), p[2]))
        return {"positions": tuple(displaced), "velocities": ((0.0,) * 3,) * 4,
                "time_s": 0.0, "temperature_K": 293.15,
                "geometry": self.geometry,
                "presets": {STVK_MODEL.model_id: self.preset},
                "model_state": {}}

    def test_single_record_type_and_fields(self):
        records = self.mech.evaluate(self.displaced_inputs())
        self.assertEqual(len(records), 6)  # 4 vertices + 2 faces
        for rec in records:
            self.assertIsInstance(rec, MechanismContribution)
            self.assertIsNotNone(rec.solver)
            self.assertGreater(rec.solver.tolerance_energy_scale_j, 0.0)
            self.assertTrue(rec.applicable)
            self.assertEqual(rec.heat_flux_w_per_m2, 0.0)
            self.assertEqual(rec.dissipated_power_w, 0.0)
            self.assertIsNone(rec.state_proposal)  # the law is history-free
        forces = [r for r in records if r.channel == "force"]
        energies = [r for r in records if r.channel == "stored_energy"]
        self.assertEqual(len(forces), 4)
        self.assertEqual(len(energies), 2)
        for rec in forces:
            self.assertIsNotNone(rec.force)
        for rec in energies:
            self.assertGreater(rec.stored_energy_j, 0.0)
            self.assertEqual(len(rec.stress_voigt), 6)

    def test_conservative_law_zero_net_internal_force(self):
        records = self.mech.evaluate(self.displaced_inputs())
        total = [0.0, 0.0, 0.0]
        for rec in records:
            if rec.force:
                for k in range(3):
                    total[k] += rec.force[k]
        for k in range(3):
            self.assertLess(abs(total[k]), 1e-12)

    def test_missing_input_is_named_refusal(self):
        with self.assertRaises(MechanismRefusal) as ctx:
            self.mech.evaluate({"positions": ((0.0, 0.0, 0.0),)})
        self.assertIn("unresolved_dependency", str(ctx.exception))

    def test_wrong_preset_model_refused(self):
        import dataclasses
        inputs = self.displaced_inputs()
        # correct lookup key, but the preset record claims a different model
        inputs["presets"] = {
            STVK_MODEL.model_id: dataclasses.replace(
                self.preset, model_id="some.other.model/v1")}
        with self.assertRaises(MechanismRefusal) as ctx:
            self.mech.evaluate(inputs)
        self.assertIn("mechanism_model_mismatch", str(ctx.exception))

    def test_nonsurface_geometry_refused(self):
        geometry = Geometry.particle("pts", [(0.0, 0.0, 0.0)], (1.0,))
        inputs = self.displaced_inputs()
        inputs["geometry"] = geometry
        with self.assertRaises(MechanismRefusal) as ctx:
            self.mech.evaluate(inputs)
        self.assertIn("representation_mismatch", str(ctx.exception))

    def test_inapplicable_outside_validity(self):
        inputs = self.displaced_inputs()
        inputs["temperature_K"] = 400.0  # outside 250..350 K validity
        records = self.mech.evaluate(inputs)
        self.assertTrue(records)
        for rec in records:
            self.assertFalse(rec.applicable)
            self.assertTrue(rec.inapplicable_reason)


class TestCombinationValidation(unittest.TestCase):
    def setUp(self):
        self.geometry = make_surface_geometry()
        self.inputs = {
            "positions": self.geometry.binding["rest_positions"],
            "velocities": ((0.0,) * 3,) * 4,
            "time_s": 0.0, "temperature_K": 293.15,
            "geometry": self.geometry,
            "presets": {STVK_MODEL.model_id: make_preset()},
            "model_state": {},
        }
        self.probe_ok = dict(self.inputs)
        self.probe_no_state = {k: v for k, v in self.inputs.items()
                               if k != "model_state"}

    def test_clean_assembly_has_no_issues(self):
        validator = CombinationValidator(policy=POLICY_FLAG)
        report = validator.validate(
            Assembly(mechanisms=(StvkMembraneMechanism(),),
                     model_ids=(STVK_MODEL.model_id,),
                     provided_inputs=tuple(self.inputs)),
            self.inputs)
        self.assertTrue(report.valid_for_run, report.issues)
        self.assertEqual(report.contributions_probed, 6)

    def test_planted_duplicate_stored_energy(self):
        m1 = StvkMembraneMechanism()
        m2 = StvkMembraneMechanism(
            mechanism_id="adapter.stvk_membrane/v1#planted-copy")
        validator = CombinationValidator(policy=POLICY_FLAG)
        report = validator.validate(
            Assembly(mechanisms=(m1, m2),
                     model_ids=(STVK_MODEL.model_id,),
                     provided_inputs=tuple(self.inputs)),
            self.inputs)
        self.assertFalse(report.valid_for_run)
        duplicates = report.duplicates()
        self.assertTrue(duplicates)
        points = {issue.point for issue in duplicates
                  if issue.channel == "stored_energy"}
        self.assertTrue({"f0", "f1"} <= points,
                        f"duplicates must hit the shared faces: {points}")
        for issue in duplicates:
            self.assertIn("never silently summed", issue.detail)
        # reject policy raises by name
        with self.assertRaises(CombinationRefusal) as ctx:
            CombinationValidator(policy=POLICY_REJECT).validate(
                Assembly(mechanisms=(m1, m2),
                         model_ids=(STVK_MODEL.model_id,),
                         provided_inputs=tuple(self.inputs)),
                self.inputs)
        self.assertIn("duplicate_contribution", str(ctx.exception))
        # and the integrator path refuses the same assembly
        with self.assertRaises(IntegratorRefusal) as ctx:
            Integrator(models={STVK_MODEL.model_id: STVK_MODEL},
                       geometry=make_surface_geometry(),
                       presets={STVK_MODEL.model_id: make_preset()},
                       mechanisms=(m1, m2), dt_s=1e-3, seed=SEED,
                       policy=POLICY_REJECT)
        self.assertIn("invalid_combination", str(ctx.exception))

    def test_planted_duplicate_contact_force(self):
        def contact(contact_id, point):
            return SyntheticPenaltyContactMechanism(
                ContactModel(
                    contact_id, STVK_MODEL.model_id, STVK_MODEL.model_id,
                    metas=(ParameterMeta("penalty_stiffness", "N/m",
                                         "elasticity", "penalty", 1e0, 1e9,
                                         5e2, "log"),
                           ParameterMeta("normal_damping", "N*s/m",
                                         "viscosity", "damping", 1e-3, 1e6,
                                         1.0, "log")),
                    quantities={"penalty_stiffness": Quantity(5e2, "N/m"),
                                "normal_damping": Quantity(1.0, "N*s/m")},
                    provenance="synthetic-interface-demo"),
                point=point, penetration_m=0.01)
        # two DISTINCT contacts contributing contact_force at the SAME point
        same_point = CombinationValidator(policy=POLICY_FLAG).validate(
            Assembly(mechanisms=(contact("c-a", "v1"), contact("c-b", "v1")),
                     model_ids=(STVK_MODEL.model_id,),
                     provided_inputs=tuple(self.inputs)),
            self.inputs)
        self.assertFalse(same_point.valid_for_run)
        self.assertEqual(len(same_point.duplicates()), 1)
        self.assertEqual(same_point.duplicates()[0].channel, "contact_force")
        self.assertEqual(same_point.duplicates()[0].point, "v1")
        # distinct points are legitimate: no duplicate
        different_points = CombinationValidator(policy=POLICY_FLAG).validate(
            Assembly(mechanisms=(contact("c-a", "v1"), contact("c-b", "v2")),
                     model_ids=(STVK_MODEL.model_id,),
                     provided_inputs=tuple(self.inputs)),
            self.inputs)
        self.assertTrue(different_points.valid_for_run)

    def test_unresolved_dependency(self):
        mech = ProposalMechanism()  # declares positions; provided here
        missing = ProposalMechanism(declares=("positions", "model_state"))
        report = CombinationValidator(policy=POLICY_FLAG).validate(
            Assembly(mechanisms=(mech, missing),
                     model_ids=(DECLARATION_ONLY_MODEL.model_id,),
                     provided_inputs=("positions",)),
            self.probe_no_state)
        kinds = {issue.kind for issue in report.issues}
        self.assertIn("unresolved_dependency", kinds)
        with self.assertRaises(CombinationRefusal) as ctx:
            CombinationValidator(policy=POLICY_REJECT).validate(
                Assembly(mechanisms=(missing,),
                         model_ids=(DECLARATION_ONLY_MODEL.model_id,),
                         provided_inputs=("positions",)),
                self.probe_no_state)
        self.assertIn("unresolved_dependency", str(ctx.exception))

    def test_incompatible_formulation(self):
        mech = StvkMembraneMechanism()
        mech.model_id = "elastic_foundation.stvk_membrane/v2"  # drifted binding
        report = CombinationValidator(policy=POLICY_FLAG).validate(
            Assembly(mechanisms=(mech,),
                     model_ids=("elastic_foundation.stvk_membrane/v1",),
                     provided_inputs=tuple(self.inputs)),
            self.inputs)
        kinds = {issue.kind for issue in report.issues}
        self.assertIn("incompatible_formulation", kinds)
        # contact pairing models absent from the assembly
        contact = SyntheticPenaltyContactMechanism(
            ContactModel("c-x", "model.not.present/v1", STVK_MODEL.model_id,
                         metas=(ParameterMeta("penalty_stiffness", "N/m",
                                              "elasticity", "p", 1e0, 1e9,
                                              5e2, "log"),
                                ParameterMeta("normal_damping", "N*s/m",
                                              "viscosity", "d", 1e-3, 1e6,
                                              1.0, "log")),
                         quantities={"penalty_stiffness": Quantity(1.0, "N/m"),
                                     "normal_damping": Quantity(1.0, "N*s/m")}),
            point="v0")
        report2 = CombinationValidator(policy=POLICY_FLAG).validate(
            Assembly(mechanisms=(contact,),
                     model_ids=(STVK_MODEL.model_id,),
                     provided_inputs=tuple(self.inputs),
                     contacts=(contact.contact,)),
            self.inputs)
        self.assertIn("incompatible_formulation",
                      {issue.kind for issue in report2.issues})


class TestSyntheticLabeling(unittest.TestCase):
    def test_measured_requires_citation_species_validity(self):
        with self.assertRaises(Exception) as ctx:
            MaterialPreset.measured(
                "p", STVK_MODEL,
                {"young_modulus": CitedValue(Quantity(100.0, "Pa"),
                                             citation="", species="x"),
                 "poisson_ratio": CitedValue(Quantity(0.3, "1"),
                                             citation="s", species="x"),
                 "thickness": CitedValue(Quantity(1.0, "m"),
                                         citation="s", species="x")},
                ValidityRange("K", 250.0, 350.0))
        self.assertIn("missing_citation", str(ctx.exception))
        with self.assertRaises(Exception) as ctx:
            MaterialPreset.measured(
                "p", STVK_MODEL,
                {"young_modulus": CitedValue(Quantity(100.0, "Pa"),
                                             citation="source-A", species="x"),
                 "poisson_ratio": CitedValue(Quantity(0.3, "1"),
                                             citation="source-A", species=""),
                 "thickness": CitedValue(Quantity(1.0, "m"),
                                         citation="source-A", species="x")},
                ValidityRange("K", 250.0, 350.0))
        self.assertIn("missing_species", str(ctx.exception))

    def test_arbitrary_combination_auto_declared_synthetic(self):
        parts = {
            "young_modulus": CitedValue(Quantity(100.0, "Pa"),
                                        citation="source-A table 2",
                                        species="synthetic alloy A",
                                        source_id="source-A"),
            "poisson_ratio": CitedValue(Quantity(0.3, "1"),
                                        citation="source-B table 5",
                                        species="synthetic alloy B",
                                        source_id="source-B"),
            "thickness": CitedValue(Quantity(1.0, "m"),
                                    citation="source-A table 2",
                                    species="synthetic alloy A",
                                    source_id="source-A"),
        }
        mixed = MaterialPreset.combine_values(
            "mixed", STVK_MODEL, parts,
            ValidityRange("K", 250.0, 350.0))
        # values drawn from TWO distinct sources => auto-declared synthetic
        self.assertEqual(mixed.kind, "synthetic")
        self.assertIn("synthetic combination", mixed.provenance.citation)
        for source in ("source-A", "source-B"):
            self.assertIn(source, mixed.provenance.citation)
        # per-value provenance survives in the note
        self.assertIn("synthetic alloy A", mixed.provenance.note)
        self.assertIn("synthetic alloy B", mixed.provenance.note)
        # a SINGLE-source combination stays measured
        single = MaterialPreset.combine_values(
            "single", STVK_MODEL,
            {k: CitedValue(v.quantity, v.citation, "synthetic alloy A",
                           source_id="source-A")
             for k, v in parts.items()},
            ValidityRange("K", 250.0, 350.0))
        self.assertEqual(single.kind, "measured")
        self.assertEqual(single.provenance.species, "synthetic alloy A")

    def test_repo_skin_constants_cannot_make_a_measured_stvk_preset(self):
        """The repo measures skin's E (YAMADA 1970) but no nu and no h, so a
        measured STVK preset is impossible; only the synthetic path exists.
        This mirrors the existing repo refusal position."""
        from tools.matter_kernel.constants import lookup
        skin = lookup("mat.skin")
        cited = {
            "young_modulus": CitedValue(Quantity(skin["young_modulus"], "Pa"),
                                        citation=skin["source"],
                                        species="human skin",
                                        source_id="matter_kernel.mat.skin"),
            "poisson_ratio": CitedValue(Quantity(0.3, "1"),
                                        citation="", species=""),
            "thickness": CitedValue(Quantity(1.0, "m"), citation="",
                                    species=""),
        }
        with self.assertRaises(Exception) as ctx:
            MaterialPreset.measured("skin-stvk", STVK_MODEL, cited,
                                    ValidityRange("K", 250.0, 350.0))
        self.assertIn("missing_citation", str(ctx.exception))
        honest = MaterialPreset.synthetic(
            "skin-stvk-synthetic", STVK_MODEL,
            {"young_modulus": Quantity(skin["young_modulus"], "Pa"),
             "poisson_ratio": Quantity(0.3, "1"),
             "thickness": Quantity(1.0, "m")},
            note=("young_modulus cited from " + skin["source"] +
                  "; poisson_ratio and thickness DECLARED SYNTHETIC: the repo "
                  "measures neither for skin"))
        self.assertEqual(honest.kind, "synthetic")
        self.assertIn("YAMADA 1970", honest.provenance.note)

    def test_runtime_adjustment_relabels_measured_to_synthetic(self):
        parts = {name: CitedValue(q, "declared-test-source", "synthetic alloy",
                                  source_id="declared-test-source")
                 for name, q in (("young_modulus", Quantity(100.0, "Pa")),
                                 ("poisson_ratio", Quantity(0.3, "1")),
                                 ("thickness", Quantity(1.0, "m")))}
        measured = MaterialPreset.combine_values(
            "m", STVK_MODEL, parts, ValidityRange("K", 250.0, 350.0))
        self.assertEqual(measured.kind, "measured")
        adjusted = measured.runtime_adjusted("young_modulus",
                                             Quantity(150.0, "Pa"), step=7)
        self.assertEqual(adjusted.kind, "synthetic")
        self.assertIn("runtime adjustment at step 7", adjusted.provenance.citation)
        self.assertIn("originally measured", adjusted.provenance.note)
        self.assertIn("declared-test-source", adjusted.provenance.note)
        self.assertAlmostEqual(adjusted.values.value("young_modulus"), 150.0)
        self.assertAlmostEqual(adjusted.values.value("poisson_ratio"), 0.3)

    def test_validity_range_gating(self):
        preset = make_preset()
        ok, _ = preset.applicability({"temperature_K": Quantity(300.0, "K")})
        self.assertTrue(ok)
        # 26.85 degC == 300.0 K: the degC input must CONVERT, not fail
        ok_deg_c, reason = preset.applicability(
            {"temperature_K": Quantity(26.85, "degC")})
        self.assertTrue(ok_deg_c, reason)
        out, reason = preset.applicability(
            {"temperature_K": Quantity(400.0, "K")})
        self.assertFalse(out)
        self.assertIn("outside declared validity", reason)


class TestEnergyChangeHook(unittest.TestCase):
    def test_runtime_parameter_change_is_attributed(self):
        integrator = make_integrator()
        for _ in range(10):
            integrator.step()
        before = integrator.stored_energy_now()
        record = integrator.change_parameter(
            STVK_MODEL.model_id, "young_modulus", Quantity(150.0, "Pa"))
        # attribution identity: delta == after - before (same frozen state)
        self.assertAlmostEqual(record.stored_energy_before_j, before,
                               places=15)
        self.assertAlmostEqual(
            record.delta_stored_energy_j,
            record.stored_energy_after_j - record.stored_energy_before_j,
            places=15)
        # STVK stored energy is exactly linear in E at fixed geometry:
        self.assertAlmostEqual(record.stored_energy_after_j,
                               1.5 * record.stored_energy_before_j,
                               delta=1e-9 * max(1.0, before))
        # the change is reported in the NEXT ledger entry, not absorbed
        entry = integrator.step()
        self.assertEqual(len(entry.parameter_changes), 1)
        self.assertEqual(entry.parameter_changes[0].parameter, "young_modulus")
        self.assertAlmostEqual(entry.parameter_changes[0].new.value, 150.0)
        # later entries carry no stale attributions
        entry2 = integrator.step()
        self.assertEqual(entry2.parameter_changes, ())
        # the active preset was relabeled synthetic with an auditable note
        preset = integrator.snapshot().presets[STVK_MODEL.model_id]
        self.assertEqual(preset.kind, "synthetic")
        self.assertIn("originally", preset.provenance.note)

    def test_parameter_change_does_not_move_owned_state(self):
        integrator = make_integrator()
        integrator.step()
        snap_before = integrator.snapshot()
        integrator.change_parameter(STVK_MODEL.model_id, "young_modulus",
                                    Quantity(80.0, "Pa"))
        snap_after = integrator.snapshot()
        # the owned PHYSICAL state is untouched by attribution
        self.assertEqual(snap_after.positions, snap_before.positions)
        self.assertEqual(snap_after.velocities, snap_before.velocities)
        self.assertEqual(snap_after.time_s, snap_before.time_s)
        self.assertEqual(snap_after.model_state, snap_before.model_state)

    def test_unknown_parameter_refused_by_name(self):
        integrator = make_integrator()
        with self.assertRaises(IntegratorRefusal) as ctx:
            integrator.change_parameter(STVK_MODEL.model_id, "mystery",
                                        Quantity(1.0, "Pa"))
        self.assertIn("unknown_parameter", str(ctx.exception))


class TestIntegratorSoleAuthority(unittest.TestCase):
    def test_snapshots_are_frozen(self):
        integrator = make_integrator()
        snap = integrator.snapshot()
        with self.assertRaises(TypeError):
            snap.positions[0] = (9.0, 9.0, 9.0)  # tuple assignment
        inputs = snap.as_inputs()
        self.assertEqual(inputs["positions"], snap.positions)
        with self.assertRaises(TypeError):
            inputs["presets"]["injected"] = make_preset()
        with self.assertRaises(TypeError):
            HostileMechanism().evaluate(inputs)

    def test_proposals_only_through_the_gate(self):
        model = DECLARATION_ONLY_MODEL
        geometry = Geometry.particle("pts", [(0.0, 0.0, 0.0)], (1.0,))
        preset = MaterialPreset.synthetic("pp", model,
                                          {m.name: Quantity(m.default, m.unit)
                                           for m in model.parameters})
        mech = ProposalMechanism()
        integrator = Integrator(models={model.model_id: model},
                                geometry=geometry,
                                presets={model.model_id: preset},
                                mechanisms=(mech,), dt_s=1e-3, seed=SEED)
        hash_before = integrator.state_hash()
        # evaluating the mechanism alone must NOT advance anything
        mech.evaluate(integrator.snapshot().as_inputs())
        self.assertEqual(integrator.state_hash(), hash_before)
        entry = integrator.step()
        self.assertNotEqual(integrator.state_hash(), hash_before)
        self.assertAlmostEqual(
            dict(integrator.snapshot().model_state[model.model_id])
            ["viscous_strain"], 0.01)
        self.assertEqual(len(integrator.read_only_history(model.model_id)), 1)
        self.assertEqual(entry.dissipated_energy_j, 0.001 * 1e-3)

    def test_undeclared_state_variable_refused(self):
        model = DECLARATION_ONLY_MODEL
        geometry = Geometry.particle("pts", [(0.0, 0.0, 0.0)], (1.0,))
        preset = MaterialPreset.synthetic("pp", model,
                                          {m.name: Quantity(m.default, m.unit)
                                           for m in model.parameters})
        mech = ProposalMechanism(var="not_declared")
        integrator = Integrator(models={model.model_id: model},
                                geometry=geometry,
                                presets={model.model_id: preset},
                                mechanisms=(mech,), dt_s=1e-3, seed=SEED)
        with self.assertRaises(IntegratorRefusal) as ctx:
            integrator.step()
        self.assertIn("unknown_state_variable", str(ctx.exception))

    def test_particle_representation_binding_end_to_end(self):
        """The contact record type binds the particle representation."""
        geometry = Geometry.particle("pts",
                                     [(0.0, 0.0, 0.0), (0.5, 0.0, -0.01)],
                                     (1.0, 2.0))
        contact = SyntheticPenaltyContactMechanism(
            ContactModel("cp", STVK_MODEL.model_id, STVK_MODEL.model_id,
                         metas=(ParameterMeta("penalty_stiffness", "N/m",
                                              "elasticity", "penalty",
                                              1e0, 1e9, 5e2, "log"),
                                ParameterMeta("normal_damping", "N*s/m",
                                              "viscosity", "damping",
                                              1e-3, 1e6, 1.0, "log")),
                         quantities={"penalty_stiffness": Quantity(5e2, "N/m"),
                                     "normal_damping": Quantity(1.0, "N*s/m")},
                         provenance="synthetic-interface-demo"),
            point="p1", penetration_m=0.01)
        records = contact.evaluate({
            "positions": geometry.binding["rest_positions"],
            "velocities": ((0.0, 0.0, 0.0), (0.0, 0.0, -1.0))})
        self.assertEqual(len(records), 1)
        rec = records[0]
        self.assertEqual(rec.channel, "contact_force")
        self.assertEqual(rec.point, "p1")
        self.assertIsNotNone(rec.force)
        # pushes BACK against the -z penetration: restoring force is +z
        self.assertGreater(rec.force[2], 0.0)

    def test_volume_binding_refused_by_name(self):
        with self.assertRaises(Exception) as ctx:
            Geometry.volume("vol-1")
        self.assertIn("volume_binding_unsupported", str(ctx.exception))


class TestEndToEndDeterminism(unittest.TestCase):
    def test_identical_runs_identical_hashes(self):
        def run():
            integrator = make_integrator()
            integrator.change_parameter(STVK_MODEL.model_id, "young_modulus",
                                        Quantity(120.0, "Pa"))
            entries = [integrator.step(temperature_k=293.15)
                       for _ in range(30)]
            return integrator.state_hash(), entries

        hash_a, entries_a = run()
        hash_b, entries_b = run()
        self.assertEqual(hash_a, hash_b)
        self.assertEqual(len(entries_a), len(entries_b))
        for ea, eb in zip(entries_a, entries_b):
            self.assertEqual(ea.stored_energy_j, eb.stored_energy_j)
            self.assertEqual(ea.excluded_contributions,
                             eb.excluded_contributions)
        # ledger fully finite and accounted
        for entry in entries_a:
            for value in (entry.stored_energy_j, entry.dissipated_energy_j,
                          entry.heat_energy_j, entry.external_work_j):
                self.assertTrue(math.isfinite(value))

    def test_excluded_out_of_validity_contributes_nothing(self):
        integrator = make_integrator()
        before = integrator.snapshot().positions
        velocities_before = integrator.snapshot().velocities
        entry = integrator.step(temperature_k=400.0)  # outside 250..350 K
        self.assertEqual(entry.excluded_contributions, 6)
        # nothing applied: owned physical state does not move this step
        self.assertEqual(integrator.snapshot().positions, before)
        self.assertEqual(integrator.snapshot().velocities, velocities_before)
        self.assertEqual(entry.stored_energy_j, 0.0)

    def test_heat_and_external_work_recorded_not_hidden(self):
        integrator = make_integrator()
        entry = integrator.step()
        # the adapted STVK law is conservative: zero heat, zero dissipation,
        # zero external work -- recorded as explicit zeros, not silently
        # treated as unsupported
        self.assertEqual(entry.heat_energy_j, 0.0)
        self.assertEqual(entry.dissipated_energy_j, 0.0)
        self.assertEqual(entry.external_work_j, 0.0)
        self.assertGreater(entry.stored_energy_j, 0.0)


# ---------------------------------------------------------------------------
# entry point

def load_artifact_hashes() -> dict:
    package = Path(__file__).resolve().parents[1]
    hashes = {}
    for path in sorted(package.rglob("*.py")):
        hashes[str(path.relative_to(ROOT))] = sha256_file(path)
    return hashes


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromModule(
        sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    output_dir = os.environ.get("CHIMERA_OUTPUT_DIR")
    summary = {
        "lane": "material-iface",
        "base_sha": BASE_SHA,
        "seed": SEED,
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "deterministic_seed": SEED,
        "reference_adapter_law": "tools/elastic_foundation (STVK membrane)",
        "artifact_sha256": load_artifact_hashes(),
    }
    if output_dir:
        path = Path(output_dir) / "result.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(summary, indent=2, sort_keys=True),
                        encoding="utf-8")
    print("RESULT_JSON " + json.dumps(
        {k: summary[k] for k in ("tests_run", "failures", "errors",
                                 "skipped")}))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
