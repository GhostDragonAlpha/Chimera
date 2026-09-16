"""Independent source-value controls and adverse schema/semantic probes."""
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest

from tools.science_funnel.common import Refusal
from tools.science_funnel.force_adapters import (
    nist_constants, jpl_gravity, cantera_nasa7, nist_aluminum, iaea_nuclides)
from tools.science_funnel.units import convert

DATA = Path(__file__).resolve().parents[1] / "data" / "force_sources"


class SourceContracts(unittest.TestCase):
    def parse(self, function, file):
        return function((DATA / file).read_bytes(), {}, DATA / file)

    def iaea_fixture(self, change=None, identity=("6", "8")):
        reader = csv.DictReader(io.StringIO((DATA / "iaea_ground_states.csv").read_text(encoding="latin1")))
        row = next(r for r in reader if (r["z"], r["n"]) == identity)
        if change:
            row.update(change)
        out = io.StringIO(newline="")
        writer = csv.DictWriter(out, reader.fieldnames)
        writer.writeheader()
        writer.writerow(row)
        return out.getvalue().encode("latin1")

    def test_codata_numeric_and_truncated_exact_are_separate(self):
        rows = self.parse(nist_constants, "nist_constants.txt")
        values = {r["payload"]["subject"]: r["payload"] for r in rows if r["record_type"] == "measurement"}
        self.assertEqual(len(rows), 367)
        self.assertEqual(values["speed of light in vacuum"]["value_si"], 299792458)
        self.assertEqual(values["speed of light in vacuum"]["uncertainty_si"], 0)
        self.assertEqual(values["Newtonian constant of gravitation"]["value_si"], 6.67430e-11)
        self.assertAlmostEqual(values["Newtonian constant of gravitation"]["uncertainty_si"], 1.5e-15, delta=1e-29)
        r = next(r["payload"] for r in rows if r["external_id"] == "CODATA2022/molar gas constant")
        self.assertTrue(r["printed_value_truncated"])
        self.assertTrue(r["exact_physical_definition"])
        self.assertFalse(r["scalar_ready"])
        self.assertNotIn("molar gas constant", values)

    def test_codata_duplicate_and_changed_release_refuse(self):
        raw = (DATA / "nist_constants.txt").read_bytes()
        line = next(s for s in raw.splitlines() if s.startswith(b"speed of light in vacuum"))
        for mutation in (raw + b"\n" + line, raw.replace(b"2022 CODATA", b"2026 CODATA")):
            with self.assertRaises(Refusal):
                nist_constants(mutation, {}, None)

    def test_jpl_GM_uses_cubic_unit_conversion_and_system_identity(self):
        rows = self.parse(jpl_gravity, "jpl_astrodynamics.html")
        by_id = {r["external_id"]: r["payload"] for r in rows}
        self.assertEqual(len(rows), 11)
        self.assertEqual(by_id["DE440/399/GM"]["value_si"], 398600.435507e9)
        self.assertEqual(by_id["DE440/301/GM"]["value_si"], 4902.800118e9)
        self.assertEqual(by_id["DE440/5/GM"]["conditions"]["mass_scope"], "planetary_system")
        self.assertEqual(by_id["DE440/399/GM"]["conditions"]["mass_scope"], "body")
        self.assertAlmostEqual(by_id["DE440/10/GM"]["value_si"] / 1e20, 1.32712440041279419, places=15)

    def test_jpl_scope_relabel_is_not_a_name_match(self):
        raw = (DATA / "jpl_astrodynamics.html").read_bytes().replace(b"Jupiter system", b"Jupiter")
        with self.assertRaises(Refusal):
            jpl_gravity(raw, {}, None)

    def test_yaml_NO_is_species_and_global_loader_is_unchanged(self):
        import yaml
        previous = yaml.safe_load("NO")
        rows = self.parse(cantera_nasa7, "cantera_gri30.yaml")
        self.assertEqual(len(rows), 53)
        nitric = next(r["payload"]["definition"] for r in rows if r["external_id"] == "Cantera/NASA7/NO")
        self.assertEqual(nitric["species"], "NO")
        self.assertEqual(nitric["composition"], {"N": 1, "O": 1})
        self.assertEqual(yaml.safe_load("NO"), previous)
        water = next(r["payload"]["definition"] for r in rows if r["external_id"] == "Cantera/NASA7/H2O")
        self.assertEqual(water["composition"], {"H": 2, "O": 1})
        self.assertEqual(water["temperature_ranges_K"], [200, 1000, 3500])

    def test_yaml_duplicate_alias_and_executable_tag_refuse(self):
        for raw in (b"species: []\nspecies: []", b"a: &x [1]\nspecies: *x",
                    b"!!python/object/apply:os.system ['echo invalid']"):
            with self.assertRaises(Refusal):
                cantera_nasa7(raw, {}, None)

    def test_nasa7_descending_ranges_refuse(self):
        raw = b"""species:
- name: NO
  composition: {N: 1, O: 1}
  thermo:
    model: NASA7
    temperature-ranges: [200, 1000, 500]
    data: [[1,0,0,0,0,0,0], [1,0,0,0,0,0,0]]
"""
        with self.assertRaises(Refusal):
            cantera_nasa7(raw, {}, None)

    def test_solid_equation_range_does_not_extend_data_coverage(self):
        rows = self.parse(nist_aluminum, "nist_al6061.html")
        curves = {r["payload"]["definition"]["quantity"]: r["payload"]["definition"] for r in rows}
        self.assertEqual(curves["thermal_conductivity"]["temperature_range_K"], [4, 300])
        self.assertEqual(curves["thermal_conductivity"]["equation_range_K"], [1, 300])
        self.assertEqual(curves["young_modulus"]["temperature_range_K"], [2, 295])
        self.assertEqual(curves["young_modulus"]["output_scale_to_SI"], 1e9)
        self.assertEqual(curves["thermal_strain"]["output_scale_to_SI"], 1e-5)
        self.assertEqual(curves["specific_heat"]["curve_fit_relative_error_percent"], 5)
        self.assertNotIn("uncertainty_si", curves["specific_heat"])

    def test_iaea_micro_AMU_is_not_AMU_or_kg(self):
        row = iaea_nuclides(self.iaea_fixture(), {}, None)[0]["payload"]
        self.assertAlmostEqual(row["atomic_mass_u"], 14.00324198862, places=11)
        self.assertEqual(row["half_life"]["seconds"], 179874478055.1744)
        self.assertEqual(row["half_life"]["kind"], "estimate")
        self.assertEqual(row["source_extraction_date"], "2023-10-18")
        self.assertEqual(row["binding_energy_per_nucleon_keV"], 7520.3198)

    def test_stable_unknown_and_bound_half_lives_are_distinct(self):
        stable = iaea_nuclides(self.iaea_fixture(identity=("8", "8")), {}, None)[0]["payload"]
        self.assertEqual(stable["half_life"]["kind"], "stable")
        self.assertIsNone(stable["half_life"]["seconds"])
        unknown = iaea_nuclides(self.iaea_fixture({"half_life": "", "half_life_sec": "", "unc_hls": ""}), {}, None)[0]["payload"]
        self.assertEqual(unknown["half_life"]["kind"], "unknown")
        bound = iaea_nuclides(self.iaea_fixture({"operator_hl": "GT"}), {}, None)[0]["payload"]
        self.assertEqual(bound["half_life"]["kind"], "bound")
        self.assertEqual(bound["half_life"]["operator"], "GT")

    def test_conflicting_stable_and_invalid_qualifier_refuse(self):
        for change in ({"half_life": "STABLE"}, {"operator_hl": "BANANA"},
                       {"half_life_sec": "-1"}, {"decay_1_%": "101"}):
            with self.assertRaises(Refusal):
                iaea_nuclides(self.iaea_fixture(change), {}, None)

    def test_shifted_level_keeps_qualification(self):
        row = iaea_nuclides(self.iaea_fixture({"energy_shift": "X", "ripl_shift": "200"}), {}, None)[0]
        self.assertFalse(row["payload"]["level"]["resolved_ground_state"])
        self.assertEqual(row["payload"]["level"]["ripl_assigned_shift_keV"], 200)
        self.assertIn("level_assignment_unresolved", row["unknowns"])

    def test_iaea_full_inventory_and_zero_binding_preserved(self):
        rows = self.parse(iaea_nuclides, "iaea_ground_states.csv")
        self.assertEqual(len(rows), 3386)
        self.assertEqual(len({r["external_id"] for r in rows}), 3386)
        self.assertEqual(sum(not r["payload"]["level"]["resolved_ground_state"] for r in rows), 45)
        neutron = next(r["payload"] for r in rows if r["payload"]["Z"] == 0)
        self.assertEqual(neutron["binding_energy_per_nucleon_keV"], 0)
        self.assertIsNotNone(neutron["atomic_mass_u"])

    def test_acquisition_verifies_existing_bytes_and_refuses_pin_drift(self):
        import shutil
        from tools.science_funnel.force_catalog import acquire
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for file in DATA.iterdir():
                if file.is_file():
                    shutil.copyfile(file, root / file.name)
            result = acquire(root)
            self.assertTrue(all(r["status"] == "verified_existing" for r in result))
            path = root / "nist_constants.txt"
            path.write_bytes(path.read_bytes() + b"changed")
            with self.assertRaises(Refusal) as ctx:
                acquire(root)
            self.assertEqual(ctx.exception.code, "existing_acquisition_pin_mismatch")

    def test_force_units_do_not_equate_thermal_and_mechanical_quantities(self):
        self.assertEqual(convert(1, "km3/s2", "gravitational_parameter")["value_si"], 1e9)
        for unit, quantity in (("J/K", "energy"), ("J/(kg*K)", "heat_capacity"),
                               ("m3/s2", "gravitational_constant"), ("J*s", "energy"),
                               ("F/m", "permeability")):
            with self.assertRaises(Refusal):
                convert(1, unit, quantity)


if __name__ == "__main__":
    unittest.main()
