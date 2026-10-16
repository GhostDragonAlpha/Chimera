"""piece_record_checks.py -- THE REGISTERED FALSIFIER BATTERY for the
§11.20.1 piece-record layer (first increment of 11.20 "artificial
proteins"). Six checks on the house harness (tools/port_registry.py
port_test/expect); exit 0 = the three qualified artifacts are library
citizens. Scope: the piece library's record layer over the REAL retained
evidence; the packet's 1e-6 law is quoted, never widened.

  (a) completeness: the three records carry every required section, and a
      record with an unknown top-level field is refused by name
      (piece_unknown_field).
  (b) evidence + DOMAIN: every receipt id resolves to a real file, AND
      each record's valid-load/scale claims are covered by in-gate
      measured cases in the cited receipts -- a star record claiming
      scale support at 1.5x/2.0x is REFUSED (piece_domain_unmeasured)
      because the chain receipt records the scale drift OVER the gate
      there. Domain drift is caught, not just link rot.
  (c) work accounting: for one solved case (the k=2 star at scale 1.0),
      the port work along a QUASISTATIC 9-point load ramp equals the
      stored surface-energy change within the preregistered 1e-3
      relative tolerance (measured 1.99e-4: 8-interval trapezoid +
      the solver's stagnation floor). Honest finding recorded: the
      ramp's INTERMEDIATE states stagnate over the packet's unchanged
      1e-6 gate -- only the endpoints are qualified states.
  (d) recipe immutability: the star record's recipe hash matches a
      recomputation, and its TWO instances share that immutable recipe
      while their state hashes differ (state separation).
  (e) naming grants nothing: a copy of the star record renamed to
      "muscle" WITH a function_label claim but no measured anchors or
      evidence is refused function_card_required.
  (f) failure persistence: a copy of the star record dropping the
      rejected table/learned representation entries is refused
      representations_incomplete.

Run:  python tools/mechanism_factory/piece_record_checks.py
      exit 0 = all PASS, 1 = a check failed, 2 = evidence-path refusal.
"""
from __future__ import annotations

import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_TOOLS = _HERE.parent
sys.path.insert(0, str(_TOOLS))
sys.path.insert(0, str(_TOOLS / "membrane_scale_lab"))
sys.path.insert(0, str(_HERE))

from port_registry import port_test, expect        # noqa: E402 harness
import piece_record as pr                           # noqa: E402 the layer
import composed_patch as cp                         # noqa: E402 pieces/laws
import composed_chain as cc                         # noqa: E402 the star
import receipt_adapter as ra                        # noqa: E402 the judge

PACKET = cp.PACKET_PATH
EVID_DIR = cp.EVID_DIR

# the REAL retained receipts the records cite (all must resolve)
V2_RECEIPT = "qualification_receipt_20261016T075038.618903Z.json"
MULTI_RECEIPT = "qualification_receipt_20261016T075137.420787Z.json"
ASM1_RECEIPT = "composed_qualification_receipt_20261016T075201.116240Z.json"
CHAIN_RECEIPT = "composed_chain_receipt_20261016T092136.068087Z.json"
CHAIN_CHECKS = "composed_chain_checks_20261016T093949.650913Z.json"
FIT_RECEIPT = "fit_receipt_20261016T075201.333890Z.json"
FIT_JOB_RECEIPT = "fit_job_receipt_20261016T075339.472945Z.json"
LINEAR_T7 = "bounded_fit_checks_20261016T012234.469338Z.json"

LAW_REV = pr.law_revision()
UNITS = pr.units()
GATE_N = pr.packet_gate()

# PREREGISTERED ALLOWANCES (frozen before the battery run; nothing widened)
ALLOWANCES = {
    "work_accounting_rel_tol": 1.0e-3,   # quasistatic identity |W-dS|/|dS|;
                                          # measured 1.985e-4 with a
                                          # 9-point trapezoid ramp (the
                                          # discretization + the solver's
                                          # stagnation floor dominate)
    "ramp_points": 9,
    "ramp_finding": "the ramp's INTERMEDIATE states (lambda 0.25-0.625) "
                    "stagnate OVER the packet's unchanged 1e-6 gate "
                    "(up to 2.8e-6 N); only the endpoints are qualified "
                    "states -- recorded, not tuned",
    "balance_law_source": "example_packet.acceptance_thresholds",
    "scale_drift_note": "star scales 1.5x/2.0x honestly OVER the gate "
                        "(chain receipt scale_window_finding); a record "
                        "claiming them is refused piece_domain_unmeasured",
}
EXPECTED_CHECKS = 6


def _pins(*relpaths) -> dict:
    return {r: pr._sha256_file(cp._REPO / r) for r in relpaths}


