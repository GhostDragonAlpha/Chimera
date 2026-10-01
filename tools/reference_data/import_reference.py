"""Build the reference-data store from the pinned cached artifacts.

Writes:
  data/reference_store.json     -- the reference records (7 families):
        Source, reference_entity, relationship, property_assertion,
        geometry_asset (none this run -- recorded gap), mapping, model_definition
  data/import_provenance.json   -- the provenance table of record: exact
        sources/releases, sha256 checksums, licenses, coverage, known gaps.

IDEMPOTENT: records are keyed by stable authored ids derived from
(source_id, external_id). Importing the same pinned data twice creates
nothing new and changes no bytes (verified by acceptance test 6). A record
that differs on re-import is reported as a CONFLICT and kept (never silently
overwritten, never averaged).

Every assertion carries: quantity, units, value, conditions (specimen/species,
loading, temperature, strain-rate, frame where relevant), source + version,
status. Status is EXTRACTED -- "a source states it", NOT "physics verified".
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import fetch_cache  # noqa: E402
import parsers  # noqa: E402
import sources as sources_mod  # noqa: E402

DATA_DIR = os.path.join(HERE, "data")
STORE_PATH = os.path.join(DATA_DIR, "reference_store.json")
PROV_PATH = os.path.join(DATA_DIR, "import_provenance.json")

FETCHED_UTC = "2026-09-15"  # first pin date (pins freeze the bytes)


def _prov_entry(sid, entry, artifact_prov):
    """Assemble the provenance record for one source from the registry +
    the fetch cache results."""
    arts = {k.split("::", 1)[1]: v for k, v in artifact_prov.items()
            if k.startswith(sid + "::")}
    return {
        "source_id": sid,
        "family": entry["family"],
        "entry_url": entry["entry_url"],
        "resolved_url": entry["resolved_url"],
        "release": entry["release"],
        "license": entry["license"],
        "license_evidence": entry["license_evidence"],
        "artifacts": arts,
        "parser": entry["parser"],
        "coverage": entry["coverage"],
        "known_gaps": entry["known_gaps"],
        "first_pinned_utc": FETCHED_UTC,
    }


# ---------------------------------------------------------------------------
# record builders (all deterministic)
# ---------------------------------------------------------------------------

def records_for_uberon(artifact_prov):
    path = os.path.join(fetch_cache.CACHE_DIR, "uberon",
                        "appendicular-minimal.obo")
    parsed = parsers.parse_obo(path)
    objs, rels = [], []
    n_structural = 0
    for t in parsed["terms"]:
        if t["is_typedef"] or not t["id"]:
            continue
        if not t["id"].startswith("UBERON:"):
            n_structural += 1  # BFO/oboInOwl stanzas: present, not projected
            continue
        oid = "ref.uberon." + t["id"].replace(":", "_")
        objs.append({
            "id": oid, "kind": "reference_entity", "name": t["name"] or t["id"],
            "classification": None, "status": "extracted", "priority": None,
            "build_rank": None, "inventory_anchor": None, "spatial": None,
            "geometry": None, "physical": None, "attachments": [],
            "dependencies": [], "evidence": [], "falsifier": {},
            "external_ids": [t["id"]],
            "definition": t["definition"],
            "synonyms": t["synonyms"][:8],
            "unknowns": [],
            "notes": "EXTRACTED: Uberon states it; not a creature part, not "
                     "physically verified. Human anatomy is REFERENCE, never "
                     "automatically Chimera proportions.",
            "provenance": {"source_id": "uberon.appendicular-minimal",
                           "release": "v2026-06-23", "license": "CC BY 3.0"},
        })
    id2obj = {o["external_ids"][0]: o["id"] for o in objs}
    for t in parsed["terms"]:
        if not t["id"] or not t["id"].startswith("UBERON:"):
            continue
        src = id2obj[t["id"]]
        for parent in t["is_a"]:
            if parent in id2obj:
                rels.append({"src": src, "rel": "is_a", "dst": id2obj[parent],
                             "note": "rdfs:subClassOf (structural; is_a is not an "
                                     "RO relation -- meaning recorded, not renamed)"})
        for rtype, tgt in t["relationships"]:
            if tgt in id2obj:
                rels.append({"src": src, "rel": f"ref:{rtype}",
                             "dst": id2obj[tgt],
                             "note": f"Uberon relationship '{rtype}' (meaning "
                                     f"defined in the Relation Ontology; see "
                                     f"rel.ro.* records)"})
    meta = {"n_terms": len(parsed["terms"]),
            "n_uberon_entities": len(objs),
            "n_structural_stanzas_not_projected": n_structural,
            "n_edges_projected": len(rels),
            "omissions": "the simplified graph projection preserves is_a and "
                         "named relationships; it OMITS intersection_of axioms, "
                         "disjointness, and property_value annotations (present "
                         "in the pinned cache, re-parseable any time)"}
    return objs, rels, meta


def records_for_ro(artifact_prov):
    path = os.path.join(fetch_cache.CACHE_DIR, "ro", "ro-base.owl")
    rels_in = parsers.parse_ro_owl(path)
    objs = []
    for r in rels_in:
        objs.append({
            "id": "rel.ro." + r["short"].replace(" ", "_"), "kind": "relationship",
            "name": f"{r['short']} ({r['label']})" if r["label"] else r["short"],
            "classification": None, "status": "extracted", "priority": None,
            "build_rank": None, "inventory_anchor": None, "spatial": None,
            "geometry": None, "physical": None, "attachments": [],
            "dependencies": [], "evidence": [], "falsifier": {},
            "external_ids": [r["iri"]],
            "definition": r["definition"],
            "unknowns": ["domain/range axioms and property chains NOT projected "
                         "(in the pinned OWL; re-parseable)"],
            "notes": "relation TYPE from the Relation Ontology; the reference "
                     "store's ref:* edges cite these meanings",
            "provenance": {"source_id": "ro.base", "release": "v2026-09-04",
                           "license": "CC0 1.0"},
        })
    return objs, {"n_selected": len(objs), "n_selected_available": len(parsers.RO_SELECTED)}


def records_for_qudt(artifact_prov):
    objs = []
    for key, prov in artifact_prov.items():
        if not key.startswith("qudt.units::"):
            continue
        rel = prov["cached_path"]
        path = os.path.join(fetch_cache.CACHE_DIR, rel.replace("/", os.sep))
        rec = parsers.parse_qudt_ttl(path)
        if not rec["subject"]:
            continue  # unparseable artifact: reported, never guessed
        short = rec["subject"].split(":")[-1]
        is_unit = rel.startswith("qudt/unit_")
        oid = ("ref.qudt.unit." if is_unit else "ref.qudt.quantitykind.") + short
        if is_unit:
            objs.append({
                "id": oid, "kind": "reference_entity", "name": rec["label"] or short,
                "classification": None, "status": "extracted", "priority": None,
                "build_rank": None, "inventory_anchor": None, "spatial": None,
                "geometry": None, "physical": None, "attachments": [],
                "dependencies": [], "evidence": [], "falsifier": {},
                "external_ids": [rec["subject"].replace("unit:", "unit:")
                                 .replace("quantitykind:", "quantitykind:")],
                "symbol": rec["symbol"],
                "si_conversion_multiplier": rec["conversion_multiplier"],
                "dimension_vector": rec["dimension_vector"],
                "quantity_kinds": rec["quantity_kinds"],
                "unknowns": [] if rec["conversion_multiplier"] else
                            ["SI conversion multiplier absent in the served doc"],
                "notes": "unit definition (QUDT); factor-unit structure omitted "
                         "in projection (present in the pinned TTL)",
                "provenance": {"source_id": "qudt.units", "release": "live LOD "
                               "endpoint, pinned by sha256", "license": "UNKNOWN "
                               "(not stated in served documents)"},
            })
        else:
            objs.append({
                "id": oid, "kind": "reference_entity", "name": rec["label"] or short,
                "classification": None, "status": "extracted", "priority": None,
                "build_rank": None, "inventory_anchor": None, "spatial": None,
                "geometry": None, "physical": None, "attachments": [],
                "dependencies": [], "evidence": [], "falsifier": {},
                "external_ids": [rec["subject"]],
                "applicable_units": rec["applicable_units"],
                "dimension_vector": rec["dimension_vector"],
                "unknowns": [],
                "notes": "quantity kind (QUDT)",
                "provenance": {"source_id": "qudt.units", "release": "live LOD "
                               "endpoint, pinned by sha256", "license": "UNKNOWN"},
            })
    return objs


def records_for_osim(artifact_prov):
    path = os.path.join(fetch_cache.CACHE_DIR, "osim", "leg6dof9musc.osim")
    m = parsers.parse_osim(path)
    objs = []
    # ModelDefinition record
    objs.append({
        "id": "def.osim.leg6dof9musc", "kind": "model_definition",
        "name": f"OpenSim {m['model_name']} (model definition record)",
        "classification": None, "status": "extracted", "priority": None,
        "build_rank": None, "inventory_anchor": None, "spatial": None,
        "geometry": None, "physical": None, "attachments": [],
        "dependencies": [], "evidence": [], "falsifier": {},
        "external_ids": ["osim:leg6dof9musc"],
        "osim_version": m["osim_version"],
        "n_bodies": m["n_bodies"], "n_joints": m["n_joints"],
        "n_muscles": m["n_muscles"],
        "bodies": [b["name"] for b in m["bodies"]],
        "joints": [j["name"] for j in m["joints"]],
        "muscles": [x["name"] for x in m["muscles"]],
        "unknowns": ["no license terms for the source repo (recorded UNKNOWN)"],
        "notes": "IMPORTED, NEVER EXECUTED: parsed as XML only. The model is a "
                 "human RIGHT-leg reference -- a REFERENCE for structures and "
                 "parameter magnitudes, not a creature definition.",
        "provenance": {"source_id": "opensim.leg6dof9musc",
                       "release": "opensim-models master 2025-11-05 (pinned by sha256)",
                       "license": "NOT STATED (recorded UNKNOWN)"},
    })
    # reference entities for bodies + joints
    for b in m["bodies"]:
        objs.append({
            "id": f"ref.osim.leg6dof9musc.body.{b['name']}", "kind": "reference_entity",
            "name": f"OpenSim body {b['name']}",
            "classification": None, "status": "extracted", "priority": None,
            "build_rank": None, "inventory_anchor": None, "spatial": None,
            "geometry": None, "physical": None, "attachments": [],
            "dependencies": [], "evidence": [], "falsifier": {},
            "external_ids": [f"osim:leg6dof9musc/Body/{b['name']}"],
            "definition": f"rigid body in the leg6dof9musc model"
                          + (f", mass {b['mass_kg']} kg" if b["mass_kg"] else
                             " (no mass element parsed)"),
            "unknowns": [], "notes": "reference body; human geometry, not Chimera",
            "provenance": {"source_id": "opensim.leg6dof9musc",
                           "release": "master 2025-11-05", "license": "NOT STATED"},
        })
    for j in m["joints"]:
        objs.append({
            "id": f"ref.osim.leg6dof9musc.joint.{j['name']}", "kind": "reference_entity",
            "name": f"OpenSim joint {j['name']}",
            "classification": None, "status": "extracted", "priority": None,
            "build_rank": None, "inventory_anchor": None, "spatial": None,
            "geometry": None, "physical": None, "attachments": [],
            "dependencies": [], "evidence": [], "falsifier": {},
            "external_ids": [f"osim:leg6dof9musc/Joint/{j['name']}"],
            "definition": f"{j['type']} joint" +
                          (f" between {'/'.join(p.split('/')[-1] for p in j['parent_frames'])}"
                           if j["parent_frames"] else ""),
            "unknowns": [], "notes": "reference joint",
            "provenance": {"source_id": "opensim.leg6dof9musc",
                           "release": "master 2025-11-05", "license": "NOT STATED"},
        })
    # property assertions: one per muscle parameter (units, conditions, source)
    CONDITIONS = {
        "max_isometric_force_N": ("isometric, maximally activated", "N"),
        "optimal_fiber_length_m": ("at optimal fiber length", "m"),
        "tendon_slack_length_m": ("tendon unloaded (slack)", "m"),
        "pennation_angle_at_optimal_rad": ("at optimal fiber length", "rad"),
        "max_contraction_velocity": ("contractile-element model constant "
                                     "(fiber lengths/s)", "1/s"),
        "activation_time_constant_s": ("activation dynamics", "s"),
        "deactivation_time_constant_s": ("deactivation dynamics", "s"),
    }
    for mus in m["muscles"]:
        for field, (condition, unit) in CONDITIONS.items():
            val = mus.get(field)
            if val is None:
                continue
            objs.append({
                "id": f"pa.osim.leg6dof9musc.{mus['name']}.{field}",
                "kind": "property_assertion",
                "name": f"{mus['name']} {field} = {val} {unit}",
                "classification": None, "status": "extracted", "priority": None,
                "build_rank": None, "inventory_anchor": None, "spatial": None,
                "geometry": None, "physical": None, "attachments": [],
                "dependencies": [], "evidence": [], "falsifier": {},
                "external_ids": [f"osim:leg6dof9musc/Muscle/{mus['name']}#{field}"],
                "quantity": field,
                "units": unit,
                "value": val,
                "range": None,
                "conditions": {
                    "specimen": "human (Rajagopal-line leg model, 21 cadaver + "
                                "24 MRI subjects upstream per docs/JOINT_ATLAS.md S2)",
                    "loading": condition,
                    "temperature": "unknown",
                    "strain_rate": "unknown (except contraction-velocity constant)",
                    "frame": "OpenSim model frame (leg6dof9musc)",
                    "side": "right leg only",
                },
                "unknowns": [k for k, v in
                             {"temperature": "unknown", "strain_rate": "unknown"}.items()],
                "notes": "EXTRACTED: the SOURCE STATES it -- not physically "
                         "verified, not a creature parameter. Selecting it for "
                         "the creature is an explicit adaptation decision.",
                "provenance": {"source_id": "opensim.leg6dof9musc",
                               "release": "master 2025-11-05",
                               "license": "NOT STATED"},
            })
    # reference-internal candidate mappings (name-token based, CANDIDATE only)
    uberon_names = {}  # filled by the caller below (needs uberon objects)
    return objs, m, uberon_names


# candidate mappings BETWEEN datasets (uberon <-> osim), computed on exact
# lowercase name tokens only -- similarity yields CANDIDATES, never equivalence
UBERON_OSIM_TOKENS = {
    "femur": "femur_r",
    "tibia": "tibia_r",
    "fibula": None,          # not in leg6dof9musc (recorded as a known gap)
    "patella": "patella_r",
    "talus": "talus_r",
    "calcaneus": "calcn_r",
    "phalanx": "toes_r",
}


def build_all(refresh: bool = False):
    artifact_prov = fetch_cache.ensure_all_cached(sources_mod.SOURCES,
                                                  refresh=refresh)
    prov_table = {sid: _prov_entry(sid, entry, artifact_prov)
                  for sid, entry in sources_mod.SOURCES.items()}

    objs, rels, metas = [], [], {}
    ub_objs, ub_rels, ub_meta = records_for_uberon(artifact_prov)
    objs += ub_objs
    rels += ub_rels
    metas["uberon"] = ub_meta
    ro_objs, ro_meta = records_for_ro(artifact_prov)
    objs += ro_objs
    metas["ro"] = ro_meta
    q_objs = records_for_qudt(artifact_prov)
    objs += q_objs
    metas["qudt"] = {"n_records": len(q_objs)}
    o_objs, o_model, _ = records_for_osim(artifact_prov)
    objs += o_objs
    metas["osim"] = {"n_bodies": o_model["n_bodies"],
                     "n_joints": o_model["n_joints"],
                     "n_muscles": o_model["n_muscles"],
                     "n_property_assertions": sum(1 for o in o_objs
                                                  if o["kind"] == "property_assertion")}

    # dataset-candidate mappings: exact anatomical-name token match only
    by_name = {}
    for o in ub_objs:
        for tok in re_tokens(o["name"]):
            by_name.setdefault(tok, []).append(o["id"])
    n_map = 0
    for uberon_tok, osim_body in UBERON_OSIM_TOKENS.items():
        if osim_body is None:
            metas.setdefault("mappings", {}).setdefault("unmatched", []).append(
                {"uberon_token": uberon_tok,
                 "reason": "no OpenSim body carries this bone (known gap: "
                           "leg6dof9musc has no fibula; recorded, not forced)"})
            continue
        cands = by_name.get(uberon_tok, [])
        if not cands:
            continue
        for c in cands[:1]:  # deterministic: first by id if several
            objs.append({
                "id": f"map.uberon-{uberon_tok}__osim-{osim_body}",
                "kind": "mapping",
                "name": f"CANDIDATE: UBERON {uberon_tok} ~ osim body {osim_body}",
                "classification": None, "status": "extracted", "priority": None,
                "build_rank": None, "inventory_anchor": None, "spatial": None,
                "geometry": None, "physical": None, "attachments": [],
                "dependencies": [], "evidence": [], "falsifier": {},
                "mapping_type": "candidate",
                "meaning": "NAME-TOKEN MATCH ONLY. A candidate, NEVER an "
                           "equivalence; confirming or rejecting it is an "
                           "explicit human/mapping-record decision.",
                "left": c, "right": f"ref.osim.leg6dof9musc.body.{osim_body}",
                "unknowns": [],
                "notes": "similar names produce candidates, not automatic "
                         "equivalences (brief, reference-data ingestion)",
                "provenance": {"source_id": "join:uberon+opensim",
                               "rule": "exact lowercase anatomical-name token"},
            })
            n_map += 1
    metas["mappings"] = {"n_dataset_candidates": n_map}

    # Source records (one per registry entry)
    for sid, entry in sources_mod.SOURCES.items():
        objs.append({
            "id": "src." + sid, "kind": "source", "name": f"{sid} (pinned source)",
            "classification": None, "status": "extracted", "priority": None,
            "build_rank": None, "inventory_anchor": None, "spatial": None,
            "geometry": None, "physical": None, "attachments": [],
            "dependencies": [], "evidence": [], "falsifier": {},
            "external_ids": [entry["entry_url"]],
            "family": entry["family"], "release": entry["release"],
            "license": entry["license"],
            "license_evidence": entry["license_evidence"],
            "coverage": entry["coverage"], "known_gaps": entry["known_gaps"],
            "unknowns": [],
            "notes": "pinned source of record; checksums in data/pins.json + "
                     "import_provenance.json",
            "provenance": {"source_id": sid, "release": entry["release"],
                           "license": entry["license"]},
        })
    # provenance relation: every non-source record cites its Source
    for o in objs:
        sid = (o.get("provenance") or {}).get("source_id")
        if sid and o["kind"] != "source":
            rels.append({"src": o["id"], "rel": "derived_from",
                         "dst": "src." + sid, "note": "provenance citation"})

    store = {
        "schema_version": "1.0.0",
        "generated_note": "deterministic; regenerated byte-identical from the "
                          "pinned cache (see import_provenance.json)",
        "objects": sorted(objs, key=lambda o: o["id"]),
        "relations": sorted((json.dumps(r, sort_keys=True) for r in rels)),
    }
    store["relations"] = [json.loads(s) for s in store["relations"]]
    return store, prov_table, metas


def re_tokens(name: str) -> list:
    return [t for t in re.findall(r"[a-z]+", (name or "").lower())
            if len(t) > 3]


def import_all(refresh: bool = False, force_rebuild: bool = False) -> dict:
    """Idempotent import. Returns a report. Second run on the same pinned data:
    created == 0, unchanged == all, store bytes identical."""
    store, prov_table, metas = build_all(refresh=refresh)
    os.makedirs(DATA_DIR, exist_ok=True)
    report = {"mode": "force_rebuild" if force_rebuild else "merge",
              "created": 0, "unchanged": 0, "conflicts": [],
              "counts_by_kind": {}, "metas": metas}
    for o in store["objects"]:
        k = o["kind"]
        report["counts_by_kind"][k] = report["counts_by_kind"].get(k, 0) + 1
    existing = None
    if os.path.exists(STORE_PATH) and not force_rebuild:
        with open(STORE_PATH, encoding="utf-8") as f:
            existing = json.load(f)
    if existing is None:
        report["created"] = len(store["objects"])
        _write_store(store)
    else:
        old = {o["id"]: o for o in existing["objects"]}
        merged = []
        for o in store["objects"]:
            prev = old.get(o["id"])
            if prev is None:
                report["created"] += 1
                merged.append(o)
            elif prev == o:
                report["unchanged"] += 1
                merged.append(prev)
            else:
                report["conflicts"].append({
                    "id": o["id"],
                    "handling": "kept the EXISTING record (never silently "
                                "overwritten, never averaged); re-run with "
                                "--force-rebuild to adopt the re-computed record"})
                merged.append(prev)
        for oid, o in old.items():
            if oid not in {m["id"] for m in merged}:
                merged.append(o)  # records only in the store stay (provenance)
        store["objects"] = sorted(merged, key=lambda x: x["id"])
        _write_store(store)
    with open(PROV_PATH, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"generated_note": "provenance table of record",
                   "sources": prov_table, "metas": metas},
                  f, indent=1, ensure_ascii=False)
    report["store_path"] = os.path.normpath(STORE_PATH)
    report["prov_path"] = os.path.normpath(PROV_PATH)
    return report


def _write_store(store: dict) -> None:
    tmp = STORE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(store, f, indent=1, ensure_ascii=False)
    os.replace(tmp, STORE_PATH)
