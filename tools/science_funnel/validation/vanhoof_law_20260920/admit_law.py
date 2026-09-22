"""VLAW admit_law: the funnel admission of the Vanhoof S2 macaque data at the
registered constant, per the prereg's admission_tiers_original and the prestage
RUNBOOK's record shapes (vanhoof_prestage_20260921/admit_vanhoof.py output contract).

Rule-0 discipline (prereg receipt.json + constants.json in this directory):
  * Verdicts come from the ONE math path (laws_registered.compute_rows) and are
    cross-checked against the committed laws_registered.json before anything is
    admitted (two artifacts must agree exactly).
  * Values are the landed 654 TENTATIVE pins: read from the pinned
    reconciliation.json, never re-read from images, never edited (F3). Every
    record's printed value is asserted equal (Decimal) to every pass record
    carrying the same (muscle, specimen, field) key in passA/passB.
  * admit_vanhoof.admit itself is NOT modified and NOT forced: it requires all 7
    canonical fields and the measured manifest carries 3 (mass_g/fl_mm/pcsa_mm2)
    -- the intake's F-MANIFEST named branch. This driver emits the SAME contract
    shapes from the lane (draft records, batch.property.measurement v1,
    units.convert SI, named refusals with weights, count identity, content-derived
    external ids vanhoof:s002:{muscle}:{spec}:{field} for idempotent replay), and
    registers the manifest honestly as a 3-field source.
  * Graph apply / controller admission / fleet qualification are NOT run from this
    lane (shared state; F5): the funnel's own mode "proposals are reviewable files;
    generating one is not a claim of admission" is the honest ceiling; downstream
    steps are named in the receipt.
  * Deterministic (F4): frozen inputs only, canonical JSON, no randomness, no
    timestamps in derived artifacts.
"""
import glob
import hashlib
import json
import os
import sys
from collections import defaultdict
from decimal import Decimal