def _record_patch() -> dict:
    return {
        "record_id": "piece.patch-equilibrium",
        "kind": "piece",
        "name": "Full-rim-pinned high-degree fan patch under the "
                "constant-gamma current-area surface-energy law",
        "design_recipe": {
            "immutable": True, "executable_code": False,
            "nodes": [{"node_id": "fan", "kind": "patch",
                        "generator": "fixture_generator.high_degree_fan",
                        "params": {"n_rim": 200, "radius": 1.0,
                                    "height": 0.3},
                        "seed": 1, "parent_ids": []}],
            "edges": [],
        },
        "physical_definition": {
            "law_id": "constant-gamma-current-area-surface-energy",
            "law_revision": LAW_REV,
            "units": UNITS,
            "topology": "one triangular fan membrane: 200 rim vertices "
                        "pinned, 1 free apex, 200 faces",
            "reference_configuration": "the generator's seeded rest "
                                        "geometry (fixture_generator)",
            "valid_loads_N": [0.4, 0.8, 1.2, 1.6, 2.0],
            "valid_scales": [0.5, 0.75, 1.0, 2.0],
            "excluded_phenomena": [
                "loads on pinned vertices (load_on_fixed_vertex)",
                "loads with zero tension (LOAD_ZERO_TENSION: U unbounded "
                "below, no equilibrium exists)",
                "free seam rings: NO equilibrium under this law (witness "
                "(g): step_limit, free residual ~1e0)",
                "grounded rings: bit-for-bit zero port transfer",
                "rim-weld chains: impossible; apex welds only",
            ],
            "measured_in": [V2_RECEIPT, MULTI_RECEIPT, ASM1_RECEIPT,
                             CHAIN_RECEIPT],
        },
        "ports": [
            {"port_id": "seam-apex", "kind": "input",
             "patch_geometry": "the free apex vertex (index n_rim)",
             "local_frame": "vertical axis; +z up, load applied -z",
             "exchanges": "vertical dead load [N], displacement [m]",
             "sign_convention": "work W = f.x positive when the load "
                                 "displaces along its own direction",
             "variables": {"prescribed": "vertical dead load magnitude "
                                          "(|f| <= packet max_force_N 2.0)",
                            "free": "apex displacement (x,y,z)"},
             "work_accounting": "quasistatic: W_port = stored-energy "
                                 "change along the load ramp (battery "
                                 "check (c))"},
            {"port_id": "rim-ground", "kind": "output",
             "patch_geometry": "the 200 pinned rim vertices",
             "local_frame": "global frame at rest coordinates",
             "exchanges": "reaction forces [N] at the pins",
             "sign_convention": "reactions are the pin-APPLIED forces "
                                 "reported by the solver",
             "variables": {"prescribed": "rim positions (fixed)",
                            "free": "none (grounded)"},
             "work_accounting": "pins do no work (zero displacement)"},
        ],
        "instance_state": {
            "owner": "piece_record layer (no engine runtime exists yet); "
                     "recipes are immutable and shared, state is per "
                     "instance",
            "instances": [
                {"instance_id": "piece.patch-equilibrium.instance-1",
                 "state": {"stored_energy_J": 6.274436846,
                            "state_kind": "zero-load rest equilibrium "
                                          "of the star's ground piece"},
                 "state_hash": None},
            ],
        },
        "representations": [
            {"kind": "direct-reference", "status": "qualified",
             "receipt_ids": [V2_RECEIPT, MULTI_RECEIPT],
             "note": "the solver itself is the reference representation; "
                     "three frozen CPU cases + 5-point load sweep, all "
                     "within the packet thresholds"},
            {"kind": "table", "status": "rejected_at_gate",
             "receipt_ids": [FIT_RECEIPT, LINEAR_T7],
             "measured": {"pchip_loo_max_N": 1.4422663666699073e-04,
                           "linear_loo_max_N": 3.9416871530697714e-04,
                           "gate_N": GATE_N},
             "note": "RETAINED FAILURE: bounded knot table REJECTED at "
                     "the preregistered 1e-6 LOO gate; nothing widened"},
            {"kind": "learned", "status": "rejected_at_gate",
             "receipt_ids": [FIT_JOB_RECEIPT],
             "measured": {"validation_max_error_N": 3.366755675170242e-02,
                           "gate_N": GATE_N,
                           "physically_qualified": False},
             "note": "RETAINED FAILURE: CPU learned candidate stopped; "
                     "renaming it cannot erase the failure"},
        ],
        "function_card": {
            "function_label": "",
            "measured_response_anchors": [
                {"quantity": "pin reactions vs vertical load magnitude",
                  "measured_in": MULTI_RECEIPT,
                  "values": "5 magnitudes per train/validation family, "
                            "residuals 2.2e-9..1.2e-7 N (all in-gate)"},
                {"quantity": "stored surface energy at 0.8 N",
                  "measured_in": CHAIN_RECEIPT, "values": "see receipts"}],
            "operating_domain": "vertical dead loads 0.4-2.0 N "
                                 "(packet max_force_N); rigid scales "
                                 "0.5x/0.75x/1.0x/2.0x as measured by the "
                                 "cited composed receipts; rim fully pinned",
            "costs": {"reference_solve": "~15-19 s CPU mean per case "
                                           "(fit receipt probe)",
                       "table_probe": "23.5 us shadow (unqualified)"},
            "failures": ["bounded table rejected at LOO gate",
                          "learned candidate rejected (3.37e-2 N)",
                          "1.5x/2.0x assembly scales over the unchanged "
                          "gate (star topology)"],
            "evidence_ids": [V2_RECEIPT, MULTI_RECEIPT, FIT_RECEIPT,
                              FIT_JOB_RECEIPT],
            "freshness": {"source_pins": _pins(
                "tools/membrane_scale_lab/surface_energy_reference.py",
                "tools/mechanism_factory/patch_equilibrium.py")},
        },
        "fabrication_binding": {
            "required_material": "constant-gamma membrane; gamma from the "
                                  "pinned lab law [J/m^2]",
            "required_energy": "none beyond solver CPU (no engine runtime)",
            "permitted_assembly_ops": ["apex-weld"],
            "exclusions": ["free seam rings (witness (g))",
                            "grounded rings (zero transfer)",
                            "rim welds: impossible under the seam law"],
            "physical_to_render": "unset: no engine binding exists yet "
                                   "(recorded honestly, not claimed)",
        },
    }


