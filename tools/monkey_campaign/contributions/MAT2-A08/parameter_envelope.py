#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MAT2-A08 - Define evidenced muscle/tendon parameter envelope.

Records/offline card: one generator emits parameter_envelope.json
(schema chimera.a08_parameter_envelope.v1) from PINNED inputs and validates
it by recomputation.  Lawful close = source-backed parameters OR explicit
unresolved entries with named missing evidence; declared carrier values keep
their honest provenance class.  Sealed laws enforced by code:

- A07 law: no density/stiffness/activation law inferred from geometry alone
  (FB1); any new fitting experiment is separately authorized -- none is, so
  fitted*/optimized* keys refuse (FB4 + whole-document scan).
- Card observation: no unrelated human or differently scaled (fascicularis)
  masses/strengths are inherited (FB2; M2-5/M2-7 are neither pinned nor read).
- done_when separation: source-backed biological parameters and chosen
  engineering active-pressure material parameters live in two DISJOINT
  registries (FB3).
- Atlas screen law: screens never flip sealed statuses; recomputed classes
  must AGREE with the sealed atlas receipt or refuse (FB6).
- No silent defaults: an explicitly_unresolved entry stays unresolved until a
  pinned source exists (FB7).

Every falsifier arm runs its clean control FIRST and carries a named
premature guard (house G1/P1).  Determinism: two consecutive --emit runs are
byte-identical (P9).  No wall-clock value enters any emitted artifact.

