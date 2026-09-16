"""Source-specific reductions into assertions; imported equations are never executed."""
import copy
import csv
import io
import math
import re
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser

from .common import Refusal, draft, number, require, text
from .units import convert


class Tables(HTMLParser):
    """Read table text only. Scripts and markup are not executable inputs."""
    def __init__(self, raw):
        super().__init__(convert_charrefs=True)
        self.tables, self.table, self.row, self.cell = [], None, None, None
        self.feed(raw.decode("utf-8-sig"))
        require(self.table is None and self.cell is None, "unclosed_source_table")

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            require(self.table is None, "nested_source_table")
            self.table = []
        elif tag == "tr" and self.table is not None:
            require(self.row is None, "nested_source_row")
            self.row = []
        elif tag in ("th", "td") and self.row is not None:
            require(self.cell is None, "nested_source_cell")
            self.cell = []

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None:
            self.row.append(" ".join(" ".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            require(self.cell is None, "unclosed_source_cell")
            self.table.append(self.row)
            self.row = None
        elif tag == "table" and self.table is not None:
            require(self.row is None, "unclosed_source_row")
            self.tables.append(self.table)
            self.table = None

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)


def one(items, code):
    require(len(items) == 1, code, len(items))
    return items[0]


def decimal_text(raw, ellipsis=False):
    value = re.sub(r"\s+", "", raw)
    if "..." in value:
        require(ellipsis, "truncated_number_not_scalar", raw)
        value = value.replace("...", "")
    require(re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", value),
            "source_number_syntax", raw)
    try:
        out = Decimal(value)
    except InvalidOperation as exc:
        raise Refusal("source_number_syntax", raw) from exc
    require(out.is_finite(), "nonfinite_source_number")
    return str(out)


NIST_SCALARS = {
    "speed of light in vacuum": ("speed", "m s^-1", "m/s"),
    "Newtonian constant of gravitation": ("gravitational_constant", "m^3 kg^-1 s^-2", "m3/(kg*s2)"),
    "Avogadro constant": ("inverse_amount", "mol^-1", "1/mol"),
    "Boltzmann constant": ("heat_capacity", "J K^-1", "J/K"),
    "elementary charge": ("charge", "C", "C"),
    "Planck constant": ("action", "J Hz^-1", "J*s"),
    "atomic mass constant": ("mass", "kg", "kg"),
    "electron mass": ("mass", "kg", "kg"),
    "proton mass": ("mass", "kg", "kg"),
    "neutron mass": ("mass", "kg", "kg"),
    "vacuum electric permittivity": ("permittivity", "F m^-1", "F/m"),
    "vacuum mag. permeability": ("permeability", "N A^-2", "N/A2"),
}


def nist_constants(raw, manifest, path):
    content = raw.decode("ascii")
    require("2022 CODATA adjustment" in content, "codata_release_not_supported")
    lines = content.splitlines()
    start = one([i for i, s in enumerate(lines) if s.startswith("----")], "codata_header")
    out, names = [], set()
    for ordinal, line in enumerate(lines[start + 1:], start + 2):
        if not line.strip():
            continue
        require(len(line) >= 110, "codata_fixed_columns", ordinal)
        name, value, unc, unit = line[:60].strip(), line[60:85].strip(), line[85:110].strip(), line[110:].strip()
        require(name and name not in names, "codata_duplicate_identity", name)
        names.add(name)
        exact, truncated = unc == "(exact)", "..." in value
        prefix = decimal_text(value, ellipsis=True)
        u = "0" if exact else decimal_text(unc)
        entity = {"type": "physical_constant", "name": name, "release": "CODATA2022",
                  "raw_value": value, "raw_uncertainty": unc, "raw_unit": unit,
                  "value_decimal_prefix": prefix, "uncertainty_decimal": u,
                  "exact_physical_definition": exact, "printed_value_truncated": truncated,
                  "source_line": ordinal, "raw_line": line,
                  "scalar_ready": not truncated and name in NIST_SCALARS}
        out.append(draft("CODATA2022/" + name, "entity", entity,
                         unknowns=["quantity_mapping_unselected"] if name not in NIST_SCALARS else []))
        if name in NIST_SCALARS:
            quantity, expected_unit, engine_unit = NIST_SCALARS[name]
            require(unit == expected_unit and not truncated, "codata_selected_unit_or_precision", name)
            result = convert(prefix, engine_unit, quantity, u)
            result.update(subject=name, conditions={"release": "CODATA2022", "kind": "fundamental_constant"},
                          exact_physical_definition=exact, raw_line=line, decimal_value=prefix)
            out.append(draft("CODATA2022/" + name + "/SI", "measurement", result))
    require(set(NIST_SCALARS) <= names, "codata_selected_constant_missing")
    return out


JPL_IDS = {"Mercury": ("199", "body"), "Venus": ("299", "body"),
           "Earth": ("399", "body"), "Moon": ("301", "body"),
           "Mars system": ("4", "planetary_system"), "Jupiter system": ("5", "planetary_system"),
           "Saturn system": ("6", "planetary_system"), "Uranus system": ("7", "planetary_system"),
           "Neptune system": ("8", "planetary_system"), "Pluto system": ("9", "planetary_system")}


def jpl_gravity(raw, manifest, path):
    require(b"DE440" in raw, "jpl_ephemeris_missing")
    tables = Tables(raw).tables
    table = one([t for t in tables if t and t[0] == ["Planet", "GM (km 3 s -2 )"]],
                "jpl_gravity_header")
    names, out = set(), []
    for row in table[1:]:
        require(len(row) == 2 and row[0] in JPL_IDS and row[0] not in names, "jpl_body_identity", row)
        name, value = row
        names.add(name)
        body_id, scope = JPL_IDS[name]
        converted = convert(decimal_text(value), "km3/s2", "gravitational_parameter")
        require(converted["value_si"] > 0, "jpl_nonpositive_GM")
        converted.update(subject=name, conditions={"ephemeris": "DE440", "mass_scope": scope},
                         naif_id=body_id, raw_row=row)
        out.append(draft("DE440/" + body_id + "/GM", "measurement", converted, unknowns=["source_uncertainty"]))
    require(names == set(JPL_IDS), "jpl_body_inventory_changed")
    solar = one([r for t in tables for r in t if r and r[0] == "heliocentric gravitational constant"],
                "jpl_solar_parameter")
    require(len(solar) == 4, "jpl_solar_columns")
    match = re.fullmatch(r"([0-9.]+) x 10 ([+-]?[0-9]+) m 3 s -2", solar[2])
    require(match, "jpl_solar_units")
    value = Decimal(match[1]) * Decimal(10) ** int(match[2])
    result = convert(str(value), "m3/s2", "gravitational_parameter")
    result.update(subject="Sun", conditions={"ephemeris": "DE440", "mass_scope": "body"},
                  naif_id="10", raw_row=solar)
    out.append(draft("DE440/10/GM", "measurement", result, unknowns=["source_uncertainty"]))
    return out


def cantera_nasa7(raw, manifest, path):
    # YAML 1.1 interprets NO as False; Cantera species names use YAML 1.2 semantics.
    # Remove those implicit conversions locally, without changing PyYAML globals.
    import yaml
    class Loader(yaml.SafeLoader):
        yaml_implicit_resolvers = {
            key: [(tag, rx) for tag, rx in values
                  if tag not in ("tag:yaml.org,2002:bool", "tag:yaml.org,2002:timestamp")]
            for key, values in copy.deepcopy(yaml.SafeLoader.yaml_implicit_resolvers).items()
        }
        def construct_mapping(self, node, deep=False):
            result = {}
            for key_node, val_node in node.value:
                key = self.construct_object(key_node, deep=deep)
                require(isinstance(key, str) and key not in result, "yaml_duplicate_or_nontext_key", key)
                result[key] = self.construct_object(val_node, deep=deep)
            return result
    try:
        for count, event in enumerate(yaml.parse(raw, Loader=Loader)):
            require(count < 100000, "yaml_event_limit")
            require(not isinstance(event, yaml.events.AliasEvent), "yaml_alias_refused")
        data = yaml.load(raw, Loader=Loader)
    except yaml.YAMLError as exc:
        raise Refusal("yaml_source_invalid", str(exc)) from exc
    require(isinstance(data, dict) and isinstance(data.get("species"), list), "cantera_species_required")
    out = []
    for row in data["species"]:
        name = text(row.get("name"), "species.name")
        composition = row.get("composition")
        require(isinstance(composition, dict) and composition, "species_composition")
        for symbol, count in composition.items():
            require(re.fullmatch(r"[A-Z][a-z]?", symbol) and number(count) > 0 and
                    number(count).is_integer(), "species_atom_count", name)
        thermo = row.get("thermo", {})
        require(thermo.get("model") == "NASA7", "species_model_not_NASA7", name)
        ranges = [number(x) for x in thermo.get("temperature-ranges", [])]
        coeff = [[number(x) for x in part] for part in thermo.get("data", [])]
        require(len(ranges) in (2, 3) and len(coeff) == len(ranges)-1 and
                all(len(c) == 7 for c in coeff) and ranges[0] > 0 and
                all(a < b for a, b in zip(ranges, ranges[1:])), "NASA7_shape", name)
        require(thermo.get("reference-pressure", 101325) == 101325, "NASA7_reference_pressure", name)
        definition = {"model": "NASA7", "species": name, "composition": composition,
                      "temperature_ranges_K": ranges, "coefficients": coeff,
                      "reference_pressure_Pa": 101325,
                      "coefficients_order": "ascending temperature regions, a0..a6",
                      "equations": ["Cp/R=sum(a_i*T^i,i=0..4)",
                                    "H/(RT)=a0+a1*T/2+a2*T^2/3+a3*T^3/4+a4*T^4/5+a5/T",
                                    "S/R=a0*ln(T)+a1*T+a2*T^2/2+a3*T^3/3+a4*T^4/4+a6"],
                      "semantics": "Ideal-gas species standard-state thermo, not a condensed-phase or reaction model.",
                      "source_note": thermo.get("note"), "source_species": row,
                      "source_description": data.get("description"),
                      "parser": {"name": "PyYAML SafeLoader with strict chemical-name semantics", "version": yaml.__version__}}
        out.append(draft("Cantera/NASA7/" + name, "model", {"definition": definition, "executable": False},
                         unknowns=["fit_uncertainty", "phase_applicability", "reaction_kinetics_not_imported"]))
    require(out, "empty_capture")
    return out


def table_map(table):
    require(all(len(r) == 3 for r in table), "nist_curve_columns")
    rows = {}
    for row in table[1:]:
        require(row[0] not in rows, "nist_curve_duplicate_row", row[0])
        rows[row[0]] = row[1:]
    return rows


def range_pair(value):
    match = re.fullmatch(r"([0-9.]+)-([0-9.]+)", value)
    require(match, "nist_temperature_range", value)
    pair = [number(match[1]), number(match[2])]
    require(0 <= pair[0] < pair[1], "nist_temperature_range")
    return pair


def nist_aluminum(raw, manifest, path):
    require(b"6061-T6" in raw, "nist_alloy_identity")
    tables = Tables(raw).tables
    thermal = table_map(one([t for t in tables if t and t[0] == ["", "Thermal Conductivity", "Specific Heat"]],
                            "nist_thermal_header"))
    elastic = table_map(one([t for t in tables if t and t[0] == ["", "Young's Modulus", "Linear expansion"]],
                            "nist_elastic_header"))
    require(thermal["UNITS"] == ["W/(m-K)", "J/(kg-K)"], "nist_thermal_units")
    require(elastic["UNITS"] == ["GPa", "[(L-L 293 )/L 293 ] x 10 5 unitless, eg. m/m"],
            "nist_elastic_units")
    specs = [("thermal_conductivity", thermal, 0, "log10_polynomial", 9, "W/(m*K)", 1),
             ("specific_heat", thermal, 1, "log10_polynomial", 9, "J/(kg*K)", 1),
             ("young_modulus", elastic, 0, "polynomial", 5, "Pa", 1e9),
             ("thermal_strain", elastic, 1, "polynomial_low_constant", 5, "1", 1e-5)]
    out = []
    for quantity, rows, column, model, count, unit, scale in specs:
        key = "data range" if rows is thermal else "data range (K)"
        data_range = range_pair(rows[key][column])
        equation_range = range_pair(rows[key.replace("data", "equation")][column])
        valid = [max(data_range[0], equation_range[0]), min(data_range[1], equation_range[1])]
        coeff = [number(rows[chr(ord("a")+i)][column]) for i in range(count)]
        definition = {"model": model, "quantity": quantity, "unit_si": unit,
                      "subject": "Aluminum 6061-T6 (UNS A96061)", "coefficients": coeff,
                      "output_scale_to_SI": scale, "temperature_range_K": valid,
                      "data_range_K": data_range, "equation_range_K": equation_range,
                      "curve_fit_relative_error_percent": number(rows["curve fit % error relative to data"][column]),
                      "error_semantics": "Source curve-fit error relative to data; not measurement standard uncertainty.",
                      "raw_table": rows, "coefficients_order": "ascending powers"}
        if model == "polynomial_low_constant":
            definition.update(low_temperature_K=number(rows["T low (K)"][column]),
                              low_constant=number(rows["f>"][column]), reference_temperature_K=293,
                              boundary_convention="polynomial at equality")
        out.append(draft("NIST/Al6061T6/" + quantity, "model",
                         {"definition": definition, "executable": False},
                         unknowns=["material_batch_variation", "measurement_uncertainty",
                                   "yield_fracture_poisson_ratio_not_supplied"]))
    return out


def iaea_nuclides(raw, manifest, path):
    reader = csv.DictReader(io.StringIO(raw.decode("latin1"), newline=""))
    fields = reader.fieldnames
    required = {"z", "n", "symbol", "energy", "energy_shift", "half_life", "operator_hl",
                "half_life_sec", "unc_hls", "atomic_mass", "unc_am", "binding", "unc_ba",
                "me_systematics", "ENSDFpublicationcut-off", "ENSDFauthors", "Extraction_date"}
    require(fields and len(set(fields)) == len(fields) and required <= set(fields), "iaea_header")
    out = []
    for line, row in enumerate(reader, 2):
        require(None not in row and all(v is not None for v in row.values()), "iaea_ragged_row", line)
        z, n = number(row["z"]), number(row["n"])
        require(z.is_integer() and n.is_integer() and 0 <= z <= 118 and n >= 0 and z+n > 0,
                "nuclide_integer_identity", line)
        z, n = int(z), int(n)
        name = text(row["symbol"], "nuclide.symbol")
        require((z == 0 and name == "n") or (z > 0 and re.fullmatch("[A-Z][a-z]?", name)),
                "nuclide_element_symbol", line)
        energy = number(row["energy"]) if row["energy"] else None
        ripl = number(row["ripl_shift"]) if row["ripl_shift"] else None
        require(energy is None or energy >= 0, "nuclide_negative_level", line)
        level = {"energy_numeric_keV": energy, "unknown_shift_label": row["energy_shift"],
                 "ripl_assigned_shift_keV": ripl,
                 "resolved_ground_state": row["energy_shift"] == "" and energy == 0}
        op = row["operator_hl"].strip()
        require(op in ("", "AP", "GT", "GE", "LT", "LE"), "half_life_operator", op)
        if row["half_life"] == "STABLE":
            require(not row["half_life_sec"] and not op, "stable_half_life_conflict")
            hl = {"kind": "stable", "seconds": None, "operator": op, "uncertainty_seconds": None}
        elif not row["half_life_sec"]:
            hl = {"kind": "unknown", "seconds": None, "operator": op, "uncertainty_seconds": None}
        else:
            seconds = number(row["half_life_sec"])
            require(seconds > 0, "half_life_nonpositive", line)
            uncertainty = number(row["unc_hls"]) if row["unc_hls"] else None
            require(uncertainty is None or uncertainty >= 0, "negative_uncertainty", line)
            hl = {"kind": "estimate" if not op else "approximate" if op == "AP" else "bound",
                  "seconds": seconds, "operator": op, "uncertainty_seconds": uncertainty}
        mass = None if not row["atomic_mass"] else number(row["atomic_mass"]) * 1e-6
        mass_unc = None if not row["unc_am"] else number(row["unc_am"]) * 1e-6
        require(mass is None or mass > 0, "nuclide_nonpositive_mass", line)
        require(mass_unc is None or mass_unc >= 0, "negative_uncertainty", line)
        branches = []
        for i in (1, 2, 3):
            mode = row["decay_" + str(i)]
            val = row["decay_" + str(i) + "_%"]
            if mode:
                branching = number(val) / 100 if val else None
                require(branching is None or 0 <= branching <= 1, "decay_branching_range", line)
                branches.append({"mode": mode, "fraction": branching,
                                 "raw_uncertainty": row["unc_" + str(i)]})
        payload = {"type": "nuclide_ground_states_entry", "Z": z, "N": n, "A": z+n, "symbol": name,
                   "level": level,
                   "half_life": hl, "atomic_mass_u": mass, "atomic_mass_uncertainty_u": mass_unc,
                   "mass_semantics": "Neutral atomic mass in u, converted from source micro-AMU; neutron row is explicitly Z=0.",
                   "mass_from_systematics": row["me_systematics"], "listed_decay_modes": branches,
                   "decay_completeness": "Only three most probable modes; not a complete reaction network.",
                   "binding_energy_per_nucleon_keV": number(row["binding"]) if row["binding"] else None,
                   "binding_uncertainty_keV": number(row["unc_ba"]) if row["unc_ba"] else None,
                   "evaluation_cutoff": row["ENSDFpublicationcut-off"], "evaluators": row["ENSDFauthors"],
                   "source_extraction_date": row["Extraction_date"], "raw_row": row}
        out.append(draft(f"IAEA/nuclide/{z}/{n}/ground_states_row", "entity", payload,
                         label=f"{name}-{z+n} " + ("ground state" if level["resolved_ground_state"] else "evaluated level"),
                         unknowns=["decay_energy_deposition", "full_decay_network"] +
                         ([] if level["resolved_ground_state"] else ["level_assignment_unresolved"])))
    require(out, "empty_capture")
    return out


FORCE_ADAPTERS = {"nist_codata": nist_constants, "jpl_gravity": jpl_gravity,
                  "cantera_nasa7": cantera_nasa7, "nist_al6061": nist_aluminum,
                  "iaea_ground_states": iaea_nuclides}