def _record_law() -> dict:
    return {
        "record_id": "law.apex-weld-seam",
        "kind": "law",
        "name": "The apex-weld seam law: hangers weld only at apexes, "
                "reflected about (hA + h)/2, seam owned by the ground "
                "piece",
        "design_recipe": {
            "immutable": True, "executable_code": False,
            "nodes": [], "edges": [],
            "law_spec": {
                "coordinate_agreement_tol": 1.0e-12,
                "refusal": "seam_vertex_coordinate_mismatch before any "
                            "solve",
                "placement": "hanger reflection z -> (hA + h) - z; "
                             "reduces to assembly 1's transform for "
                             "hangers with h = hA (byte-identical reuse)",
                "winding_fix": "reflected faces get [0, 2, 1] winding",
                "ownership": "one seam vertex, owned by the ground piece, "
                             "referenced by every hanger; deduplicated",
            },
        },
        "physical_definition": {
            "law_id": "apex-weld-seam",
            "law_revision": LAW_REV,
            "units": UNITS,
            "topology": "any connected assembly of fan patches is a "
                        "single-seam star (one grounded piece + k "
                        "inverted hangers); two-seam chains cannot exist",
            "reference_configuration": "n/a (a law, not a geometry)",
            "valid_loads_N": [0.8],
            "valid_scales": [0.5, 0.75, 1.0, 2.0],
            "excluded_phenomena": [
                "rim welds (witness (g): free seam rings have no "
                "equilibrium, residual ~1.08)",
                "grounded rings (zero transfer, bit-for-bit)",
                "seam coordinate mismatch above 1e-12 (refused before "
                "any solve)",
                "second ownership claims (SEAM_OWNER_CONFLICT)",
            ],
            "measured_in": [ASM1_RECEIPT, CHAIN_RECEIPT, CHAIN_CHECKS],
        },
        "ports": [
            {"port_id": "weld-interface", "kind": "input",
             "patch_geometry": "one shared seam vertex; the opposing "
                                "films' pull balances the transferred "
                                "load (real port transfer)",
             "local_frame": "vertical axis at the seam apex",
             "exchanges": "load transfer through the weld [N]",
             "sign_convention": "transfer measured by the port net "
                                 "reaction norms",
             "variables": {"prescribed": "weld topology (which apexes)",
                            "free": "seam vertex DOFs"},
             "work_accounting": "port transfer measured via block mean "
                                 "reaction norms (margin 0.488 in the "
                                 "star)"},
        ],
        "instance_state": {
            "owner": "piece_record layer; the law is immutable, shared "
                     "by every assembly record citing it",
            "instances": [
                {"instance_id": "law.apex-weld-seam.application-star-k2",
                 "state": {"applied_to": "assembly.star-k2"},
                 "state_hash": None},
            ],
        },
        "representations": [
            {"kind": "direct-reference", "status": "qualified",
             "receipt_ids": [ASM1_RECEIPT, CHAIN_RECEIPT, CHAIN_CHECKS],
             "note": "qualified twice: assembly 1 (0.5x/1.0x/2.0x) and "
                     "the byte-identical-reuse star (1.0x/0.75x)"},
        ],
        "function_card": {
            "function_label": "",
            "measured_response_anchors": [
                {"quantity": "weld transfer margin", "measured_in":
                    CHAIN_CHECKS, "values": "0.488 block margin; port "
                    "nets 0.922/0.737 N at 1.0x"}],
            "operating_domain": "fan-patch assemblies whose pieces each "
                                 "have exactly one apex",
            "costs": {"weld": "placement reflection + index remap; no "
                               "extra solve cost"},
            "failures": ["rim-weld chains: structurally impossible "
                         "(witness (g), recorded in composed receipts)"],
            "evidence_ids": [ASM1_RECEIPT, CHAIN_RECEIPT, CHAIN_CHECKS],
            "freshness": {"source_pins": _pins(
                "tools/mechanism_factory/composed_patch.py",
                "tools/mechanism_factory/composed_chain.py")},
        },
        "fabrication_binding": {
            "required_material": "as for the pieces it joins",
            "required_energy": "none beyond solver CPU",
            "permitted_assembly_ops": ["apex-weld"],
            "exclusions": ["every seam topology other than apex welds "
                           "(witness (g))"],
            "physical_to_render": "unset: no engine binding exists yet",
        },
    }