BASE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(BASE, "..", "..", "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from tools.science_funnel.common import canonical, digest, draft, number  # noqa: E402
from tools.science_funnel.units import convert  # noqa: E402
import laws_registered as L  # noqa: E402

TLANE = os.path.join(BASE, "..", "vanhoof_transcription_20260920")
RECONCILE_PATH = os.path.join(TLANE, "reconciliation.json")
CROPS_PATH = os.path.join(TLANE, "crops_manifest.json")
LAWS_REGISTERED_PATH = os.path.join(BASE, "laws_registered.json")
CONSTANTS_PATH = os.path.join(BASE, "constants.json")

SOURCE_TIFF_SHA256 = "cb9e91be3d2345182b6d2b956245b76905243d4bbf37fff79c3d96a802e5debe"
SHEET = "JOA-238-321-s002"
REFUSAL_TAXONOMY_CLOSED = {
    "row_closure_violation", "marker_absent", "marker_absent_cfr",
    "marker_crossref_APB", "marker_crossref_FDP", "merged_cell_covered",
}
FIELD_SPECS = {"mass_g": ("g", "mass"), "fl_mm": ("mm", "length"), "pcsa_mm2": ("mm2", "area")}
PARAMETER = {"mass_g": "muscle mass", "fl_mm": "fascicle length",
             "pcsa_mm2": "physiological cross-sectional area"}
UNIT_SOURCE = {"mass_g": "g", "fl_mm": "mm", "pcsa_mm2": "mm2"}
DATASET_NOTE = ("Vanhoof MJM, van Leeuwen T, Galletta L, Vereecke EE (2021) J Anat "
                "238(2):321-337, Part II Table S2 (adult Macaca mulatta Mm1-Mm7); "
                "double-entry vision transcription lane vanhoof_transcription_20260920")
LAW_FORM = "PCSA_pred = 1e6*(mass_g/1000)/(rho_g_cm3*fl_mm/1000); PASS iff |PCSA_table-PCSA_pred|/PCSA_pred <= 0.02"
LICENSE_NOTE = ("(c) 2020 Anatomical Society; no explicit reuse grant found on PMC/XML/DOI pages "
                "-- recorded tension per the intake receipt, never waived silently")
MANIFEST_NOTE = ("3-field source (mass_g/fl_mm/pcsa_mm2): volume_cm3/mtu_mm/tendon_ext_mm/"
                 "tendon_int_mm do not exist in the tables -- intake F-MANIFEST named branch; "
                 "density/mtu/mass-additivity laws named not-runnable")
UNKNOWN_FIELDS = ["values_from_double_entry_agent_vision_of_cmyk_paper_scan_not_born_digital_bytes"]
ADMIT_UNKNOWN_FIELDS = UNKNOWN_FIELDS + ["lane_local_drafts_graph_admission_is_downstream"]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_inputs():
    registration, rho = L.load_constants()
    rec, grid_sha = L.load_reconciliation_with_pins()
    laws_sha = sha256_file(LAWS_REGISTERED_PATH)  # recorded as provenance below
    laws = json.load(open(LAWS_REGISTERED_PATH))
    rows = L.compute_rows(rec, rho)
    if rows != laws["law_rows"]:
        raise SystemExit("REFUSAL: recomputed verdicts != committed laws_registered.json")
    if laws["registered_constant"]["rho_g_cm3"] != rho or laws["registered_constant"]["route"] != registration["route"]:
        raise SystemExit("REFUSAL: laws_registered.json constant/route != constants.json")
    verdict = {(r["muscle"], r["specimen"]): r for r in rows}
    return registration, rho, rec, grid_sha, laws, laws_sha, verdict


def cell_provenance():
    """(m, s, f) -> {'passA': [cellrec...], 'passB': [...], 'group': str} rebuilt from
    the 24 frozen transcription tile files (mechanical reads for PROVENANCE, never
    for values)."""
    crops = json.load(open(CROPS_PATH))
    tile_sha = {t["tile"].rsplit(".", 1)[0]: t["sha256"] for t in crops["tiles"]}
    prov = {}
    for passdir in ("passA", "passB"):
        for p in sorted(glob.glob(os.path.join(TLANE, passdir, "*.json"))):
            d = json.load(open(p))
            tile = d["tile"]
            crop_sha = d["crop_sha256"]
            if tile_sha.get(tile) != crop_sha:
                raise SystemExit("REFUSAL: tile %s crop sha drift vs crops_manifest.json" % tile)
            for c in d["cells"]:
                if passdir == "passA":
                    m, g, s, f, v, leg, marker, merge = (c["m"], c["g"], c["s"], c["f"],
                                                         c["v"], c["leg"], c.get("marker"), c.get("merge"))
                else:
                    m, g, s, f, v, leg, marker, span, role = c
                e = prov.setdefault((m, s, f), {"group": g, "passA": [], "passB": []})
                if e["group"] != g:
                    raise SystemExit("REFUSAL: muscle group drift for %s" % m)
                e[passdir].append({"tile": tile, "crop_sha256": crop_sha,
                                   "v": v, "leg": leg})
    return prov


def provenance_block(key, value, cell, prov_entry, verdict_row, laws_sha, rho_g_cm3):
    tiles = sorted(
        ({"pass": pid, "tile": r["tile"], "crop_sha256": r["crop_sha256"]}
         for pid in ("passA", "passB") for r in prov_entry[pid]),
        key=lambda t: (t["pass"], t["tile"]))
    return {
        "sheet": SHEET,
        "tiff_sha256": SOURCE_TIFF_SHA256,
        "panel": tiles[0]["tile"].split("_")[0] if tiles else None,
        "tiles": tiles,
        "muscle": key[0], "muscle_group": prov_entry["group"], "specimen": key[1],
        "field": key[2],
        "printed_value": value,
        "unit_source": UNIT_SOURCE[key[2]],
        "pass_values": {"passA": sorted({r["v"] for r in prov_entry["passA"]}),
                        "passB": sorted({r["v"] for r in prov_entry["passB"]})},
        "legibility": {"passA": cell.get("passA_leg"), "passB": cell.get("passB_leg"),
                       "reconciled": cell.get("legibility")},
        "double_entry_exact_agreement": 1.0,
        "row_closure_law": {
            "law": "pcsa_closure", "form": LAW_FORM,
            "rho_g_cm3": rho_g_cm3,
            "constant_route": "stated_cited: Vanhoof et al. 2021 Methods 2.3 -- 'the density "
                              "value of 0.0011 g/mm3 is used in the calculation of the PCSA for "
                              "all muscles in this study'",
            "rel_dev": verdict_row["rel_dev"] if verdict_row else None,
            "verdict": verdict_row["law"] if verdict_row else None,
            "artifact": "laws_registered.json (sha256 %s)" % laws_sha,
        },
        "manifest": MANIFEST_NOTE,
        "license": LICENSE_NOTE,
        "law_lane": "vanhoof_law_20260920",
    }


def build():
    registration, rho, rec, grid_sha, laws, laws_sha, verdict = load_inputs()
    prov = cell_provenance()

    records, rejections = [], []
    counts = defaultdict(int)
    seen_ids = set()

    cells = sorted(rec["cells"], key=lambda c: (c["specimen"], c["muscle"], c["field"]))
    for cell in cells:
        key = (cell["muscle"], cell["specimen"], cell["field"])
        location = "vanhoof:s002:%s:%s:%s" % key
        counts["fetched"] += 1
        v = cell.get("verdict")
        if v == "TENTATIVE":
            value = cell["value"]
            pe = prov[key]
            for pid in ("passA", "passB"):
                for r in pe[pid]:
                    if r["v"] is None or Decimal(r["v"]) != Decimal(value):
                        raise SystemExit("REFUSAL: pass value drift at %s (%r vs %r) -- F3 pin would break"
                                         % (location, r["v"], value))
            row = verdict[(key[0], key[1])]
            block = provenance_block(key, value, cell, pe, row, laws_sha, rho)
            if row["law"] == "PASS":
                unit, quantity = FIELD_SPECS[key[2]]
                payload = convert(number(value), unit, quantity)
                payload.update(
                    subject="Macaca mulatta/%s (%s)" % (key[0], key[1]),
                    conditions=block,
                    source_field=key[2],
                    parameter=PARAMETER[key[2]])
                ext_id = location
                if ext_id in seen_ids:
                    raise SystemExit("REFUSAL: duplicate external_id %s" % ext_id)
                seen_ids.add(ext_id)
                rcd = draft(ext_id, "measurement", payload,
                            unknowns=ADMIT_UNKNOWN_FIELDS,
                            label="%s %s %s" % key)
                rcd["class_contract"] = {"class_id": "batch.property.measurement", "version": 1}
                records.append(rcd)
                counts["admitted_cells"] += 1
            else:
                rejections.append({
                    "location": location,
                    "refusal": {"code": "row_closure_violation",
                                "detail": ("row PCSA closure at the registered rho=1.1 g/cm3 "
                                           "(%s): rel_dev %.4f > 0.02, class %s, implied rho %.4f "
                                           "g/cm3 -- per-row source inconsistency, named not repaired"
                                           % (registration["route"], row["rel_dev"],
                                              row["deviation_class"], row["implied_rho_g_cm3"]))},
                    "provenance": block, "weight": 1})
                counts["row_closure_violation"] += 1
                counts["row_closure_violation:" + row["deviation_class"]] += 1
        elif v == "MARKER_AGREED":
            code = cell["marker"]
            if code not in REFUSAL_TAXONOMY_CLOSED:
                raise SystemExit("REFUSAL: marker class %s outside the closed taxonomy" % code)
            rejections.append({"location": location,
                               "refusal": {"code": code,
                                           "detail": "source text marker (double-entry agreed class); never a number"},
                               "weight": 1})
            counts["marker_refused_cells"] += 1
        elif v == "BLANK_AGREED":
            rejections.append({"location": location,
                               "refusal": {"code": "merged_cell_covered",
                                           "detail": "position covered by a merged multi-muscle cell in the source (both passes blank)"},
                               "weight": 1})
            counts["merged_covered_positions"] += 1
        elif v == "DISPUTED":
            raise SystemExit("REFUSAL: DISPUTED cell present but landed agreement is 1.0 -- pins broken")
        else:
            raise SystemExit("REFUSAL: unexpected verdict %r at %s" % (v, location))

    fetched = counts["fetched"]
    admitted = len(records)
    rejected_weight = sum(r.get("weight", 1) for r in rejections)
    closed = (fetched == admitted + rejected_weight and fetched == 774
              and admitted == 438 and rejected_weight == 336)
    tier_summary = {
        "law_pass_rows": laws["n_pass"], "law_fail_rows": laws["n_checkable_rows"] - laws["n_pass"],
        "admitted_cells": admitted,
        "refused_row_closure_violation_cells": counts["row_closure_violation"],
        "refused_by_class": {k.split(":", 1)[1]: counts[k] for k in counts
                             if k.startswith("row_closure_violation:")},
        "marker_refused_cells": counts["marker_refused_cells"],
        "merged_covered_positions": counts["merged_covered_positions"],
        "fetched_total": fetched,
    }
    manifest = {
        "schema": "chimera.rule0.manifest_registration.v1",
        "connector_id": "vanhoof_s2_transcription",
        "adapter": "tools/science_funnel/validation/vanhoof_law_20260920/admit_law.py (lane-local driver "
                   "emitting the prestage admit_vanhoof.py contract shapes; admit_vanhoof.admit NOT "
                   "modified and NOT forced -- its 7-field require cannot close on the measured "
                   "3-field manifest, the intake's F-MANIFEST named branch)",
        "source": {"id": "vanhoof_2021_part2_table_s2",
                   "doi": "10.1111/joa.13314", "pmcid": "PMC7812139",
                   "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC7812139/",
                   "identity": "Table S2, 7 adult Macaca mulatta (Mm1-Mm7), two panels",
                   "license": LICENSE_NOTE},
        "artifacts": [{"id": "JOA-238-321-s002.tif", "sha256": SOURCE_TIFF_SHA256, "bytes": 6455574}],
        "canonical_fields_present": ["mass_g", "fl_mm", "pcsa_mm2"],
        "canonical_fields_absent_named": ["volume_cm3", "mtu_mm", "tendon_ext_mm", "tendon_int_mm"],
        "laws": {"runnable": [{"law": "pcsa_closure", "rho_g_cm3": rho,
                               "route": registration["route"], "tolerance": L.LAW_TOLERANCE_INHERITED}],
                 "not_runnable": ["density_law (no volume column)", "mtu_additivity (no MTU/tendon columns)",
                                  "mass_additivity_dev (no belly/tendon mass columns)"]},
        "record_class": "batch.property.measurement v1 (draft shape; graph ids data.assertion.* are "
                        "minted downstream -- graph apply is not run from this lane)",
        "idempotent_replay": "content-derived external ids vanhoof:s002:{muscle}:{spec}:{field}; "
                             "3-run byte-identical outputs (F4)",
    }
    out = {
        "schema": "chimera.rule0.admission.v1",
        "lane": "vanhoof_law_20260920",
        "inputs": {"reconciliation.json_sha256_verified": True, "tentative_grid_sha256": grid_sha,
                   "constants_route": registration["route"], "rho_g_cm3": rho,
                   "laws_registered.json_sha256": laws_sha},
        "manifest": manifest,
        "tier_summary": tier_summary,
        "record_set_digest": digest({"records": records, "rejections": rejections}),
        "records": records,
        "rejections": rejections,
        "count_identity": {
            "law": "fetched == admitted + rejected(weighted), zero silent drops",
            "fetched": fetched, "admitted": admitted,
            "rejected_records": len(rejections), "rejected_weight": rejected_weight,
            "grid": "774 = 654 TENTATIVE + 105 MARKER_AGREED + 15 BLANK_AGREED (landed, re-verified)",
            "closed": closed,
        },
    }
    if not closed:
        raise SystemExit("REFUSAL: count identity does not close -- fix the lane, not the arithmetic")
    with open(os.path.join(BASE, "admission.json"), "w", newline="\n") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    with open(os.path.join(BASE, "records_vanhoof_s2.json"), "w", newline="\n") as f:
        json.dump({"schema": "chimera.rule0.admission.v1", "lane": "vanhoof_law_20260920",
                   "record_set_digest": out["record_set_digest"], "records": records},
                  f, indent=1, sort_keys=True)
    print(json.dumps({"count_identity": out["count_identity"], "tier_summary": tier_summary,
                      "record_set_digest": out["record_set_digest"]}, indent=1, sort_keys=True))


if __name__ == "__main__":
    build()
