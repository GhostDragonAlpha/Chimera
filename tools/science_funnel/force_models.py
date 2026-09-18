"""Compile explicit graph selections into bounded native SI models.

Historical assertion producer hashes stay historical. This compiler independently
replays their pinned source semantics with the current adapter, without re-IDing
the graph or pretending an old bundle was produced by this implementation.
"""
import argparse
import copy
from decimal import Decimal, localcontext
from pathlib import Path

from .common import canonical, digest, loads, local_file, number, require, sha
from .force_adapters import FORCE_ADAPTERS
from .force_catalog import DATA, LOCK, ROOT, lock

SCHEMA = "chimera.force_models.v1"
LAWS = ["point_mass_gravity", "NASA7_ideal_gas_species",
        "ideal_gas_mixture_energy_closure", "nist_solid_property_curves",
        "evaluated_parent_decay", "evaluated_binding_energy"]
RECIPE = "model.force_library.v1"
KEYS = ("external_id", "record_type", "label", "payload", "unknowns")


def compile_packet(graph, source_root=DATA):
    objects = graph.objects if hasattr(graph, "objects") else graph["objects"]
    recipe = objects[RECIPE]
    contract = recipe["physical"]["contract"]
    require(contract.get("packet_schema") == SCHEMA, "model_packet_schema")
    require(contract.get("allowed_laws") == LAWS, "model_law_inventory")
    require(sha(LOCK.read_bytes()) == contract.get("source_lock_sha256"),
            "model_source_lock_drift")
    manifest_lock = lock()
    artifacts = {a["path"]: a for a in manifest_lock["artifacts"]}
    blobs = {}
    for name, art in artifacts.items():
        raw = local_file(source_root, name).read_bytes()
        require(len(raw) == art["bytes"] and sha(raw) == art["sha256"],
                "model_source_pin_drift", name)
        blobs[name] = raw
    sources = {s["adapter"]: s for s in manifest_lock["sources"]}
    require(len(sources) == len(manifest_lock["sources"]), "duplicate_model_source")
    replay = {}
    for adapter, source in sources.items():
        rows = FORCE_ADAPTERS[adapter](blobs[source["data"]], {}, Path(source_root) / source["data"])
        mapping = {}
        for row in rows:
            require("refusal" not in row, "model_source_replay_refusal")
            require(row["external_id"] not in mapping, "model_source_duplicate")
            mapping[row["external_id"]] = row
        replay[adapter] = mapping
    inputs = contract["inputs"]
    require(set(inputs) == {"constants", "gravity", "gas_species", "solid_curves",
                            "nuclides", "element_masses"}, "model_input_inventory")
    ids = list(inputs["constants"].values())
    for group in inputs.keys() - {"constants"}:
        require(isinstance(inputs[group], list), "model_input_list")
        ids.extend(inputs[group])
    require(len(ids) == len(set(ids)), "duplicate_model_selection")
    selected = {}
    for rid in ids:
        require(rid in objects, "model_input_missing", rid)
        obj = objects[rid]
        if rid in inputs["element_masses"]:
            continue
        record = obj.get("science_funnel", {})
        body = {k: v for k, v in record.items() if k != "id"}
        require(record.get("id") == rid == "data.assertion." + digest(body),
                "model_assertion_content_drift", rid)
        adapter = record.get("adapter")
        require(adapter in sources, "model_adapter_unsupported")
        source = sources[adapter]
        require(record["source"] == {k: source[k] for k in
                ("id", "release", "license", "url", "attribution", "scope")},
                "model_source_identity_drift")
        require(record["artifact"] == {"id": source["data"],
                "sha256": artifacts[source["data"]]["sha256"]}, "model_artifact_identity")
        expected = replay[adapter].get(record["external_id"])
        require(expected is not None and {k: record[k] for k in KEYS} == expected,
                "model_semantic_replay_mismatch", rid)
        if record["record_type"] == "measurement":
            require(obj.get("value") == record["payload"]["value_si"] and
                    obj.get("units") == record["payload"]["unit_si"],
                    "model_graph_projection_drift")
        selected[rid] = record

    def refs(rid):
        rec = selected[rid]
        return {"record_id": rid, "external_id": rec["external_id"],
                "source_sha256": rec["artifact"]["sha256"], "unknowns": rec["unknowns"]}

    def group(name, adapter):
        for rid in inputs[name]:
            rec = selected[rid]
            require(rec["adapter"] == adapter, "model_selection_family_mismatch", rid)
            yield rid, rec["payload"]

    constants = {}
    for subject, rid in inputs["constants"].items():
        rec = selected[rid]
        p = rec["payload"]
        require(rec["adapter"] == "nist_codata" and p["subject"] == subject and
                rec["record_type"] == "measurement", "model_constant_identity")
        constants[subject] = {**refs(rid), **{k: p[k] for k in
                ("value_si", "unit_si", "decimal_value", "uncertainty_si",
                 "exact_physical_definition", "quantity", "dimensions")}}
    with localcontext() as ctx:
        ctx.prec = 50
        kb = constants["Boltzmann constant"]
        na = constants["Avogadro constant"]
        mu = constants["atomic mass constant"]
        require(kb["exact_physical_definition"] and na["exact_physical_definition"],
                "derived_R_requires_exact_definitions")
        R = Decimal(kb["decimal_value"]) * Decimal(na["decimal_value"])
        molar_unit = Decimal(mu["decimal_value"]) * Decimal(na["decimal_value"])

    # This explicit reduction promotes only AtomicMass for selected stable
    # terrestrial element labels, not every periodic-table numeric column.
    ep = ROOT / "tools/science_funnel/data/pubchem/periodic_table.json"
    ep_raw = ep.read_bytes()
    ep_hash = sha(ep_raw)
    table = loads(ep_raw)["Table"]
    columns = table["Columns"]["Column"]
    require(len(columns) == len(set(columns)), "element_duplicate_columns")
    rows = {}
    for row in table["Row"]:
        cells = row["Cell"]
        require(len(cells) == len(columns), "element_row_shape")
        cells = dict(zip(columns, cells))
        z = int(cells["AtomicNumber"])
        require(z not in rows, "element_duplicate_identity")
        rows[z] = cells
    elements = {}
    for rid in inputs["element_masses"]:
        obj = objects[rid]
        z = obj["external_ids"]["atomic_number"]
        require(obj["provenance"]["artifact_sha256"] == ep_hash and
                obj["reference_payload"]["raw_source_cells"] == rows[z] and
                obj["external_ids"]["symbol"] == rows[z]["Symbol"],
                "element_source_drift")
        raw_mass = rows[z]["AtomicMass"]
        require("[" not in raw_mass and "(" not in raw_mass, "element_mass_not_scalar")
        ar = Decimal(raw_mass)
        require(ar.is_finite() and ar > 0, "element_mass_invalid")
        symbol = rows[z]["Symbol"]
        require(symbol not in elements, "element_selection_duplicate")
        elements[symbol] = {"record_id": rid, "relative_atomic_mass": float(ar),
            "molar_mass_kg_per_mol": float(ar * molar_unit),
            "source_sha256": ep_hash, "uncertainty": None,
            "scope": "Tabulated conventional element mass; not arbitrary isotope abundance.",
            "unit_definition_url": "https://pubchem.ncbi.nlm.nih.gov/periodic-table/atomic-mass"}

    gravity, gases, solids, nuclides = {}, {}, {}, {}
    for rid, p in group("gravity", "jpl_gravity"):
        require(p["unit_si"] == "m3/s2", "gravity_unit")
        key = p["naif_id"]
        require(key not in gravity, "gravity_duplicate_body")
        gravity[key] = {**refs(rid), "mu_m3_s2": p["value_si"], "name": p["subject"],
                        "mass_scope": p["conditions"]["mass_scope"], "model": "point_mass"}
    for rid, p in group("gas_species", "cantera_nasa7"):
        d = p["definition"]
        require(d["model"] == "NASA7", "gas_model_family")
        name = d["species"]
        require(name not in gases, "gas_duplicate_species")
        require(set(d["composition"]) <= set(elements), "species_element_mass_missing")
        mass = sum(number(n) * elements[e]["molar_mass_kg_per_mol"]
                   for e, n in d["composition"].items())
        gases[name] = {**refs(rid), **{k: d[k] for k in
             ("model", "temperature_ranges_K", "coefficients", "reference_pressure_Pa",
              "composition")}, "molar_mass_kg_per_mol": mass}
    for rid, p in group("solid_curves", "nist_al6061"):
        d = p["definition"]
        require(d["model"] in ("log10_polynomial", "polynomial", "polynomial_low_constant"),
                "solid_model_family")
        key = d["quantity"]
        require(key not in solids, "solid_duplicate_quantity")
        solids[key] = {**refs(rid), **{k: copy.deepcopy(v) for k, v in d.items()
                      if k not in ("raw_table", "coefficients_order")}}
    for rid, p in group("nuclides", "iaea_ground_states"):
        key = str(p["Z"]) + ":" + str(p["N"])
        require(key not in nuclides, "nuclide_duplicate_identity")
        nuclides[key] = {**refs(rid), **{k: copy.deepcopy(p[k]) for k in
            ("Z", "N", "A", "symbol", "half_life", "level", "atomic_mass_u",
             "binding_energy_per_nucleon_keV", "source_extraction_date",
             "evaluation_cutoff", "decay_completeness")}}
    packet = {"schema": SCHEMA, "recipe_id": RECIPE, "recipe_sha256": digest(recipe),
        "input_sha256": digest({rid: objects[rid] for rid in sorted(ids)}),
        "source_lock_sha256": sha(LOCK.read_bytes()),
        "compiler_sha256": sha(Path(__file__).read_bytes()),
        "semantic_replay": "Pinned raw artifacts replayed; historical producer identities retained.",
        "qualification": "Compiled bounded models; see separate validation receipt, not a game qualification.",
        "R_J_per_mol_K": float(R), "R_exact_decimal": str(R),
        "constants": constants, "elements": elements,
        "gravity": gravity, "gas_species": gases, "solid_curves": solids, "nuclides": nuclides,
        "energy_convention": "NASA7 formation/reference terms preserved. Nuclear Q is not heat deposition."}
    packet["packet_sha256"] = digest(packet)
    return packet


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph", type=Path,
                        default=ROOT / "tools/creature_graph/data/creature_graph.json")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    from tools.creature_graph.store import merged_payload
    packet = compile_packet(merged_payload(str(args.graph)))
    raw = canonical(packet)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(raw)
    print(canonical({"file": str(args.output), "bytes": len(raw),
                     "packet_sha256": packet["packet_sha256"]}).decode())


if __name__ == "__main__":
    main()