def _record_star() -> dict:
    rec = {
        "record_id": "assembly.star-k2",
        "kind": "assembly",
        "name": "The k=2 fan-out star: ground piece A + inverted hangers "
                "B and C, two apex welds at one seam vertex",
        "design_recipe": {
            "immutable": True, "executable_code": False,
            "nodes": [
                {"node_id": "A", "kind": "patch",
                  "generator": "fixture_generator.high_degree_fan",
                  "params": {"n_rim": 200, "radius": 1.0, "height": 0.3},
                  "seed": 1, "parent_ids": [],
                  "role": "ground piece; owns the seam; input port"},
                {"node_id": "B", "kind": "patch",
                  "generator": "fixture_generator.high_degree_fan",
                  "params": {"n_rim": 200, "radius": 0.8, "height": 0.3},
                  "seed": 2, "parent_ids": [],
                  "role": "reused hanger; far rim = output port"},
                {"node_id": "C", "kind": "patch",
                  "generator": "fixture_generator.high_degree_fan",
                  "params": {"n_rim": 200, "radius": 0.5, "height": 0.25},
                  "seed": 3, "parent_ids": [],
                  "role": "new hanger; far rim = output port"}],
            "edges": [
                {"edge_id": "weld-A-B", "kind": "apex-weld",
                  "endpoints": ["A", "B"], "seam_owner": "A",
                  "law_id": "apex-weld-seam"},
                {"edge_id": "weld-A-C", "kind": "apex-weld",
                  "endpoints": ["A", "C"], "seam_owner": "A",
                  "law_id": "apex-weld-seam"}],
        },
        "physical_definition": {
            "law_id": "constant-gamma-current-area-surface-energy + "
                       "apex-weld-seam",
            "law_revision": LAW_REV,
            "units": UNITS,
            "topology": "601 vertices / 600 faces / 600 pins; one seam "
                         "vertex carrying both welded joints",
            "reference_configuration": "built star mesh (byte-identical "
                                        "reuse of assembly 1's A and B "
                                        "blocks, hashed by reuse check (a))",
            "valid_loads_N": [0.8],
            "valid_scales": [0.75, 1.0],
            "excluded_phenomena": [
                "scales 1.5x/2.0x for THIS topology: measured OVER the "
                "packet's unchanged 1e-6 gate (1.11e-6 / 1.64e-6 N) -- "
                "domain drift recorded, not tuned",
                "free seam rings and rim welds (witness (g))",
                "loads on pinned vertices"],
            "measured_in": [CHAIN_RECEIPT, CHAIN_CHECKS],
            "reuse_lineage": [ASM1_RECEIPT],
        },
        "ports": [
            {"port_id": "star-input-seam-apex", "kind": "input",
             "patch_geometry": "the seam apex on piece A's side (the "
                                "only legal free vertex)",
             "local_frame": "vertical axis; load applied -z",
             "exchanges": "vertical dead load [N], displacement [m]",
             "sign_convention": "W = f.x, positive along the load",
             "variables": {"prescribed": "vertical dead load 0.8 N",
                            "free": "seam displacement"},
             "work_accounting": "quasistatic ramp identity (check (c))"},
            {"port_id": "star-output-B-rim", "kind": "output",
             "patch_geometry": "piece B's 200 far-rim pins",
             "local_frame": "global frame",
             "exchanges": "reaction forces [N]",
             "sign_convention": "port net = sum of pin reactions",
             "variables": {"prescribed": "far-rim positions (fixed)",
                            "free": "none"},
             "work_accounting": "measured port net 0.922 N at 1.0x"},
            {"port_id": "star-output-C-rim", "kind": "output",
             "patch_geometry": "piece C's 200 far-rim pins",
             "local_frame": "global frame",
             "exchanges": "reaction forces [N]",
             "sign_convention": "port net = sum of pin reactions",
             "variables": {"prescribed": "far-rim positions (fixed)",
                            "free": "none"},
             "work_accounting": "measured port net 0.737 N at 1.0x"},
        ],
        "instance_state": {
            "owner": "piece_record layer (no engine runtime yet); two "
                     "instances SHARE this immutable recipe and own "
                     "SEPARATE state",
            "instances": [
                {"instance_id": "assembly.star-k2.instance-loaded",
                 "state": {"applied_load_N": 0.8,
                            "stored_surface_energy_J": 6.315991884,
                            "seam_z_wu": 0.284380,
                            "free_residual_N": 7.076e-07},
                 "state_hash": None},
                {"instance_id": "assembly.star-k2.instance-rest",
                 "state": {"applied_load_N": 0.0,
                            "stored_surface_energy_J": 6.274436846,
                            "seam_z_wu": 0.386957,
                            "free_residual_N": 9.794e-08},
                 "state_hash": None},
            ],
        },
        "representations": [
            {"kind": "direct-reference", "status": "qualified",
             "receipt_ids": [CHAIN_RECEIPT, CHAIN_CHECKS],
             "note": "ONE solve_equilibrium per scale; 6/6 reuse battery; "
                     "adapter PASS under the unchanged composed-v1 "
                     "schema"},
            {"kind": "table", "status": "rejected_at_gate",
             "receipt_ids": [FIT_RECEIPT],
             "measured": {"pchip_loo_max_N": 1.4422663666699073e-04,
                           "gate_N": GATE_N},
             "note": "the piece library's table representation is "
                     "REJECTED for every member; retained here too"},
            {"kind": "learned", "status": "rejected_at_gate",
             "receipt_ids": [FIT_JOB_RECEIPT],
             "measured": {"validation_max_error_N": 3.366755675170242e-02,
                           "gate_N": GATE_N},
             "note": "RETAINED FAILURE: stopped without success"},
        ],
        "function_card": {
            "function_label": "",
            "measured_response_anchors": [
                {"quantity": "input->output transfer through both welds",
                  "measured_in": CHAIN_CHECKS,
                  "values": "block margin 0.488; port nets 0.922 / 0.737 "
                             "N at 1.0x"},
                {"quantity": "coupled balance",
                  "measured_in": CHAIN_RECEIPT,
                  "values": "free residual 7.32e-7 N <= the packet's "
                             "unchanged 1e-6 law at 1.0x; 3.36e-7 at "
                             "0.75x"}],
            "operating_domain": "vertical dead load 0.8 N; rigid scales "
                                 "0.75x and 1.0x ONLY (1.5x/2.0x measured "
                                 "over the unchanged gate)",
            "costs": {"solve": "two CPU solves (601-vertex meshes), "
                                "minutes"},
            "failures": ["scale drift at 1.5x/2.0x (over the gate)",
                          "rim-weld chain alternatives impossible "
                          "(witness (g))"],
            "evidence_ids": [CHAIN_RECEIPT, CHAIN_CHECKS, FIT_RECEIPT,
                              FIT_JOB_RECEIPT],
            "freshness": {"source_pins": _pins(
                "tools/mechanism_factory/composed_chain.py",
                "tools/mechanism_factory/composed_patch.py",
                "tools/membrane_scale_lab/surface_energy_reference.py")},
        },
        "fabrication_binding": {
            "required_material": "constant-gamma membrane pieces",
            "required_energy": "none beyond solver CPU",
            "permitted_assembly_ops": ["apex-weld"],
            "exclusions": ["rim welds; free/grounded rings (witness (g)); "
                            "any second seam vertex"],
            "physical_to_render": "unset: no engine binding exists yet",
        },
    }
    # additive amendments made AFTER this record was first retained (the
    # 11.20.5 port-based representation, amended by port_solve_checks and
    # archived under pieces/archive/) are carried forward so this
    # battery's idempotent write matches the retained bytes
    try:
        retained = pr.load_record("assembly.star-k2")
        for r in retained["representations"]:
            if r["kind"] not in {x["kind"] for x in rec["representations"]}:
                rec["representations"].append(r)
    except pr.PieceRecordRefused:
        pass                                    # first run: not yet retained
    return rec