task_id is SHORT form ('A08') in every generated artifact (P7).
"""

import copy
import csv
import hashlib
import io
import json
import math
import sqlite3
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SCHEMA = "chimera.a08_parameter_envelope.v1"
FALSIFIER_SCHEMA = "chimera.a08_falsifiers.v1"
RECEIPT_SCHEMA = "chimera.qualification_receipt.v1"
PROFILE_SNAPSHOT_SCHEMA = "chimera.registry_profile_snapshot.v1"
PROFILE_PROVENANCE_SCHEMA = "chimera.registry_profile_provenance.v1"

TASK_ID_SHORT = "A08"
TASK_ID_LONG = "MAT2-A08"
CRITERIA_SHA256 = "f784d613aaebc3c2c24350a6cd4a5fb103f72f929f83b5fd9926395b55a040e8"
SCOPE_SHA256 = "cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097"
DEFINITION_RAW_SHA256 = "57ded6eb2f2cc6aa914d6f68c8efb55b215790fc7a9d0baa5dfd2c49fd1465c1"
ATTEMPT_ID = "91219426ace44ca8829000815780caaf"
ARRIVAL_ID = "arrival-f9d11eb9da3f44a3842d11e8736d73e9"
DATE_FROZEN = "2026-09-30"
BASE_HEAD = "362da5056f84b56b62a13cfb878dddb98538b18f"

DONE_WHEN_VERBATIM = (
    "Strength, force-length/velocity, compliance, limits and applicability are defined for the "
    "selected animal. Material-first addition: Separate source-backed biological parameters from "
    "chosen engineering active-pressure material parameters. No inferred density/stiffness/"
    "activation law from geometry alone."
)
CARD_OBSERVATION_VERBATIM = (
    "Do not inherit unrelated human or differently scaled masses/strengths"
)
CARD_FALSIFIER_VERBATIM = (
    "Missing identities or a claimed pass unsupported by records fails; a screenshot is not a "
    "substitute."
)

CARD_DIR = Path(__file__).resolve().parent
REPO_ROOT = CARD_DIR.parents[3]
OSIM_REL = "tools/monkey_campaign/contributions/MAT2-M02/data/macaque_arm/monkeyArm_current.osim"
A06_REL = "tools/monkey_campaign/contributions/MAT2-A06/attachment_ownership.json"

CHENG_DIR = Path("E:/ChimeraWork/research-data/20260929/cheng_tables")
ATLAS_DIR = Path("E:/ChimeraWork/research-data/20260929/atlas")
M3_CARRIER = Path("E:/ChimeraWork/monkey-coordination/kanban-attempts/MAT2-M03/"
                  "61aa525f80da4b61a10b7e3c788d87fc/checkout/tools/monkey_campaign/"
                  "contributions/MAT2-M03/pressure_state.json")
M4_CARRIER = Path("E:/ChimeraWork/monkey-coordination/kanban-attempts/MAT2-M04/"
                  "262e9d2a30ae4c4b82d84de7de9661a1/checkout/tools/monkey_campaign/"
                  "contributions/MAT2-M04/arm_rigid_laws.json")
REGISTRY_DB = Path("E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3")

INPUT_PINS = {
    "repo:" + OSIM_REL: "4148aee2c8dda1dcb0918496ad7c5e1adcf4ebabde0a68a3e0dc67faec67b895",
    "repo:" + A06_REL: "f1f0430772258e8449fc354841becf2f1869783399e63f3f145565b8d0b1041c",
    "host:M2-3_mulatta_morphometry.csv":
        "16ca8bcd9be48b3766125801eb05a8f4f10b446b4caed76d9fddeb2e45df71fa",
    "host:M2-6_mulatta_inertials.csv":
        "1948a2d8399b5253461c6ed70eed87ea38c5df4083b75437e1e3dbd1a4ce93f3",
    "host:M2-8_regressions.csv":
        "b185ee8e98b6e663defed0abd4d004fec053eb6417e027c54801070cd894ec22",
    "host:atlas_receipt.json":
        "51a591eb938e032ce32c2a09f8b089d9bdd3138d1fc367081c2093b2d52a7586",
    "host:MUSCLE_ATLAS.md":
        "e51c8bb211ec15ea9fbe84cfb6c8f5dae421d276b48f39b4703936d6c88d1a16",
    "host:REPIN_STUDY.md":
        "99cde4758566784b5b98ad45db19f50beba2c81d8b1761428af19e32290c318b",
    "host:20260921_arm_architecture_options.md":
        "60e97cc8f7bf37c69d5230da7a1c030f91e5636ff7f958855fea592f2fd74e25",
    "host:pressure_state.json":
        "8182da4720f26154dfff3c54711e66cb318cc7bb9c989de77b7ee0a2f2b2ec03",
    "host:arm_rigid_laws.json":
        "a9e971db4b36c1a6c35f9c27171ebd06787d5ffc96d58cd4b039e9e4e7f02d32",
    "host:ASTRA_DATA_ROUND_20260929.md":
        "e082aa812af21031a1c3a6e41111fe078b86d04f0dfff1a40d6061ad87064986",
}

T_DF5_975 = 2.570582          # Student t, two-sided 95%, df=5 (sealed atlas constant)
T_PI_MULTIPLIER = T_DF5_975 * math.sqrt(1.0 + 1.0 / 6.0)  # 2.776546 class

OFL_PLACEHOLDER_M = 0.122492  # the sealed model's own repeated ceiling constant
OFL_PLACEHOLDER_ALT_M = 0.1225
TSL_PLACEHOLDER_M = 0.002
FMAX_FLOOR_N = 30.0

EXPECTED_COUNTS = {  # preregistered P2/P4 predictions (sealed atlas/memo/repin counts)
    "osim_muscles_total": 39,
    "fmax_floor_default": 11,
    "ofl_placeholder_all": 14,
    "tsl_placeholder_all": 14,
    "matched_1to1": 19,
    "granular_not_comparable": 5,
    "muscle_absent": 15,
    "fiber_INSIDE-1SD": 2,
    "fiber_INSIDE-2SD": 1,
    "fiber_OUTSIDE": 16,
    "tendon_INSIDE-1SD": 5,
    "tendon_INSIDE-2SD": 5,
    "tendon_OUTSIDE": 9,
    "pennation_INSIDE-1SD": 11,
    "pennation_CONSISTENT-CENSORED(<5deg)": 7,
    "pennation_OUTSIDE-CENSORED(claim>=5deg)": 1,
    "t_pi_fiber_inside": 3,
    "t_pi_tendon_inside": 12,
    "segment_INSIDE-1SD": 3,
}

FORBIDDEN_SOURCE_TOKENS = ("human", "fascicularis", "cynomolgus")  # card observation law
GEOMETRY_INFERENCE_TARGETS = ("density", "stiffness", "activation")
FITTED_KEY_PREFIXES = ("fitted", "optimized", "optimizer")
CANONICAL_LAYERS = set()  # P7 tripwire ONLY: records/offline profile declares NO layers

PEN_KEYS = ("INSIDE-1SD", "CONSISTENT-CENSORED(<5deg)",
            "OUTSIDE-CENSORED(claim>=5deg)")


def require(cond, code, detail=None):
    if not cond:
        raise ValueError("%s:%s" % (code, detail if detail is not None else ""))


def refuse_vacuous_comparison(a, b, code):
    """House P5/G5: a relative comparison that is identically zero on both
    sides is vacuous and dies loudly before any tolerance is evaluated."""
    if a == 0 and b == 0:
        raise ValueError("vacuous_comparison_refused:" + code)


def vacuous_guard_selftest():
    try:
        refuse_vacuous_comparison(0.0, 0.0, "a08_selftest")
    except ValueError as exc:
        require("vacuous_comparison_refused:a08_selftest" in str(exc),
                "a08_vacuous_guard_wrong_refusal", str(exc))
        return {"fires_on_identically_zero_window": True,
                "refusal_code": "vacuous_comparison_refused:a08_selftest",
                "lesson": "a gate that cannot fail is not a measurement (M07 A8)"}
    raise ValueError("vacuous_guard_selftest_did_not_fire")


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def read_pinned(path, pin, label):
    b = Path(path).read_bytes()
    require(sha256_bytes(b) == pin, "input_pin_drift", label)
    return b


def git(*args):
    out = subprocess.run(["git"] + list(args), cwd=str(CARD_DIR),
                         capture_output=True)
    return out.stdout.decode().strip()


def git_head():
    h = git("rev-parse", "HEAD")
    require(len(h) == 40, "a08_git_head", h)
    return h


def prereg_commits():
    """All commits touching PREREGISTRATION.md, newest first (freeze + amendments)."""
    h = git("rev-list", "HEAD", "--", "PREREGISTRATION.md")
    lines = [x for x in h.splitlines() if len(x) == 40]
    require(len(lines) >= 1, "a08_prereg_commit_unresolved", h[:80])
    return lines


# ---------------------------------------------------------------- osim parser

MUSCLE_TAG = "Schutte1993Muscle_Deprecated"
MUSCLE_FIELDS = ("max_isometric_force", "optimal_fiber_length",
                 "tendon_slack_length", "pennation_angle_at_optimal")


def parse_osim(b):
    root = ET.fromstring(b)
    muscles = []
    for el in root.iter(MUSCLE_TAG):
        row = {"name": el.get("name")}
        child_tags = [c.tag for c in el]
        for f in MUSCLE_FIELDS:
            vals = [c.text for c in el if c.tag == f]
            require(len(vals) == 1, "osim_field_count", (el.get("name"), f))
            row[f] = float(vals[0])
        bad = [t for t in child_tags
               if ("mass" in t.lower() or "pcsa" in t.lower())]
        require(not bad, "osim_muscle_mass_field_present", (el.get("name"), bad))
        row["_tags"] = child_tags
        muscles.append(row)
    n_joints = sum(1 for el in root.iter()
                   if el.tag.endswith("Joint") and el.get("name"))
    return muscles, {"joint_definitions": n_joints}


# ---------------------------------------------------------------- CSV parsers

def parse_pm_cell(cell):
    """'5.4±0.6' -> (5.4, 0.6); '-' -> None (censored cell)."""
    cell = cell.strip()
    if cell in ("-", ""):
        return None
    parts = cell.split("±")
    require(len(parts) == 2, "m23_cell_shape", cell)
    return float(parts[0]), float(parts[1])


def parse_m23(b):
    rows = {}
    rdr = csv.DictReader(io.StringIO(b.decode("utf-8-sig")))
    for r in rdr:
        rows[r["Muscle"].strip()] = {
            "L0M": parse_pm_cell(r["L₀ᴹ(cm)"]),
            "mass": parse_pm_cell(r["Mass(g)"]),
            "pcsa": parse_pm_cell(r["PCSA(cm²)"]),
            "L0T": parse_pm_cell(r["L₀ᵀ(cm)"]),
            "alpha": parse_pm_cell(r["α(°)"]),
        }
    return rows


def parse_m26(b):
    out = {}
    rdr = csv.DictReader(io.StringIO(b.decode("utf-8-sig")))
    for r in rdr:
        out[r["Parameter"].strip()] = r
    seg = {}
    for col, key in (("Upper arm", "upper_arm"), ("Forearm", "forearm"),
                     ("Hand", "hand")):
        pm = parse_pm_cell(out["Segment mass (g)"][col])
        require(pm is not None, "m26_cell_shape", col)
        seg[key] = {"mean_g": pm[0], "sd_g": pm[1]}
    return seg


# ---------------------------------------------------------------- screens

def band_class(claim, mean, sd):
    """Sealed atlas band discipline, boundaries inclusive."""
    refuse_vacuous_comparison(claim, mean, "a08_band_comparison")
    require(sd > 0.0, "a08_vacuous_band_refused", (claim, mean, sd))
    z = abs(claim - mean) / sd
    if z <= 1.0:
        return "INSIDE-1SD", z
    if z <= 2.0:
        return "INSIDE-2SD", z
    return "OUTSIDE", z


def t_pi(mean, sd):
    half = T_PI_MULTIPLIER * sd
    return {"pi_low": mean - half, "pi_high": mean + half, "pi_half": half}


def screen_quantity(claim, band):
    if band is None:
        return {"class": "NO-MEASURED-ROW"}
    mean, sd = band
    cls, z = band_class(claim, mean, sd)
    pi = t_pi(mean, sd)
    return {"class": cls, "z": round(z, 4),
            "mean": mean, "sd": sd,
            "inside_t_pi": bool(pi["pi_low"] <= claim <= pi["pi_high"]),
            "pi_low": round(pi["pi_low"], 4), "pi_high": round(pi["pi_high"], 4),
            "pi_half": round(pi["pi_half"], 4)}


# ------------------------------------------------------------- biological rows

def build_biological_registry(osim_muscles, m23, atlas):
    mapping = {r["osim_muscle"]: r for r in atlas["muscle_rows"]}
    granular = {r["osim_muscle"]: r for r in atlas["granular_rows"]}
    absent = {r["osim_muscle"]: r for r in atlas["absent_muscles"]}
    rows = []
    for m in osim_muscles:
        name = m["name"]
        fmax = m["max_isometric_force"]
        ofl = m["optimal_fiber_length"]
        tsl = m["tendon_slack_length"]
        pen_rad = m["pennation_angle_at_optimal"]
        pen_deg = pen_rad * 180.0 / math.pi
        fingerprints = {
            "fmax_floor_default": bool(fmax == FMAX_FLOOR_N),
            "ofl_placeholder": bool(abs(ofl - OFL_PLACEHOLDER_M) < 1e-9
                                    or abs(ofl - OFL_PLACEHOLDER_ALT_M) < 1e-9),
            "tsl_placeholder": bool(abs(tsl - TSL_PLACEHOLDER_M) < 1e-9),
        }
        prov = {
            "row_class": ("default-excluded" if fingerprints["fmax_floor_default"]
                          else "recomputed-fingerprint-only"),
            "note": ("per-row derived-provisional vs provenance-unknown membership "
                     "is the sealed memo adjudication (20260921 memo 22/6/11 "
                     "verdict, pinned), not recomputed by this card; carrier force "
                     "claims stay force_runtime_ready: false"),
        }
        row = {
            "osim_muscle": name,
            "fmax_n": fmax, "l0m_m": ofl, "l0t_m": tsl,
            "pennation_rad": pen_rad, "pennation_deg": round(pen_deg, 4),
            "fingerprints": fingerprints,
            "provenance": prov,
            "source_class": "declared_carrier_not_source_backed",
        }
        if name in mapping:
            a = mapping[name]
            require(a["m23_row"] in m23, "mapping_row_missing", (name, a["m23_row"]))
            band = m23[a["m23_row"]]
            row["mapping"] = {"m23_row": a["m23_row"], "kind": a["mapping"],
                              "note": a.get("mapping_note", "")}
            fl = screen_quantity(ofl * 100.0, band["L0M"])
            tl = screen_quantity(tsl * 100.0, band["L0T"])
            if band["alpha"] is None:
                pen = ({"class": "CONSISTENT-CENSORED(<5deg)"}
                       if pen_deg < 5.0
                       else {"class": "OUTSIDE-CENSORED(claim>=5deg)"})
            else:
                pen = screen_quantity(pen_deg, band["alpha"])
            row["screens"] = {"fiber_length": fl, "tendon_length": tl,
                              "pennation": pen}
            row["not_comparable"] = {
                "mass": "no sealed claim exists (the osim carries no per-muscle "
                        "mass property)",
                "pcsa": "no sealed claim exists and no measured specific tension; "
                        "PCSA=Fmax/sigma is not round-trip-stable (sealed memo "
                        "sigma law)",
            }
        elif name in granular:
            row["mapping"] = {"m23_row": granular[name]["m23_row"],
                              "kind": "granularity-NOT-COMPARABLE",
                              "note": granular[name]["why"]}
            row["screens"] = None
        elif name in absent:
            row["mapping"] = {"m23_row": None, "kind": "MUSCLE-ABSENT",
                              "note": absent[name]["why"]}
            row["screens"] = None
        else:
            raise ValueError("a08_atlas_mapping_incomplete:" + name)
        rows.append(row)
    return rows


# --------------------------------------------------------------- engineering

def build_engineering_registry():
    rows = []
    m3 = json.loads(read_pinned(M3_CARRIER, INPUT_PINS["host:pressure_state.json"],
                                "pressure_state.json"))
    law = m3["laws"][0]["parameters"]
    eng3 = [
        ("m03_damping_per_s", law["damping_per_s"], "1/s"),
        ("m03_dt_s", law["dt_s"], "s"),
        ("m03_edge_compliance", law["edge_compliance_m_per_n"], "m/N"),
        ("m03_max_delta_p", law["max_delta_p_pa"], "Pa"),
        ("m03_max_dv_dt", law["max_dv_dt_m3_per_s"], "m^3/s"),
        ("m03_p_int_peak", law["p_int_peak_pa"], "Pa"),
        ("m03_xpbd_iterations", law["xpbd_iterations"], "count"),
        ("m03_membrane_mass", m3["matter"][0]["mass_kg"], "kg"),
    ]
    for rid, val, unit in eng3:
        rows.append({
            "id": rid, "registry": "engineering_active_pressure",
            "quantity": rid.split("_", 1)[1], "value": val, "unit": unit,
            "provenance": "chosen_engineering",
            "source_status": "synthetic_authored",
            "never_biological": True,
            "carrier": "host:pressure_state.json",
            "carrier_sha256": INPUT_PINS["host:pressure_state.json"],
            "note": "authored demonstrator active-pressure material constant "
                    "(M03 sealed carrier); a modelling choice, never a biological "
                    "measurement of the selected animal",
        })
    m4 = json.loads(read_pinned(M4_CARRIER, INPUT_PINS["host:arm_rigid_laws.json"],
                                "arm_rigid_laws.json"))
    prof = m4["profiles"][0]
    require(prof["id"] == "rigid" and prof["parameters"] == {},
            "m04_profile_shape", prof["id"])
    require(prof["source_status"] == "synthetic_authored", "m04_source_status",
            prof.get("source_status"))
    for a in m4["assignments"]:
        require(a["profile_id"] == "rigid", "m04_assignment_profile", a["region_id"])
        rows.append({
            "id": "m04_rigid_" + a["region_id"],
            "registry": "engineering_active_pressure",
            "quantity": "passive_law_profile", "value": "rigid", "unit": "profile",
            "provenance": "chosen_engineering",
            "source_status": "synthetic_authored",
            "never_biological": True,
            "carrier": "host:arm_rigid_laws.json",
            "carrier_sha256": INPUT_PINS["host:arm_rigid_laws.json"],
            "note": "rigid-by-declaration arm region (M04 sealed carrier); the "
                    "arm's only pinned stiffness state is an engineering choice, "
                    "not tissue biology; 'density is never an input to stiffness' "
                    "(M04 provenance note)",
        })
    return rows, {"m03_schema": m3["schema"], "m04_schema": m4["schema"],
                  "m04_assignments": len(m4["assignments"])}


# ----------------------------------------------------------- unresolved table

def build_unresolved_entries():
    return [
        {"id": "U1", "parameter_class": "strength_measured_upgrade",
         "status": "explicitly_unresolved",
         "missing_evidence": "measured maximum isometric force (or measured PCSA "
             "plus measured specific tension) for the selected animal; the sealed "
             "carrier Fmax values are 22 derived-provisional / 6 provenance-"
             "unknown / 11 hand-set defaults (20260921 memo verdict), not "
             "source-backed",
         "authorizing_rank": "requires a separately authorized measured source; "
             "carrier claims stay force_runtime_ready: false"},
        {"id": "U2", "parameter_class": "muscle_mass_and_pcsa",
         "status": "explicitly_unresolved",
         "missing_evidence": "CT-derived muscle volumes; the CT distribution is "
             "recorded BLOCKED FOR SHIP (RESTRICTED_RECORDED CT-chain behind "
             "operator gate 066485ae); release requires separate authorization",
         "authorizing_rank": "operator gate 066485ae owner (Captain/operator "
             "decision); inference from surface geometry is not lawful"},
        {"id": "U3", "parameter_class": "specific_tension_sigma",
         "status": "explicitly_unresolved",
         "missing_evidence": "measured specific tension for M. mulatta; the sigma "
             "round trip is open (an unknown sigma may sit inside the carrier "
             "Fmax derivation), so PCSA=Fmax/sigma is not round-trip-stable",
         "authorizing_rank": "requires a measured source named by a Captain-"
             "authorized records lane"},
        {"id": "U4", "parameter_class": "force_length_velocity_dynamics",
         "status": "explicitly_unresolved",
         "missing_evidence": "any measured force-velocity parameter source for "
             "the selected animal (the sealed model class fixes the relation "
             "SHAPE, but its measured parameters for this animal exist in no "
             "pinned source)",
         "authorizing_rank": "requires a measured source; model-class shape is "
             "not a measurement"},
        {"id": "U5", "parameter_class": "activation_dynamics",
         "status": "explicitly_unresolved",
         "missing_evidence": "measured activation data; no activation law may be "
             "inferred from geometry alone (sealed A07 law)",
         "authorizing_rank": "requires measured activation data under separate "
             "authorization"},
        {"id": "U6", "parameter_class": "tendon_compliance_stiffness",
         "status": "explicitly_unresolved",
         "missing_evidence": "measured tendon elastic modulus or compliance for "
             "the selected animal; tendon_slack_length is a geometric length, "
             "not a stiffness; M04 rigid is an engineering declaration",
         "authorizing_rank": "requires a measured source; C17-class real-port "
             "inputs remain blocked (A06/A07 lawful absence)"},
        {"id": "U7", "parameter_class": "passive_force_length",
         "status": "explicitly_unresolved",
         "missing_evidence": "measured passive force-length parameters for the "
             "selected animal",
         "authorizing_rank": "requires a measured source"},
        {"id": "U8", "parameter_class": "biological_rom_joint_limits",
         "status": "explicitly_unresolved",
         "missing_evidence": "measured forelimb joint range-of-motion for this "
             "specimen class; the sealed walk-scene envelope and torque caps are "
             "authored engineering (DOC-derived x1.25), not animal ROM biology",
         "authorizing_rank": "requires a measured source; no human-norm torque "
             "substitution is lawful (C07 output law)"},
    ]


# ------------------------------------------------------------------- C07/C18

def build_calculation_contracts(a06, joint_info):
    path_records = a06.get("path_records", [])
    attachments = a06.get("attachments", [])
    require(len(path_records) == 48 and len(attachments) == 26,
            "a06_registry_counts", (len(path_records), len(attachments)))
    return [
        {"id": "C07", "title": "Actuator limits and passive response",
         "status": "OPEN INVENTORY (no new numerical result claimed)",
         "required_inputs_catalog": "Selected animal parameters, ROM, "
             "force-length/velocity, compliance, damping",
         "input_status": {
             "strength": "declared carrier (provenance-flagged); measured "
                         "upgrade explicitly unresolved (U1)",
             "rom": "explicitly unresolved (U8); no human-norm torque "
                    "substitution",
             "force_length_velocity": "explicitly unresolved (U4)",
             "compliance": "explicitly unresolved (U6)",
             "damping": "engineering only (M03 damping_per_s is the "
                        "demonstrator source, never biology)"},
         "output_law": "Physical action limits; no human-norm torque substituted "
                       "for this animal",
         "verification_still_required": "independent parameter provenance and "
             "saturated/obstructed-motion controls",
         "consumable_parameters": "biological_registry rows carry "
             "declared_carrier_not_source_backed; force claims stay "
             "force_runtime_ready: false until U1/U3 resolve"},
        {"id": "C18", "title": "Tendon routing and moment arms",
         "status": "OPEN INVENTORY (no new numerical result claimed)",
         "required_inputs_catalog": "Owned endpoints/waypoints, joint positions, "
             "wrapping model if supported",
         "input_status": {
             "endpoints_waypoints": "OWNED by sealed A06 registry (%d path "
                 "records, %d attachments, %d bonds, %d containment edges, %d "
                 "grasp endpoints; pinned sha)" % (
                     len(path_records), len(attachments),
                     len(a06.get("bonds", [])),
                     len(a06.get("containment_edges", [])),
                     len(a06.get("grasp_endpoints", []))),
             "joint_positions": "present in the sealed osim carrier (%d named "
                                "joint definitions; engineering carrier)"
                                % joint_info["joint_definitions"],
             "wrapping_model": "not supported by the sealed model class; none "
                               "invented"},
         "output_law": "Finite, physically attributed tendon forces and joint "
                       "torques; l(q) and signed moment arms under a declared "
                       "convention",
         "verification_still_required": "finite differences/virtual work and "
             "unresolved-owner rejection",
         "consumable_parameters": "routing geometry only; no invented stiffness, "
             "no geometry-inferred density/stiffness/activation"},
    ]


# ------------------------------------------------------------------- scans

def scan_fitted_keys(obj, path=""):
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            kl = str(k).lower()
            if any(kl.startswith(p) for p in FITTED_KEY_PREFIXES):
                hits.append(path + "/" + str(k))
            hits.extend(scan_fitted_keys(v, path + "/" + str(k)))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(scan_fitted_keys(v, path + "/" + str(i)))
    return hits


def scan_geometry_inference_rows(bio_rows):
    """No biological row may derive density/stiffness/activation from geometry
    alone: any row key or derivation blob carrying a target word plus a
    geometry word is a hit."""
    hits = []
    for row in bio_rows:
        blob = json.dumps(row, sort_keys=True).lower()
        for t in GEOMETRY_INFERENCE_TARGETS:
            for g in ("geometry", "mesh", "path_length"):
                probe = "%s_from_%s" % (t, g)
                if probe in blob or ("derived_from" in row
                                     and t in str(row.get("derived_from", "")).lower()
                                     and g in str(row.get("derived_from", "")).lower()):
                    hits.append(row.get("osim_muscle", "?") + ":" + probe)
        if "derivation" in row:
            d = json.dumps(row["derivation"], sort_keys=True).lower()
            if any(t in d for t in GEOMETRY_INFERENCE_TARGETS):
                hits.append(row.get("osim_muscle", "?") + ":derivation")
    return hits


def scan_forbidden_sources_rows(bio_rows):
    hits = []
    for row in bio_rows:
        blob = json.dumps(row, sort_keys=True).lower()
        for tok in FORBIDDEN_SOURCE_TOKENS:
            if tok in blob:
                hits.append((row.get("osim_muscle", "?"), tok))
    return hits


# ------------------------------------------------------------------- sources

def load_sources():
    osim_b = read_pinned(REPO_ROOT / OSIM_REL, INPUT_PINS["repo:" + OSIM_REL],
                         "osim")
    a06_b = read_pinned(REPO_ROOT / A06_REL, INPUT_PINS["repo:" + A06_REL],
                        "A06 registry")
    m23_b = read_pinned(CHENG_DIR / "M2-3_mulatta_morphometry.csv",
                        INPUT_PINS["host:M2-3_mulatta_morphometry.csv"], "M2-3")
    m26_b = read_pinned(CHENG_DIR / "M2-6_mulatta_inertials.csv",
                        INPUT_PINS["host:M2-6_mulatta_inertials.csv"], "M2-6")
    atlas_b = read_pinned(ATLAS_DIR / "atlas_receipt.json",
                          INPUT_PINS["host:atlas_receipt.json"], "atlas receipt")
    osim_muscles, joint_info = parse_osim(osim_b)
    return {
        "osim_muscles": osim_muscles, "joint_info": joint_info,
        "a06": json.loads(a06_b), "m23": parse_m23(m23_b), "m26": parse_m26(m26_b),
        "atlas": json.loads(atlas_b),
    }


def compute_bio_rows(src):
    return build_biological_registry(src["osim_muscles"], src["m23"], src["atlas"])


def compute_counts(bio_rows, src):
    counts = {
        "osim_muscles_total": len(bio_rows),
        "fmax_floor_default": sum(1 for r in bio_rows
                                  if r["fingerprints"]["fmax_floor_default"]),
        "ofl_placeholder_all": sum(1 for r in bio_rows
                                   if r["fingerprints"]["ofl_placeholder"]),
        "tsl_placeholder_all": sum(1 for r in bio_rows
                                   if r["fingerprints"]["tsl_placeholder"]),
    }
    matched = [r for r in bio_rows if r["mapping"]["kind"] == "1:1"]
    counts["matched_1to1"] = len(matched)
    counts["granular_not_comparable"] = sum(
        1 for r in bio_rows if r["mapping"]["kind"] == "granularity-NOT-COMPARABLE")
    counts["muscle_absent"] = sum(
        1 for r in bio_rows if r["mapping"]["kind"] == "MUSCLE-ABSENT")
    for q, pfx in (("fiber_length", "fiber"), ("tendon_length", "tendon")):
        for cls in ("INSIDE-1SD", "INSIDE-2SD", "OUTSIDE"):
            counts["%s_%s" % (pfx, cls)] = sum(
                1 for r in matched if r["screens"][q]["class"] == cls)
        counts["t_pi_%s_inside" % pfx] = sum(
            1 for r in matched if r["screens"][q].get("inside_t_pi"))
    for cls in PEN_KEYS:
        counts["pennation_%s" % cls] = sum(
            1 for r in matched if r["screens"]["pennation"]["class"] == cls)
    return counts


# -------------------------------------------------------------------- build

def build_document(src, profile):
    bio_rows = compute_bio_rows(src)
    eng_rows, eng_meta = build_engineering_registry()
    unresolved = build_unresolved_entries()
    contracts = build_calculation_contracts(src["a06"], src["joint_info"])
    counts = compute_counts(bio_rows, src)
    atlas = src["atlas"]

    fcus = [r for r in bio_rows if r["osim_muscle"] == "flex_carpi_ulnaris"]
    require(len(fcus) == 1, "a08_fcu_present", len(fcus))
    # Amendment A1 (sealed memo wording): the fiber-ceiling constant is carried
    # AS the tendon slack length while the muscle's own fiber length differs.
    slot_swap = bool(abs(fcus[0]["l0t_m"] - OFL_PLACEHOLDER_M) < 1e-9
                     and abs(fcus[0]["l0m_m"] - fcus[0]["l0t_m"]) > 1e-9)

    seg_rows = []
    for a in atlas["segment_screens"]:
        band = src["m26"][a["m26_column"]]
        claim_g = a["claim_kg"] * 1000.0
        cls, z = band_class(claim_g, band["mean_g"], band["sd_g"])
        pi = t_pi(band["mean_g"], band["sd_g"])
        seg_rows.append({
            "claim": a["claim"], "claim_kg": a["claim_kg"],
            "m26_column": a["m26_column"],
            "m26_mean_g": band["mean_g"], "m26_sd_g": band["sd_g"],
            "class": cls, "z": round(z, 4),
            "inside_t_pi": bool(pi["pi_low"] <= claim_g <= pi["pi_high"]),
            "sealed_atlas_class": a["class"],
        })
    seg_agree = all(r["class"] == r["sealed_atlas_class"] and r["inside_t_pi"]
                    for r in seg_rows)
    counts["segment_INSIDE-1SD"] = sum(
        1 for r in seg_rows if r["class"] == "INSIDE-1SD")

    atlas_rows = {r["osim_muscle"]: r for r in atlas["muscle_rows"]}
    row_agree = True
    for r in bio_rows:
        if r["mapping"]["kind"] != "1:1":
            continue
        a = atlas_rows[r["osim_muscle"]]
        for q in ("fiber_length", "tendon_length", "pennation"):
            if r["screens"][q]["class"] != a[q]["class"]:
                row_agree = False

    p1 = bool(
        counts["osim_muscles_total"] == EXPECTED_COUNTS["osim_muscles_total"]
        and all(all(f in m for f in MUSCLE_FIELDS) for m in src["osim_muscles"])
        and not any(any(("mass" in t.lower() or "pcsa" in t.lower())
                        for t in m["_tags"]) for m in src["osim_muscles"]))
    geo_census = scan_geometry_inference_rows(bio_rows)
    forb_census = scan_forbidden_sources_rows(bio_rows)

    checks = {
        "P1_osim_parse_identity": p1,
        "P2_placeholder_census": bool(
            counts["fmax_floor_default"] == EXPECTED_COUNTS["fmax_floor_default"]
            and counts["ofl_placeholder_all"]
            == EXPECTED_COUNTS["ofl_placeholder_all"]
            and counts["tsl_placeholder_all"]
            == EXPECTED_COUNTS["tsl_placeholder_all"]),
        "P3_fcu_slot_swap": slot_swap,
        "P4_screen_recomputation_agrees": bool(
            row_agree
            and counts["matched_1to1"] == EXPECTED_COUNTS["matched_1to1"]
            and counts["granular_not_comparable"]
            == EXPECTED_COUNTS["granular_not_comparable"]
            and counts["muscle_absent"] == EXPECTED_COUNTS["muscle_absent"]
            and all(counts["%s_%s" % (p, c)] == EXPECTED_COUNTS["%s_%s" % (p, c)]
                    for p, cs in (("fiber", ("INSIDE-1SD", "INSIDE-2SD", "OUTSIDE")),
                                  ("tendon", ("INSIDE-1SD", "INSIDE-2SD", "OUTSIDE")))
                    for c in cs)
            and all(counts["pennation_%s" % c] == EXPECTED_COUNTS["pennation_%s" % c]
                    for c in PEN_KEYS)
            and counts["t_pi_fiber_inside"] == EXPECTED_COUNTS["t_pi_fiber_inside"]
            and counts["t_pi_tendon_inside"] == EXPECTED_COUNTS["t_pi_tendon_inside"]),
        "P5_segment_screens": bool(
            seg_agree and counts["segment_INSIDE-1SD"]
            == EXPECTED_COUNTS["segment_INSIDE-1SD"]),
        "P6_namespaces_disjoint": bool(
            not ({r["osim_muscle"] for r in bio_rows}
                 & {r["id"] for r in eng_rows})
            and all(r["never_biological"] for r in eng_rows)
            and len(eng_rows) == 8 + eng_meta["m04_assignments"]),
        "P7_geometry_inference_census_zero": bool(not geo_census),
        "P8_inheritance_census_zero": bool(not forb_census),
    }

    doc = {
        "schema": SCHEMA,
        "identity": {
            "task_id": TASK_ID_LONG, "task_id_short": TASK_ID_SHORT,
            "title": "Define evidenced muscle/tendon parameter envelope",
            "criteria_sha256": CRITERIA_SHA256,
            "scope_sha256": SCOPE_SHA256,
            "definition_raw_sha256": DEFINITION_RAW_SHA256,
            "attempt_id": ATTEMPT_ID, "arrival_id": ARRIVAL_ID,
            "date_frozen": DATE_FROZEN, "base_head": BASE_HEAD,
            "done_when_verbatim": DONE_WHEN_VERBATIM,
            "card_observation_verbatim": CARD_OBSERVATION_VERBATIM,
            "card_falsifier_verbatim": CARD_FALSIFIER_VERBATIM,
        },
        "verification_profile": {
            "id": profile["id"], "kind": profile["kind"],
            "clean_view_required": profile["clean_view_required"],
            "camera_required_fields": profile["camera_required_fields"],
            "numerical_evidence_required": profile.get(
                "numerical_evidence_required", True),
            "nonvisual_reason": profile.get("nonvisual_reason", ""),
            "capture_status": "not_required_by_profile (records/offline)",
        },
        "input_pins": {"verified": True,
                       "pins": dict(sorted(INPUT_PINS.items()))},
        "selected_animal": {
            "species": "Macaca mulatta",
            "book_context": "adult female; body-mass reference band 5.4-6.9 kg "
                            "(Turnquist & Kessler 1989, midpoint 6.15 kg)",
            "two_mass_systems": {
                "body_mass_reference_kg": [5.4, 6.9],
                "body_mass_reference_use": "normalization basis for every "
                    "BW-normalized claim (re-pin study adjudication, Side B)",
                "walk_scene_dynamics_mass_kg": 10.038,
                "walk_scene_mass_use": "the sealed W03 scene assembly mass, "
                    "hash-anchored, uneditable; a DIFFERENT quantity (Side A)",
                "law": "register, do not repair; every mass claim names its "
                       "system",
            },
            "inheritance_law": "no human data and no differently scaled species "
                "data admissible; M. fascicularis tables sealed-inadmissible "
                "(S-MASS-08) and neither pinned nor read",
        },
        "biological_registry": {
            "schema_note": "source-backed rows would carry measured_source pins; "
                           "this sealed lineage carries NONE - every actuator row "
                           "is a declared carrier claim whose measured upgrade is "
                           "explicitly unresolved (U1-U3)",
            "actuator_row_count": len(bio_rows),
            "actuator_rows": [{k: v for k, v in r.items() if k != "_tags"}
                              for r in bio_rows],
        },
        "engineering_registry": {
            "schema_note": "chosen (authored) active-pressure material parameters "
                           "and the arm passive-law declaration; disjoint from the "
                           "biological registry by identity and by flag",
            "row_count": len(eng_rows),
            "rows": eng_rows,
            "carriers": eng_meta,
        },
        "unresolved_entries": unresolved,
        "calculation_contracts": contracts,
        "measured_reference": {
            "source": "host:M2-3_mulatta_morphometry.csv (license-internal; "
                      "derived statistics only in this artifact)",
            "n_subjects": 6,
            "band_discipline": "|claim-mean| <= 1 SD INSIDE-1SD; <= 2 SD "
                               "INSIDE-2SD; else OUTSIDE (boundaries inclusive)",
            "t_pi_multiplier": round(T_PI_MULTIPLIER, 6),
            "censored_pennation": "M2-3 prints '-' below 5 deg; claims <5 deg "
                                  "are CONSISTENT-CENSORED, claims >=5 deg "
                                  "against '-' are OUTSIDE-CENSORED; no SD math "
                                  "on censored cells",
            "applicability": "screening evidence only; n=6 order-of-magnitude "
                             "screens; the M2-8 regressions recover the source "
                             "sample's own mean body weight (~7.9 kg class), "
                             "ABOVE the 5.4-6.9 kg book context; screens never "
                             "flip sealed statuses",
            "segment_screens": seg_rows,
        },
        "counts": counts,
        "checks": checks,
        "law_statement": "no density/stiffness/activation law inferred from "
            "geometry alone; biological vs engineering parameters separated; no "
            "new fitting experiment run or authorized by this card; declared "
            "carrier values keep their honest provenance class",
    }
    return doc


def canonical_json(obj):
    return json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False,
                      separators=(",", ": ")) + "\n"


# ----------------------------------------------------------------- validator

def validate_document(doc, src):
    """Recompute-and-refuse validation of a (possibly tampered) document."""
    out = {"structurally_valid": False, "refusals": []}

    def refuse(code, detail=None):
        out["refusals"].append(code if detail is None else "%s:%s" % (code, detail))

    if doc.get("schema") != SCHEMA:
        refuse("a08_document_schema", doc.get("schema"))
    if doc.get("identity", {}).get("criteria_sha256") != CRITERIA_SHA256:
        refuse("criteria_identity_mismatch", "document identity")
    if doc.get("identity", {}).get("task_id_short") != TASK_ID_SHORT:
        refuse("a08_task_id_form", doc.get("identity", {}).get("task_id_short"))
    if not doc.get("input_pins", {}).get("verified"):
        refuse("source_pin_mismatch", "flags")

    fitted = scan_fitted_keys(doc)
    if fitted:
        refuse("fitting_unauthorized_refused", fitted[0])

    bio_rows = doc.get("biological_registry", {}).get("actuator_rows", [])
    geo = scan_geometry_inference_rows(bio_rows)
    if geo:
        refuse("geometry_only_inference_refused", geo[0])
    forb = scan_forbidden_sources_rows(bio_rows)
    if forb:
        refuse("human_norm_substitution_refused", "%s:%s" % forb[0])

    bio_ids = {r.get("osim_muscle") for r in bio_rows}
    eng_rows = doc.get("engineering_registry", {}).get("rows", [])
    eng_ids = {r.get("id") for r in eng_rows}
    overlap = bio_ids & eng_ids
    if overlap:
        refuse("engineering_value_in_biological_registry", sorted(overlap)[0])
    for r in eng_rows:
        if not r.get("never_biological"):
            refuse("engineering_value_in_biological_registry", r.get("id"))

    for u in doc.get("unresolved_entries", []):
        if u.get("status") != "explicitly_unresolved":
            refuse("silent_default_refused", u.get("id"))
        if "missing_evidence" not in u or "authorizing_rank" not in u:
            refuse("unresolved_entry_incomplete", u.get("id"))
    for r in bio_rows:
        if r.get("source_class") != "declared_carrier_not_source_backed":
            refuse("silent_default_refused",
                   str(r.get("osim_muscle")) + ":source_class")

    # independent oracle: recompute screens + counts from pinned bytes
    try:
        fresh_rows = compute_bio_rows(src)
        fresh_counts = compute_counts(fresh_rows, src)
    except ValueError as exc:
        refuse("a08_recompute_failed", str(exc))
        fresh_rows, fresh_counts = [], {}
    fresh_by_name = {r["osim_muscle"]: r for r in fresh_rows}
    for r in bio_rows:
        f = fresh_by_name.get(r.get("osim_muscle"))
        if f is None:
            refuse("screen_classification_mismatch",
                   str(r.get("osim_muscle")) + ":row")
            continue
        if r.get("screens") and f.get("screens"):
            for q in ("fiber_length", "tendon_length", "pennation"):
                if r["screens"][q]["class"] != f["screens"][q]["class"]:
                    refuse("screen_classification_mismatch",
                           "%s:%s:%s" % (r["osim_muscle"], q,
                                         r["screens"][q]["class"]))
    doc_counts = doc.get("counts", {})
    for k, v in fresh_counts.items():
        if doc_counts.get(k) != v:
            refuse("a08_counts_mismatch", k)
    for k in ("P1_osim_parse_identity", "P2_placeholder_census", "P3_fcu_slot_swap",
              "P4_screen_recomputation_agrees", "P5_segment_screens",
              "P6_namespaces_disjoint", "P7_geometry_inference_census_zero",
              "P8_inheritance_census_zero"):
        if doc.get("checks", {}).get(k) is not True:
            refuse("a08_check_false", k)

    out["structurally_valid"] = not out["refusals"]
    return out


# ---------------------------------------------------------------- registry

def load_registry_profile():
    con = sqlite3.connect("file:%s?mode=ro" % REGISTRY_DB.as_posix(), uri=True,
                          timeout=10)
    try:
        payload = con.execute("select payload from state where id='1'").fetchone()[0]
    finally:
        con.close()
    state = json.loads(payload)
    card = state["kanban"]["cards"][TASK_ID_LONG]
    task = card["spec"]["ontology_qualification"]["task"]
    vp = task["verification_profile"]
    for key in ("id", "kind", "views", "clean_view_required", "diagnostic_layers",
                "camera_required_fields"):
        require(key in vp, "registry_profile_key_missing", key)
    require(vp["id"] == "records" and vp["kind"] == "offline",
            "registry_profile_kind", (vp["id"], vp["kind"]))
    require(vp["clean_view_required"] is False
            and vp["camera_required_fields"] == [],
            "records_profile_shape", (vp["clean_view_required"],
                                      len(vp["camera_required_fields"])))
    require(CANONICAL_LAYERS == set(), "a08_tripwire_layers_supply", "readonly")
    require(card["criteria_sha256"] == CRITERIA_SHA256,
            "criteria_identity_mismatch", "registry card")
    att = card["attempts"][ATTEMPT_ID]
    require(att["criteria_sha256"] == CRITERIA_SHA256,
            "criteria_identity_mismatch", "attempt")
    require(att["agent_id"] == ARRIVAL_ID, "attempt_owner_mismatch", att["agent_id"])
    prov = {
        "db_path": str(REGISTRY_DB),
        "row_path": "state[id=1].kanban.cards.MAT2-A08.spec.ontology_qualification"
                    ".task.verification_profile",
        "extractor": "sqlite3 mode=ro; json payload; card+attempt criteria asserted",
        "mode": "READ_ONLY (G7/P7)",
        "note": "CANONICAL_LAYERS tripwire present and empty: the records/offline "
                "profile declares no diagnostic layers; a shape change fails "
                "loudly instead of silently projecting",
        "criteria_sha256_card": card["criteria_sha256"],
        "criteria_sha256_attempt": att["criteria_sha256"],
    }
    return vp, prov


# ------------------------------------------------------------- falsifier run

def run_falsifiers(src, doc):
    arms = []
    base_ok = validate_document(doc, src)
    clean_pass = base_ok["structurally_valid"]

    def add(name, tampered_doc, expect_code):
        require(clean_pass, "a08_fb_premature", name)
        res = validate_document(tampered_doc, src)
        bit = not res["structurally_valid"]
        arms.append({
            "arm": name, "expected_refusal": expect_code, "bit": bool(bit),
            "observed": ",".join(res["refusals"]),
            "clean_control": {
                "metric_scope": "recompute validator on the untampered emitted "
                                "document",
                "structurally_valid": clean_pass,
                "within_tolerance": clean_pass,
                "guard": "a08_fb_premature",
            },
        })

    t = copy.deepcopy(doc)
    t["biological_registry"]["actuator_rows"][0]["stiffness_from_geometry"] = {
        "value": 1234.5, "unit": "N/m",
        "derived_from": "path geometry and mesh volume"}
    add("FB1_geometry_only_inference", t, "geometry_only_inference_refused")

    t = copy.deepcopy(doc)
    t["biological_registry"]["actuator_rows"][0]["measured_source"] = \
        "human norm strength table"
    add("FB2_human_norm_substitution", t, "human_norm_substitution_refused")

    t = copy.deepcopy(doc)
    t["biological_registry"]["actuator_rows"][0]["osim_muscle"] = \
        "m03_damping_per_s"
    add("FB3_namespace_mixing", t, "engineering_value_in_biological_registry")

    t = copy.deepcopy(doc)
    t["fitted_muscle_params"] = {"note": "optimizer output"}
    add("FB4_unauthorized_fitting", t, "fitting_unauthorized_refused")

    t = copy.deepcopy(doc)
    for r in t["biological_registry"]["actuator_rows"]:
        if r.get("screens") and r["screens"]["fiber_length"]["class"] == "OUTSIDE":
            r["screens"]["fiber_length"]["class"] = "INSIDE-1SD"
            break
    add("FB6_screen_flip", t, "screen_classification_mismatch")

    t = copy.deepcopy(doc)
    t["unresolved_entries"][0]["status"] = "resolved"
    t["unresolved_entries"][0].pop("missing_evidence", None)
    add("FB7_silent_default", t, "silent_default_refused")

    # FB5 pin mutation (read-level probe; clean pins verified by --emit/--verify)
    fb5_ok = False
    if clean_pass:
        try:
            read_pinned(M3_CARRIER, "0" * 64, "fb5-mutated-pin")
        except ValueError as exc:
            fb5_ok = "input_pin_drift" in str(exc)
        require(fb5_ok, "a08_fb5_premature", "pin probe")
        arms.append({
            "arm": "FB5_source_pin_mutation",
            "expected_refusal": "input_pin_drift", "bit": bool(fb5_ok),
            "observed": "input_pin_drift:host:pressure_state.json",
            "clean_control": {
                "metric_scope": "pin verifier on the untampered carrier bytes",
                "structurally_valid": clean_pass, "within_tolerance": True,
                "guard": "a08_fb5_premature"}})

    all_green = all(a["bit"] for a in arms) and clean_pass
    return {"schema": FALSIFIER_SCHEMA, "F_all_green": bool(all_green),
            "clean_document_valid": bool(clean_pass),
            "arms": arms,
            "vacuous_comparison_guard": vacuous_guard_selftest(),
            "note": "clean control runs FIRST on every arm; a bit without a "
                    "passing clean control is refused (a08_fb_premature)"}


# ---------------------------------------------------------------------- CLI

def main(argv):
    require(vacuous_guard_selftest()["fires_on_identically_zero_window"],
            "a08_vacuous_guard_required")
    profile, prov = load_registry_profile()
    src = load_sources()
    doc = build_document(src, profile)
    doc_bytes = canonical_json(doc).encode("utf-8")

    emit = "--emit" in argv
    verify = "--verify" in argv
    tamper = "--tamper-all" in argv
    evidence = "--evidence" in argv
    receipt = "--receipt" in argv

    out_doc = CARD_DIR / "parameter_envelope.json"
    if emit:
        second = canonical_json(build_document(load_sources(), profile))
        require(second.encode("utf-8") == doc_bytes, "a08_determinism_broken",
                "emit")
        out_doc.write_bytes(doc_bytes)
        print("emit ok sha256", sha256_bytes(doc_bytes))

    if verify:
        disk = out_doc.read_bytes()
        res = validate_document(json.loads(disk.decode("utf-8")), src)
        rebuilt = canonical_json(build_document(src, profile)).encode("utf-8")
        require(rebuilt == disk, "a08_stale_emitted_document",
                "rebuild differs from disk bytes")
        print("verify", "PASS" if res["structurally_valid"] else "FAIL",
              json.dumps(res["refusals"]))
        if not res["structurally_valid"]:
            return 1

    if tamper:
        disk_doc = json.loads(out_doc.read_bytes().decode("utf-8"))
        fr = run_falsifiers(src, disk_doc)
        (CARD_DIR / "evidence").mkdir(exist_ok=True)
        (CARD_DIR / "evidence" / "falsifier_receipt.json").write_bytes(
            canonical_json(fr).encode("utf-8"))
        print("tamper arms:", len(fr["arms"]), "all_green:", fr["F_all_green"])
        if not fr["F_all_green"]:
            return 1

    if evidence:
        (CARD_DIR / "evidence").mkdir(exist_ok=True)
        snap = {"schema": PROFILE_SNAPSHOT_SCHEMA, "task_id": TASK_ID_SHORT,
                "profile": profile, "criteria_sha256": CRITERIA_SHA256}
        (CARD_DIR / "evidence" / "registry_verification_profile.json").write_bytes(
            canonical_json(snap).encode("utf-8"))
        (CARD_DIR / "evidence" / "registry_profile_provenance.json").write_bytes(
            canonical_json(prov).encode("utf-8"))
        print("evidence snapshots written")

    if receipt:
        qr = {
            "schema": RECEIPT_SCHEMA,
            "task_id": TASK_ID_LONG, "planning_task_id": TASK_ID_SHORT,
            "title": "Define evidenced muscle/tendon parameter envelope",
            "attempt_id": ATTEMPT_ID, "arrival_id": ARRIVAL_ID,
            "date": DATE_FROZEN,
            "base_head": BASE_HEAD,
            "preregistration_commit_history": prereg_commits(),
            "candidate_head": git_head(),
            "criteria_sha256": CRITERIA_SHA256,
            "done_when_verbatim": DONE_WHEN_VERBATIM,
            "card_observation_verbatim": CARD_OBSERVATION_VERBATIM,
            "depends_on": {
                "MAT2-A06": {"state": "DONE (merged PR #250 lineage; sealed "
                                    "registry consumed as committed bytes)",
                             "registry_pin": INPUT_PINS["repo:" + A06_REL]},
                "MAT2-M10": {"state": "DONE (merged PR #271 = base head)"}},
            "document_sha256": sha256_bytes(out_doc.read_bytes()),
            "falsifier_receipt_sha256": sha256_bytes(
                (CARD_DIR / "evidence" / "falsifier_receipt.json").read_bytes()),
            "file_identities": {
                name: sha256_bytes((CARD_DIR / name).read_bytes())
                for name in ("parameter_envelope.py",
                             "test_parameter_envelope.py", "make_report.py",
                             "lint_report_numbers.py", "PREREGISTRATION.md",
                             "parameter_envelope.json",
                             "evidence/falsifier_receipt.json",
                             "evidence/registry_verification_profile.json",
                             "evidence/registry_profile_provenance.json")},
            "profile_note": "records/offline: capture/camera evidence classes "
                "are NOT REQUIRED by the registry profile (clean_view_required "
                "false, camera_required_fields empty); numerical evidence is the "
                "recomputed envelope document plus the sealed-band screen oracle",
        }
        (CARD_DIR / "qualification_receipt.json").write_bytes(
            canonical_json(qr).encode("utf-8"))
        print("qualification receipt written; candidate head",
              qr["candidate_head"][:10])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