def _state_hashes_fill(*records: dict) -> None:
    for rec in records:
        rec["design_recipe"]["recipe_hash"] = pr.recipe_hash(
            rec["design_recipe"])
        for i in rec["instance_state"]["instances"]:
            i["state_hash"] = pr.state_hash(i["state"])


def _refused(payload: dict):
    try:
        pr.validate(copy.deepcopy(payload))
    except pr.PieceRecordRefused as ex:
        return ex.reason
    return None


# ── (a) ─────────────────────────────────────────────────────────────────────

@port_test(
    "a_record_completeness",
    "The three library records (piece.patch-equilibrium, "
    "law.apex-weld-seam, assembly.star-k2) carry every required 11.20.1 "
    "section and validate; a record with an unknown top-level field is "
    "refused by name (piece_unknown_field).",
    "A required section is missing, an unknown field is accepted, or a "
    "record fails validation for a real reason.")
def a_completeness() -> dict:
    patch, law, star = _record_patch(), _record_law(), _record_star()
    _state_hashes_fill(patch, law, star)
    p1 = pr.write_record(copy.deepcopy(patch))
    p2 = pr.write_record(copy.deepcopy(law))
    p3 = pr.write_record(copy.deepcopy(star))
    forged = copy.deepcopy(star)
    forged["muscle_flag"] = "grants strength"
    reason = _refused(forged)
    ok = bool(p1.is_file() and p2.is_file() and p3.is_file()
              and reason == "piece_unknown_field")
    return {"pass": ok,
            "measured": {"records": [p1.name, p2.name, p3.name],
                          "unknown_field_refused_as": reason}}


# ── (b) ─────────────────────────────────────────────────────────────────────

@port_test(
    "b_evidence_links_and_domain_match",
    "Every receipt id in the three records resolves to a real file, AND "
    "the domain claims are covered by IN-GATE measured cases in the "
    "cited receipts: the star's valid scales are exactly {0.75, 1.0}; a "
    "copy claiming 1.5x/2.0x is refused piece_domain_unmeasured because "
    "the chain receipt records the scale drift OVER the gate there.",
    "A receipt id dangles, a domain claim exceeds what the cited "
    "receipts measured in-gate, or the refusal fires for the wrong "
    "reason.")
def b_evidence_and_domain() -> dict:
    patch = pr.load_record("piece.patch-equilibrium")
    law = pr.load_record("law.apex-weld-seam")
    star = pr.load_record("assembly.star-k2")
    cited = pr._receipt_ids(patch) + pr._receipt_ids(law) \
        + pr._receipt_ids(star)
    dangling = [n for n in set(cited) if not list(pr.EVID_ROOT.rglob(n))]
    scales_p, loads_p = pr.measured_domain(
        [pr.EVID_ROOT / n for n in pr._receipt_ids(patch)])
    scales_s_all, loads_s = pr.measured_domain(
        [pr.EVID_ROOT / n for n in pr._receipt_ids(star)])
    scales_law, _ = pr.measured_domain(
        [pr.EVID_ROOT / n for n in pr._receipt_ids(law)])
    # the star's PRIMARY domain receipt is the chain receipt; the reuse
    # battery receipt also stores assembly-1's scale cases, so the
    # domain-match assertion runs against the primary receipt while the
    # record-layer coverage law (claims <= measured over ALL cited
    # receipts) stays in piece_record.validate
    scales_s, _ = pr.measured_domain([pr.EVID_ROOT / CHAIN_RECEIPT])
    domain_match = (
        set(patch["physical_definition"]["valid_scales"]) == scales_p
        and set(law["physical_definition"]["valid_scales"]) == scales_law
        and set(star["physical_definition"]["valid_scales"]) == scales_s
        and set(star["physical_definition"]["valid_loads_N"]) <= loads_s
        and set(patch["physical_definition"]["valid_loads_N"]) <= loads_p)
    forged = copy.deepcopy(star)
    forged["physical_definition"]["valid_scales"] = [0.75, 1.0, 1.5, 2.0]
    reason = _refused(forged)
    ok = bool(not dangling and domain_match
              and reason == "piece_domain_unmeasured")
    return {"pass": ok,
            "measured": {"cited_receipts": len(set(cited)),
                          "dangling": dangling,
                          "patch_measured_scales": sorted(scales_p),
                          "star_measured_scales": sorted(scales_s),
                          "star_measured_loads_N": sorted(loads_s),
                          "over_gate_claim_refused_as": reason}}


# ── (c) ─────────────────────────────────────────────────────────────────────

@port_test(
    "c_work_accounting_quasistatic",
    "For one solved case (the k=2 star at scale 1.0) the PORT WORK along "
    "a quasistatic 9-point load ramp equals the STORED surface-energy "
    "change within the preregistered 1e-3 relative tolerance (measured "
    "1.99e-4). The solver's U = U_surface - f.x split makes the identity "
    "exact in the continuum; the residual is ramp discretization + the "
    "stagnation floor. Honest finding: the ramp's INTERMEDIATE states "
    "stagnate over the packet's unchanged 1e-6 gate.",
    "Port work and stored-energy change disagree beyond the "
    "preregistered tolerance, or the ramp fails to produce equilibria.")
def c_work_accounting() -> dict:
    star = cc.build_star(scale=1.0)
    seam, f0 = star["loads"][0]
    n_pts = ALLOWANCES["ramp_points"]
    lams = [k / (n_pts - 1) for k in range(n_pts)]
    x = np.asarray(star["positions"])
    xs, ss, ress = [], [], []
    for lam in lams:
        s = dict(star)
        s["loads"] = [(seam, tuple(v * lam for v in f0))]
        s["positions"] = x.copy()
        o = cc.solve_star(s)
        x = np.asarray(o["result"].positions)
        xs.append(x.copy())
        ss.append(o["result"].surface_energy)
        ress.append(o["result"].free_residual)
    W = sum(float(np.dot(np.asarray(f0), (xs[k + 1] - xs[k])[seam])
                  * (lams[k + 1] + lams[k]) / 2)
            for k in range(n_pts - 1))
    dS = ss[-1] - ss[0]
    rel = abs(W - dS) / abs(dS)
    mid_max = max(ress[1:-1])
    ok = bool(rel <= ALLOWANCES["work_accounting_rel_tol"]
              and ss[0] > 0 and W > 0)
    return {"pass": ok,
            "measured": {"W_ramp_J": round(W, 9), "dS_J": round(dS, 9),
                          "rel_diff": round(rel, 6),
                          "tolerance": ALLOWANCES["work_accounting_rel_tol"],
                          "max_mid_ramp_residual_N": round(mid_max, 9),
                          "ramp_finding": ALLOWANCES["ramp_finding"]}}


# ── (d) ─────────────────────────────────────────────────────────────────────

@port_test(
    "d_recipe_immutability_state_separation",
    "The star record's recipe hash matches a recomputation of its nodes+"
    "edges, and its TWO instances share that one immutable recipe while "
    "their state hashes differ (state separation); instantiating a THIRD "
    "instance from the same recipe gets the same recipe hash and a fresh "
    "state hash.",
    "The recipe hash does not match, two instances share a state hash, "
    "or a new instance silently rewrites the recipe.")
def d_recipe_immutability() -> dict:
    star = pr.load_record("assembly.star-k2")
    h = pr.recipe_hash(star["design_recipe"])
    hashes = [i["state_hash"] for i in star["instance_state"]["instances"]]
    separate = len(set(hashes)) == len(hashes) and len(hashes) >= 2
    third = pr.instantiate(star, "assembly.star-k2.instance-3",
                            {"applied_load_N": 0.4})
    ok = bool(h == star["design_recipe"]["recipe_hash"] and separate
              and third["state_hash"] not in hashes)
    return {"pass": ok,
            "measured": {"recipe_hash": h,
                          "instance_state_hashes_differ": separate,
                          "third_instance_state_hash":
                              third["state_hash"]}}


# ── (e) ─────────────────────────────────────────────────────────────────────

@port_test(
    "e_naming_grants_nothing",
    "Renaming grants no law: a copy of the star record renamed to "
    "'muscle' WITH a function_label claim but NO measured anchors and NO "
    "evidence ids is refused function_card_required. The retained "
    "records carry empty function labels and only measured anchors.",
    "A function claim without evidence is accepted, or the retained "
    "records claim an unmeasured function.")
def e_naming_grants_nothing() -> dict:
    star = pr.load_record("assembly.star-k2")
    no_label = all(not star["function_card"].get(k)
                   for k in pr._AFFORDANCE_KEYS)
    forged = copy.deepcopy(star)
    forged["name"] = "muscle"
    forged["function_card"]["function_label"] = "muscle"
    forged["function_card"]["measured_response_anchors"] = []
    forged["function_card"]["evidence_ids"] = []
    reason = _refused(forged)
    ok = bool(no_label and reason == "function_card_required")
    return {"pass": ok,
            "measured": {"retained_labels_empty": no_label,
                          "muscle_claim_refused_as": reason}}


# ── (f) ─────────────────────────────────────────────────────────────────────

@port_test(
    "f_failure_persistence",
    "A record cannot drop its lineage's failures: a copy of the star "
    "record with the rejected table/learned representation entries "
    "removed is refused representations_incomplete; the retained records "
    "carry both rejections WITH their receipts.",
    "A record without the rejected representations validates, or the "
    "retained rejections lost their receipts.")
def f_failure_persistence() -> dict:
    star = pr.load_record("assembly.star-k2")
    retained = {r["kind"]: r["status"] for r in star["representations"]}
    has_both = all(retained.get(k) == "rejected_at_gate"
                   for k in pr.REJECTED_REPRESENTATION_KINDS)
    forged = copy.deepcopy(star)
    forged["representations"] = [r for r in star["representations"]
                                  if r["kind"] == "direct-reference"]
    reason = _refused(forged)
    ok = bool(has_both and reason == "representations_incomplete")
    return {"pass": ok,
            "measured": {"retained_rejections": {k: retained.get(k)
                             for k in pr.REJECTED_REPRESENTATION_KINDS},
                          "dropped_failure_refused_as": reason}}


expect(EXPECTED_CHECKS)


# ── runner ──────────────────────────────────────────────────────────────────

ORDER = ["a_record_completeness", "b_evidence_links_and_domain_match",
         "c_work_accounting_quasistatic",
         "d_recipe_immutability_state_separation",
         "e_naming_grants_nothing", "f_failure_persistence"]


def main(argv: list) -> int:
    from evidence_output import (EVIDENCE_REFUSAL_EXIT, EvidencePathExists,
                                 resolve_evidence_path)
    try:
        out_path = resolve_evidence_path(EVID_DIR, "piece_record_checks",
                                         argv)
    except EvidencePathExists as ex:
        print(f"REFUSAL: {ex}")
        print("Nothing was computed or written; historical evidence intact.")
        return EVIDENCE_REFUSAL_EXIT

    from port_registry import TESTS
    results, failed = {}, 0
    print("=" * 100)
    print("  PIECE LIBRARY (11.20.1 record layer over the qualified "
          "alphabet): falsifier battery")
    print(f"  allowances (preregistered): work-accounting rel tol "
          f"{ALLOWANCES['work_accounting_rel_tol']}; ramp points "
          f"{ALLOWANCES['ramp_points']}; balance law = packet")
    print("=" * 100)
    for name in ORDER:
        rec = TESTS[name]
        print(f"\n[{name}]\n  STATEMENT : {rec['statement'][:96]}...")
        print(f"  FALSIFIER : {rec['falsifier'][:96]}...")
        try:
            r = rec["fn"]()
            results[name] = r
            verdict = "PASS" if r.get("pass") else "FAIL"
            if not r.get("pass"):
                failed += 1
            print(f"  -> {verdict}   "
                  f"{json.dumps(r.get('measured', {}), default=str)[:400]}")
        except Exception as ex:            # a crash is a FAIL, never a skip
            failed += 1
            results[name] = {"pass": False,
                             "error": f"{type(ex).__name__}: {ex}"}
            print(f"  -> FAIL (exception) {type(ex).__name__}: {ex}")

    print("\n" + "-" * 100)
    print(f"  {len(ORDER) - failed}/{len(ORDER)} checks PASS. Laws are "
          f"preregistered in piece_record.py + ALLOWANCES; none widened "
          f"after seeing results.")

    receipt = {
        "schema": "chimera-mechanism-factory-piece-record-checks-v1",
        "utc": datetime.now(timezone.utc).isoformat(),
        "what": "11.20 first increment: the qualified alphabet (fan "
                "patch, apex-weld seam law, k=2 star) as piece-library "
                "records with measured domains, retained failures, "
                "quasistatic work accounting and immutable shared "
                "recipes with per-instance state",
        "source_commit": cp._source_commit(),
        "source_file_hashes": {
            rel: cp._sha256_file(cp._REPO / rel) for rel in cp.HASHED_SOURCES
        },
        "packet_sha256": cp._sha256_bytes(PACKET.read_bytes()),
        "units": UNITS,
        "preregistered_allowances": ALLOWANCES,
        "checks": {n: {"pass": bool(results[n].get("pass"))} for n in ORDER},
        "cases": {n: results[n] for n in ORDER},
        "record_ids": ["piece.patch-equilibrium", "law.apex-weld-seam",
                        "assembly.star-k2"],
        "law_revision": LAW_REV,
        "domain_bounds": {
            "piece.patch-equilibrium": {"valid_loads_N": [0.4, 0.8, 1.2,
                                                            1.6, 2.0],
                                         "valid_scales": [0.5, 0.75, 1.0,
                                                           2.0]},
            "law.apex-weld-seam": {"valid_scales": [0.5, 0.75, 1.0, 2.0],
                                    "permitted_ops": ["apex-weld"]},
            "assembly.star-k2": {"valid_loads_N": [0.8],
                                  "valid_scales": [0.75, 1.0]},
        },
        "scope_note": "the packet's 1e-6 law is quoted, never widened; "
                      "no engine binding is claimed",
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(receipt, indent=1, default=str) + "\n",
                        encoding="utf-8")
    print(f"  receipt: {out_path}")
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except cp.EvidencePathExists as exc:
        print(f"REFUSED: {exc}")
        raise SystemExit(2)
