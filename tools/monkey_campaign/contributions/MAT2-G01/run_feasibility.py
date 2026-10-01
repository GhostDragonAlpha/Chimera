"""MAT2-G01 support/grip feasibility derivation (records/offline, CPU-only).

Preregistered derivation form (PREREGISTRATION.md, frozen at commit 023fd05f):
- C19 static support case analysis at the demonstrated F03 press operating
  point; per-reading verdicts under the frozen vocabulary.
- Moment templates with the named absent variables; arithmetic disclosure
  rows only.
- Reach carried as the named absent variable x_reach (no transform composed);
  in-hand span and the recorded-configuration wrap comparison derived.
- C20 potential-energy line only; dynamic transfer inputs named absent.
- Named-variable law: no synthetic constant may occupy an absent slot.

Modes:
  main     verify pins -> extract declared quantities -> derive -> write
           feasibility_receipt.json (canonical LF JSON)
  rerun    same, writing feasibility_receipt_rerun2.json
  compare  byte-identity of the two receipts (X2 determinism)
  falsify  the four preregistered bite arms (clean controls FIRST) ->
           falsifier_receipt.json

Every refusal is a named code; no wall-clock enters any receipt.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import math
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent

SCHEMA = "chimera.g01.feasibility.v1"
CARD = "MAT2-G01"
TASK_SHORT = "G01"
ATTEMPT_ID = "682fec627d7a413cb0fff77388436868"
AGENT_ID = "wk-g01-feasibility"
CRITERIA_SHA256 = "c79a569f7259084e948d60058ccd850ccb671af30e61062c59295d152b9f0374"
SCOPE_SHA256 = "cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097"
DEFINITION_RAW_SHA256 = "57ded6eb2f2cc6aa914d6f68c8efb55b215790fc7a9d0baa5dfd2c49fd1465c1"
PREREG_SHA256 = "155809ae3afbc97da58f70a4a65bd0c40d9718ccf75d46cdaa6357499abb418d"
BASE_COMMIT = "ced164735e5c2ff0a9662b04e7ffa28fd081f160"
PREREG_COMMIT = "023fd05f"
COMPOSED_AGAINST = "CARD_STARTER v3"

# ---------------------------------------------------------------------------
# Input pins (PREREGISTRATION.md section 5). Repo pins extract at the pinned
# base commit; host pins read from disk. Every sha256 is re-verified here.
# ---------------------------------------------------------------------------
REPO_PINS = [
    ("a09_grasp_package", "tools/monkey_campaign/contributions/MAT2-A09/grasp_package.json",
     "0a70adb1029d860ac9504683d77c2e94be2634724c63479f827fcbc8fcd97d24"),
    ("f03_checks", "tools/monkey_campaign/contributions/MAT2-F03/evidence/checks.json",
     "0f5463c618e55a3453e109010ff7a8b33d316f69bfdf207caea6d338cbeeeb71"),
    ("f03_trunk_mesh", "tools/monkey_campaign/contributions/MAT2-F03/assets/trunk_01_mesh.json",
     "3b17441764714c5e5e9c7a43c3253b3271a0f508954095e1960a57820cef6ee7"),
    ("w04_freeze_manifest", "tools/monkey_campaign/contributions/MAT2-W04/w04_freeze_manifest.json",
     "be632ffc85865515285f3d622a09882a3180a43101027914f1ed3408496f5d29"),
    ("d_massreg_register", "tools/monkey_campaign/contributions/MAT2-D-MASSREG/mass_register.json",
     "61fb79b1bf2df8c5e1a5b1bff2ab1c4f41700de25bc7f1a114cbc78fe693cc7a"),
    ("holodeck_catalog", "docs/roadmap/holodeck_tasks.json",
     "d9bb441939c0f07ccdbc0e4295353dc08ddb717f3b557f3e23639884d93f5a74"),
    ("monkey_completion_map", "tools/monkey_campaign/monkey_completion_map.json",
     "3efbfb141299d7cad63724431f7e5269febe15eee68d812b80d91de324385b84"),
]
HOST_PINS = [
    ("grasp_benchmark", "E:/ChimeraWork/research-data/20260929/benchmark-grasp/GRASP_BENCHMARK.md",
     "d936cebe38b1416dfc417db727ea81396eb8eb9217efed3f05b344db17f71610"),
    ("port_qualification", "E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-B07/numerical/PORT_QUALIFICATION.md",
     "4818d4b03576f2821f75f49b2d54f8c01378763b1ad1441075dda267c9ff3f00"),
    ("repin_study", "E:/ChimeraWork/monkey-coordination/re-pin/REPIN_STUDY.md",
     "99cde4758566784b5b98ad45db19f50beba2c81d8b1761428af19e32290c318b"),
    ("w03_report", "E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-W03/source/REPORT.md",
     "6692f07fc5314210c854884d1c17d7a8e561b1c9fa131c02131e3611198d64fa"),
    ("c17_stiffness_sources", "E:/ChimeraWork/monkey-coordination/c17-stiffness/STIFFNESS_SOURCES.md",
     "309b1788fa35aefe4f0cd822300ba926b30648ec8a021460dfb7f06ffe30ff0e"),
]

CATALOG_IDS = ["CTRL-03", "CTRL-04", "BIO-02", "CON-03", "CON-04", "DYN-02"]
CALC_IDS = ["C19", "C20"]

VACUOUS_LOG: list[str] = []


def refuse(code: str, detail: str) -> None:
    raise SystemExit(f"Refusal {code}: {detail}")


def refuse_vacuous_comparison(a, b, code: str) -> None:
    """House standard G5/P5: refuse relative-window comparisons that cannot
    discriminate (identical operands or non-numeric operands)."""
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        VACUOUS_LOG.append(f"{code}:non_numeric")
        refuse("vacuous_comparison_refused", f"{code}: non-numeric operand")
    if a == b:
        VACUOUS_LOG.append(f"{code}:identical_operands")
        refuse("vacuous_comparison_refused", f"{code}: identical operands {a!r}")


def canonical(obj) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def git_blob(commit: str, path: str) -> bytes:
    out = subprocess.run(["git", "cat-file", "blob", f"{commit}:{path}"],
                         cwd=str(HERE), capture_output=True)
    if out.returncode != 0:
        refuse("input_pin_missing", f"git blob {commit}:{path}")
    return out.stdout


def verify_pins() -> dict:
    pins = []
    blobs = {}
    for role, path, expect in REPO_PINS:
        b = git_blob(BASE_COMMIT, path)
        got = sha256_bytes(b)
        if got != expect:
            refuse("input_pin_drift", f"{role} {path}: {got} != {expect}")
        pins.append({"role": role, "kind": "repo", "path": path,
                     "at_commit": BASE_COMMIT, "sha256": got, "verified": True})
        blobs[role] = b
    for role, path, expect in HOST_PINS:
        p = pathlib.Path(path)
        if not p.exists():
            refuse("input_pin_missing", f"{role} {path}")
        b = p.read_bytes()
        got = sha256_bytes(b)
        if got != expect:
            refuse("input_pin_drift", f"{role} {path}: {got} != {expect}")
        pins.append({"role": role, "kind": "host", "path": path,
                     "sha256": got, "verified": True})
        blobs[role] = b
    return {"pins": pins, "blobs": blobs}


def jload(b: bytes):
    return json.loads(b.decode("utf-8"))


# ---------------------------------------------------------------------------
# Declared quantities extracted from the pins (nothing else is consumed)
# ---------------------------------------------------------------------------
def extract(blobs: dict) -> dict:
    q: dict = {}

    a09 = jload(blobs["a09_grasp_package"])
    endpoints = a09["interface_graph"]["grasp_endpoints"]
    if len(endpoints) != 6:
        refuse("count_mismatch", f"grasp_endpoints {len(endpoints)} != 6")
    for e in endpoints:
        if e.get("terminal_resolution", {}).get("state") != "supported" and \
           e.get("role") != "grasp_palm_reference":
            refuse("unavailable_body_reading", f"endpoint {e['endpoint_id']} unsupported")
    tips = [e for e in endpoints if e["role"] == "grasp_contact_endpoint"]
    if len(tips) != 5:
        refuse("count_mismatch", f"fingertip endpoints {len(tips)} != 5")
    q["grasp_endpoints"] = [
        {"endpoint_id": e["endpoint_id"], "role": e["role"],
         "owner_body": e["owner_body"], "position_m": e["position_m"],
         "frame_decl": e["frame_decl"]}
        for e in endpoints
    ]
    q["frame_law_verbatim"] = a09["frame_chain"]["law"]
    c = a09["counts"]
    q["a07_counts"] = {
        "envelope_measured_outside": c["a07_envelope_measured_outside"],
        "outside_insertions": c["a07_outside_insertions"],
        "outside_waypoints": c["a07_outside_waypoints"],
        "pending_assembly_mapping": c["a07_pending_assembly_mapping"],
        "pending_and_outside": c["a07_pending_and_outside"],
        "attachment_resolutions": c["a07_attachment_resolutions"],
        "grasp_endpoint_resolutions": c["a07_endpoint_resolutions"],
        "a08_actuator_rows": c["a08_actuator_rows"],
        "a08_unresolved_entries": c["a08_unresolved_entries"],
        "tissue_grasp_relevant": c["tissue_grasp_relevant"],
    }
    q["a09_consumer_row_verbatim"] = a09["consumer_contract"][0]
    gap_u1 = None
    for g in a09["explicit_gaps"]["gaps"]:
        if g.get("entry", {}).get("id") == "U1" or g.get("gap_id") == "A08-U1":
            gap_u1 = g
    if gap_u1 is None:
        refuse("input_pin_missing", "A08-U1 explicit gap row")
    q["a08_u1_verbatim"] = gap_u1["entry"].get("missing_evidence", gap_u1)
    # forearm-correspondence absence quote (A07 carried detail)
    q["forearm_absence_verbatim"] = a09["interface_graph"]["waypoint_resolutions_carried"][0][
        "missing_evidence"]["detail"]
    c05 = [x for x in a09["calculation_contracts"] if x["id"] == "C05"][0]
    q["c05_required_inputs"] = c05["required_inputs_catalog"]

    f03 = jload(blobs["f03_checks"])
    s1 = f03["P5_m06_contact_binding"]["experiments"]["S1_grip_stick"]
    q["s1"] = {k: s1[k] for k in ("jn_Ns", "mu_used", "grip_capacity_kg", "mode",
                                  "surface_b", "facet_centroid_m06", "facet_normal_m06",
                                  "ledger_max_abs_residual")}
    q["trunk_mass_kg"] = f03["P3_mass_provenance"]["mass_kg"]
    q["trunk_mass_band_kg"] = f03["P3_mass_provenance"]["mass_band_kg"]
    q["trunk_density_kg_m3"] = f03["P3_mass_provenance"]["density_kg_m3"]
    q["trunk_density_band_kg_m3"] = f03["P3_mass_provenance"]["band_kg_m3"]
    q["trunk_analytic_volume_m3"] = f03["P2_volume"]["analytic_solid_volume_m3"]
    q["trunk_vertex_radial_gap_m"] = f03["P6_correspondence"]["numeric"]["max_lateral_vertex_radial_gap_m"]
    p4 = f03["P4_material_documents"]
    q["trunk_reaction_state_verbatim"] = str(p4["bonds"]) + "; " + str(p4["passive_law"])

    mesh = jload(blobs["f03_trunk_mesh"])
    verts = mesh["vertices_f01_world_y_up"]
    xs = [p[0] for p in verts]
    ys = [p[1] for p in verts]
    zs = [p[2] for p in verts]
    ax = (min(xs) + max(xs)) / 2
    az = (min(zs) + max(zs)) / 2
    q["mesh"] = {
        "vertex_count": len(verts),
        "x_lo": min(xs), "x_hi": max(xs),
        "y_lo": min(ys), "y_hi": max(ys),
        "z_lo": min(zs), "z_hi": max(zs),
        "max_vertex_radial_from_bounds_midpoint_m":
            max(math.hypot(p[0] - ax, p[2] - az) for p in verts),
        "frame": "f01_world_y_up",
        "m06_transform_verbatim": mesh["frame_transform_to_m06"]["map"],
    }

    w04 = jload(blobs["w04_freeze_manifest"])
    act = w04["actuation_interface"]
    q["scene_caps_verbatim"] = act["certified_scene_caps_never_transfer"][0]
    q["scene_caps_status"] = act["status"]
    q["body_digest"] = w04["body_domain"]["bound_value"]["body_digest"]
    q["body_qualification_state"] = w04["body_domain"]["bound_value"]["qualification_state"]
    port = w04["port_active_law_inputs"]
    q["ports_qualified"] = port["ports_qualified"]
    q["ports_total"] = port["ports_total"]
    q["port_refusals"] = [
        {"identity": r["identity"], "quote": r["quote"],
         "sha256": r["evidence"]["sha256"]}
        for r in port["refusals"]
    ]
    q["r_mass_03_verbatim"] = [m["text"] for m in w04["body_domain"]["mass_rulings"]
                               if m["ruling"] == "R-MASS-03"][0]

    reg = jload(blobs["d_massreg_register"])
    tot = reg["totals"]
    q["scene_carve_kg"] = tot["scene_carve_sum_kg"]["value"]
    q["scene_carve_literal"] = tot["scene_carve_sum_kg"]["literal"]
    if tot["scene_carve_sum_kg"]["reproduced_bit_exact"] is not True:
        refuse("register_total_mismatch", "scene carve not bit-exact in the sealed register")
    q["reference_band_kg"] = tot["reference_band_kg"]
    tq = [e for e in reg["entries"] if e["contributor_id"].startswith("reference.turnquist")]
    if len(tq) != 3:
        refuse("count_mismatch", f"turnquist rows {len(tq)} != 3")
    q["turnquist_rows"] = [
        {"contributor_id": e["contributor_id"], "system": e["system"],
         "source_kind": e["source_kind"], "value_kg": e["value_kg"]}
        for e in tq
    ]
    q["massreg_reconciliation_verbatim"] = reg["specimen_classification"]["reconciliation_claim"]

    bench = blobs["grasp_benchmark"].decode("utf-8")
    m = re.search(r"g = 9\.80665", bench)
    if not m:
        refuse("input_pin_missing", "g = 9.80665 pin in GRASP_BENCHMARK")
    q["g_std"] = 9.80665
    m = re.search(r"g = 9\.81", bench)
    if not m:
        refuse("input_pin_missing", "g = 9.81 (record-g) in GRASP_BENCHMARK")
    q["g_record"] = 9.81
    m = re.search(r"dt = 0\.005 s", bench)
    if not m:
        refuse("input_pin_missing", "dt = 0.005 s in GRASP_BENCHMARK")
    q["dt_s"] = 0.005
    m = re.search(r"3\.6697247706422016 kg x 9\.80665 m/s\^2 = 35\.98770642201834 N", bench)
    q["benchmark_conversion_found"] = bool(m)
    q["benchmark_conversion_N"] = 35.98770642201834
    m = re.search(r"0\.130-1\.641", bench)
    q["measured_bw_envelope"] = "0.130-1.641" if m else None

    pq = blobs["port_qualification"].decode("utf-8")
    m = re.search(r"ports 8; ports_mechanically_qualified 0; ports_remaining_blocked 8;\s*"
                  r"waypoints_refused 24\.", pq)
    q["port_counts_verbatim_found"] = bool(m)
    q["waypoint_refusal_code"] = "waypoint_not_a_port"
    m = re.search(r"24/24 refuse", pq)
    q["waypoint_refusal_24_of_24_found"] = bool(m)

    repin = blobs["repin_study"].decode("utf-8")
    q["gap9_verbatim"] = ("Duty factor and contact channels MISSING from the sealed walk "
                          "trace") in repin
    q["grip_anchor_formula_verbatim"] = ("capacity kg = mu_s x jn / (g x dt)") in repin

    w03 = blobs["w03_report"].decode("utf-8")
    q["w03_mass_corroboration_kg_literal"] = "10.037998000000004"
    q["w03_weight_corroboration_N_literal"] = "98.43913308670002"
    q["w03_corroboration_found"] = ("10.037998000000004" in w03) and \
                                   ("98.43913308670002" in w03)

    c17 = blobs["c17_stiffness_sources"].decode("utf-8")
    q["c17_no_measured_pin_verbatim"] = ("no lawful measured pin exists for ANY of the five "
                                         "C17 input quantities") in c17
    q["x_share_absence_verbatim"] = "Per-port load share is UNPINNED (no partition source)." in c17

    completion = jload(blobs["monkey_completion_map"])
    for cid in CALC_IDS:
        found = []

        def walk(o):
            if isinstance(o, dict):
                if o.get("id") == cid and "title" in o:
                    found.append(o)
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)

        walk(completion)
        if not found:
            refuse("input_pin_missing", f"calculation row {cid}")
        q[f"calc_{cid}"] = {k: found[0].get(k) for k in
                            ("id", "title", "required_inputs", "calculation_or_contract",
                             "output", "verification", "catalog_refs", "result_status")}
    return q


# ---------------------------------------------------------------------------
# The frozen derivation (PREREGISTRATION.md section 7)
# ---------------------------------------------------------------------------
READINGS = [
    ("scene", "scene system (register scene carve literal)"),
    ("band_lo", "biological-reference system, Turnquist band low"),
    ("band_mid", "biological-reference system, Turnquist band midpoint"),
    ("band_hi", "biological-reference system, Turnquist band high"),
]
CHANNEL_CASES = [1, 2, 3]


def derive(q: dict) -> dict:
    d: dict = {}

    # geometry from the pinned mesh + sealed analytic volume
    mesh = q["mesh"]
    width_x = mesh["x_hi"] - mesh["x_lo"]
    width_z = mesh["z_hi"] - mesh["z_lo"]
    height = mesh["y_hi"] - mesh["y_lo"]
    vol = q["trunk_analytic_volume_m3"]
    r_vol = math.sqrt(vol / (math.pi * height))
    if r_vol != 0.037:
        refuse("verdict_tamper_detected",
               f"derived declared radius {r_vol!r} does not reproduce 0.037")
    ax = (mesh["x_lo"] + mesh["x_hi"]) / 2
    az = (mesh["z_lo"] + mesh["z_hi"]) / 2
    d["geometry"] = {
        "declared_radius_m": r_vol,
        "declared_diameter_m": 2 * r_vol,
        "height_m": height,
        "mesh_width_x_m": width_x,
        "mesh_width_z_m": width_z,
        "mesh_max_vertex_radial_from_bounds_midpoint_m":
            mesh["max_vertex_radial_from_bounds_midpoint_m"],
        "sealed_vertex_radial_gap_m": q["trunk_vertex_radial_gap_m"],
        "volume_consistency": vol == math.pi * r_vol * r_vol * height,
    }

    # capacity at the demonstrated operating point
    mu = q["s1"]["mu_used"]
    jn = q["s1"]["jn_Ns"]
    dt = q["dt_s"]
    cap_kg = q["s1"]["grip_capacity_kg"]
    formula_kg = mu * jn / (q["g_record"] * dt)
    if formula_kg != cap_kg:
        refuse("verdict_tamper_detected",
               f"capacity bit-reproduction failed: {formula_kg!r} != {cap_kg!r}")
    n0 = jn / dt
    c0_record = mu * n0
    c0_std = cap_kg * q["g_std"]
    d["capacity"] = {
        "mu_s": mu,
        "jn_Ns": jn,
        "dt_s": dt,
        "press_operating_point_N": n0,
        "capacity_kg": cap_kg,
        "capacity_formula_bit_reproduced": True,
        "capacity_N_record_g": c0_record,
        "capacity_N_std_g": c0_std,
        "benchmark_conversion_match": c0_std == q["benchmark_conversion_N"],
        "sensitivity_law": "capacity is linear in mu and in N (Coulomb limit)",
        "understated_mu_row_kg": 0.9174311926605504,
        "understated_mu_value": 0.15,
    }

    # body-weight readings (two DISTINCT systems; never averaged)
    g = q["g_std"]
    weights = {}
    weights["scene"] = {
        "mass_kg": q["scene_carve_kg"],
        "literal": q["scene_carve_literal"],
        "system": "scene",
        "W_N": q["scene_carve_kg"] * g,
    }
    band = q["reference_band_kg"]
    weights["band_lo"] = {"mass_kg": band["low"], "system": "biological-reference",
                          "W_N": band["low"] * g}
    weights["band_mid"] = {"mass_kg": band["midpoint"], "system": "biological-reference",
                           "W_N": band["midpoint"] * g}
    weights["band_hi"] = {"mass_kg": band["high"], "system": "biological-reference",
                          "W_N": band["high"] * g}
    d["body_readings"] = weights
    d["w03_corroboration"] = {
        "found": q["w03_corroboration_found"],
        "mass_literal": q["w03_mass_corroboration_kg_literal"],
        "weight_literal": q["w03_weight_corroboration_N_literal"],
        "note": "W03 seating scan builder-order mass 10.037998000000004 kg; the register "
                "carve literal 10.037998 is the sealed scene reading consumed here",
    }

    # C19 case analysis (equal-share case model; x_share is a named variable)
    rows = []
    for name, label in READINGS:
        W = weights[name]["W_N"]
        for n in CHANNEL_CASES:
            support = n * c0_std
            refuse_vacuous_comparison(support, W, f"friction_{name}_n{n}")
            friction_feasible = support >= W
            n_req = W / (n * mu)
            refuse_vacuous_comparison(n0, n_req, f"press_{name}_n{n}")
            press_ok = n_req <= n0
            rows.append({
                "reading": name,
                "reading_label": label,
                "n_channels": n,
                "W_N": W,
                "support_N": support,
                "friction_feasible": friction_feasible,
                "required_press_per_channel_N": n_req,
                "press_at_operating_point": press_ok,
            })
    d["case_table"] = rows

    # recorded-configuration in-hand geometry (arithmetic in the hand frame only)
    tips = [e for e in q["grasp_endpoints"] if e["role"] == "grasp_contact_endpoint"]
    best_span = 0.0
    best_pair = None
    for a, b in itertools.combinations(tips, 2):
        dist = math.dist(a["position_m"], b["position_m"])
        if dist > best_span:
            best_span = dist
            best_pair = (a["endpoint_id"], b["endpoint_id"])
    diameter = d["geometry"]["declared_diameter_m"]
    refuse_vacuous_comparison(best_span, diameter, "wrap_span_vs_diameter")
    d["wrap_comparison"] = {
        "recorded_fingertip_span_m": best_span,
        "span_pair": list(best_pair),
        "declared_trunk_diameter_m": diameter,
        "recorded_configuration_wraps": best_span >= diameter,
        "margin_m": best_span - diameter,
        "scope": "recorded configuration only; achievable aperture is x_aperture",
    }

    # moment disclosures (templates only; x_com and x_trunk_strength absent)
    facet_h = q["s1"]["facet_centroid_m06"][2]
    d["moment_disclosures"] = {
        "s1_facet_height_m": facet_h,
        "root_moment_template_N_m": {
            name: weights[name]["W_N"] * facet_h for name, _ in READINGS
        },
        "hold_moment_template_at_com_probe_N_m": {
            name: {
                "x_com_0": weights[name]["W_N"] * 0.0,
                "x_com_half_span": weights[name]["W_N"] * (best_span / 2.0),
            } for name, _ in READINGS
        },
        "demonstrated_case_external_moment": "zero (S1 static stick, S3 rest; rooted trunk)",
    }

    # C20 potential-energy line (dynamic inputs absent)
    d["pe_line"] = {
        name: {
            "per_meter_J": weights[name]["W_N"] * 1.0,
            "at_facet_height_J": weights[name]["W_N"] * facet_h,
            "full_trunk_J": weights[name]["W_N"] * height,
        } for name, _ in READINGS
    }

    # named variables (absent interface quantities; NO numeric value allowed)
    d["named_variables"] = {
        "x_reach": {
            "quantity": "hand-to-trunk placement transform T_hand_trunk",
            "status": "ABSENT",
            "provenance_verbatim": q["frame_law_verbatim"],
            "also": q["forearm_absence_verbatim"],
            "pins": ["a09_grasp_package"],
        },
        "x_press": {
            "quantity": "measured grip-force actuator bound behind the normal press",
            "status": "ABSENT",
            "provenance_verbatim": q["a08_u1_verbatim"],
            "also": "ports 0/8 qualified; 24/24 waypoints refuse waypoint_not_a_port",
            "pins": ["a09_grasp_package", "port_qualification"],
        },
        "x_com": {
            "quantity": "grasp-posture centre-of-mass offset from the grip axis",
            "status": "ABSENT",
            "provenance_verbatim": "the 9 unresolved bodies hand_l, hand_r, talus_l, "
                                   "talus_r, thorax, toes_l, toes_r, ulna, ulna_l carry "
                                   "ZERO transported mass",
            "pins": ["port_qualification"],
        },
        "x_trunk_strength": {
            "quantity": "measured trunk/root structural strength bound",
            "status": "ABSENT",
            "provenance_verbatim": q["trunk_reaction_state_verbatim"],
            "pins": ["f03_checks"],
        },
        "x_share": {
            "quantity": "per-port load share (contact force partition)",
            "status": "ABSENT",
            "provenance_verbatim": "Per-port load share is UNPINNED (no partition source).",
            "pins": ["c17_stiffness_sources"],
        },
        "x_aperture": {
            "quantity": "achievable grasp aperture (joint limits, C05 inputs)",
            "status": "ABSENT",
            "provenance_verbatim": q["c05_required_inputs"],
            "pins": ["a09_grasp_package"],
        },
        "x_sequence": {
            "quantity": "support sequence for vertical transfer",
            "status": "ABSENT",
            "provenance_verbatim": q["calc_C20"]["required_inputs"],
            "pins": ["monkey_completion_map"],
        },
        "x_inertia": {
            "quantity": "adopted-assembly body inertia in a grasp posture",
            "status": "ABSENT",
            "provenance_verbatim": q["body_qualification_state"],
            "pins": ["w04_freeze_manifest"],
        },
        "x_trajectory": {
            "quantity": "transfer trajectory",
            "status": "ABSENT",
            "provenance_verbatim": q["body_qualification_state"],
            "pins": ["w04_freeze_manifest"],
        },
        "x_losses": {
            "quantity": "transfer losses (dynamic balance)",
            "status": "ABSENT",
            "provenance_verbatim": "Duty factor and contact channels MISSING from the sealed "
                                   "walk trace",
            "pins": ["repin_study"],
        },
    }

    # verdicts under the frozen vocabulary (WITHIN | OUTSIDE | CONDITIONAL |
    # UNDECIDABLE-IN-RECORDS only)
    case = {(r["reading"], r["n_channels"]): r for r in rows}
    single = all(not case[(name, 1)]["friction_feasible"] for name, _ in READINGS)
    wrap = d["wrap_comparison"]

    per_case = []
    for name, label in READINGS:
        for n in CHANNEL_CASES:
            row = case[(name, n)]
            per_case.append({
                "clause": f"C19 case {name} n={n} ({label})",
                "verdict": "WITHIN" if row["friction_feasible"] else "OUTSIDE",
                "basis": "n * c0_std >= W at the standard-g capacity"
                if row["friction_feasible"] else "n * c0_std < W at the standard-g capacity",
                "numbers": {
                    "support_N": row["support_N"],
                    "W_N": row["W_N"],
                    "required_press_per_channel_N": row["required_press_per_channel_N"],
                    "press_at_operating_point": row["press_at_operating_point"],
                },
                "citations": ["f03_checks", "d_massreg_register", "grasp_benchmark"],
            })

    verdicts = [
        {
            "clause": "single-channel static support (all readings)",
            "verdict": "OUTSIDE" if single else "WITHIN",
            "basis": "n=1 support < W at EVERY lawful body reading",
            "numbers": {
                "capacity_N_std_g": c0_std,
                "min_W_N": min(weights[name]["W_N"] for name, _ in READINGS),
            },
            "citations": ["f03_checks", "d_massreg_register", "grasp_benchmark"],
        },
        {
            "clause": "press at the demonstrated operating point (summary)",
            "verdict": "CONDITIONAL",
            "basis": "required press per channel <= 60 N holds for band at n>=2 and scene "
                     "at n=3 only (per-case numbers in the case table); the operating point "
                     "is a fixture input, never an actuator qualification (x_press ABSENT)",
            "numbers": {
                "press_operating_point_N": n0,
                "scene_n3_required_press_N": case[("scene", 3)]["required_press_per_channel_N"],
                "band_hi_n2_required_press_N": case[("band_hi", 2)]["required_press_per_channel_N"],
                "scene_n2_required_press_N": case[("scene", 2)]["required_press_per_channel_N"],
            },
            "named_variables": ["x_press"],
            "citations": ["f03_checks", "grasp_benchmark", "d_massreg_register"],
        },
        {
            "clause": "actuator-bounds qualification (any case)",
            "verdict": "CONDITIONAL",
            "basis": "x_press is ABSENT: no measured grip-force actuator bound exists; the "
                     "39 sealed osim Fmax are declared carriers with force_runtime_ready "
                     "false; the scene caps never transfer (TC-3)",
            "named_variables": ["x_press"],
            "citations": ["a09_grasp_package", "w04_freeze_manifest", "port_qualification"],
        },
        {
            "clause": "reachable contacts (trunk-relative reach)",
            "verdict": "UNDECIDABLE-IN-RECORDS",
            "basis": "x_reach is ABSENT by law: no hand-to-trunk transform is composed; no "
                     "runtime scene co-instantiates trunk and creature",
            "named_variables": ["x_reach"],
            "citations": ["a09_grasp_package", "w04_freeze_manifest", "f03_checks"],
        },
        {
            "clause": "recorded-configuration wrap of the declared trunk",
            "verdict": "OUTSIDE" if not wrap["recorded_configuration_wraps"] else "WITHIN",
            "basis": "recorded fingertip span vs declared trunk diameter "
                     "(recorded configuration only; x_aperture absent)",
            "numbers": {
                "recorded_fingertip_span_m": wrap["recorded_fingertip_span_m"],
                "declared_trunk_diameter_m": wrap["declared_trunk_diameter_m"],
                "margin_m": wrap["margin_m"],
            },
            "named_variables": ["x_aperture"],
            "citations": ["a09_grasp_package", "f03_trunk_mesh", "f03_checks"],
        },
        {
            "clause": "moment support beyond the zero-moment demonstrated cases",
            "verdict": "CONDITIONAL",
            "basis": "x_com and x_trunk_strength ABSENT; templates recorded as disclosures",
            "named_variables": ["x_com", "x_trunk_strength", "x_share"],
            "citations": ["port_qualification", "f03_checks"],
        },
        {
            "clause": "C20 vertical transfer (dynamic ascent)",
            "verdict": "UNDECIDABLE-IN-RECORDS",
            "basis": "x_sequence, x_inertia, x_trajectory, x_losses ABSENT; static "
                     "support is necessary, not proof of climbing",
            "named_variables": ["x_sequence", "x_inertia", "x_trajectory", "x_losses"],
            "citations": ["repin_study", "w04_freeze_manifest", "monkey_completion_map"],
        },
    ]
    verdicts = per_case + verdicts
    d["verdicts"] = verdicts
    d["overall"] = {
        "verdict": "OUTSIDE-CONDITIONAL",
        "statement": "Required force/moment support is NOT established within reachable "
                     "contacts and actuator bounds for the declared trunk. Definitive from "
                     "records: single-channel support OUTSIDE at every lawful body reading; "
                     "recorded-configuration wrap OUTSIDE (span 0.0567 m < declared diameter "
                     "0.0740 m). Multi-channel friction arithmetic is feasible at the "
                     "demonstrated press operating point (band at n>=2; scene at n=3) but no "
                     "case is actuator-qualified (x_press ABSENT) and trunk-relative reach is "
                     "undecidable in records (x_reach ABSENT). Honest card outcome; nothing "
                     "is tuned.",
    }
    d["claim_class"] = "Static support is necessary, not proof of climbing (card observation)."
    return d


def build_receipt() -> dict:
    pins = verify_pins()
    q = extract(pins["blobs"])
    d = derive(q)
    catalog = jload(pins["blobs"]["holodeck_catalog"])
    cat_rows = {}
    for cid in CATALOG_IDS:
        found = [r for r in catalog["tasks"] if r.get("id") == cid]
        if not found:
            refuse("input_pin_missing", f"catalog row {cid}")
        r = found[0]
        cat_rows[cid] = {k: r.get(k) for k in ("id", "title", "domain", "kind", "status",
                                               "statement", "prediction", "falsifier")}
    calc_rows = {"C19": q["calc_C19"], "C20": q["calc_C20"]}

    receipt = {
        "schema": SCHEMA,
        "card": CARD,
        "task_id_short": TASK_SHORT,
        "attempt_id": ATTEMPT_ID,
        "agent_id": AGENT_ID,
        "criteria_sha256": CRITERIA_SHA256,
        "scope_sha256": SCOPE_SHA256,
        "definition_raw_sha256": DEFINITION_RAW_SHA256,
        "composed_against": COMPOSED_AGAINST,
        "base_commit": BASE_COMMIT,
        "preregistration_commit": PREREG_COMMIT,
        "preregistration_sha256": PREREG_SHA256,
        "done_when_verbatim": "Required force/moment support lies within reachable contacts "
                              "and actuator bounds for the declared trunk",
        "card_observation_verbatim": "Static support is necessary, not proof of climbing",
        "card_falsifier_verbatim": "Missing identities or a claimed pass unsupported by "
                                   "records fails; a screenshot is not a substitute.",
        "input_pins": pins["pins"],
        "calculations": calc_rows,
        "catalog": cat_rows,
        "declared_quantities": q,
        "derivation": d,
        "vacuous_guard_log": VACUOUS_LOG,
        "named_variable_law": "no synthetic constant may occupy an absent slot; declared "
                              "never qualifies, synthetic never transfers",
        "refusals": [],
        "determinism": "canonical LF JSON; two-run byte identity asserted by mode compare",
    }
    return receipt


def write_receipt(path: pathlib.Path) -> None:
    receipt = build_receipt()
    path.write_bytes(canonical(receipt))
    print(f"wrote {path.name} sha256 {sha256_bytes(canonical(receipt))}")


# ---------------------------------------------------------------------------
# Falsifier arms (clean control FIRST; tampered copies in scratch, never here)
# ---------------------------------------------------------------------------
def _load_receipt() -> dict:
    return json.loads((HERE / "feasibility_receipt.json").read_text(encoding="utf-8"))


def _check_verdict_consistency(r: dict) -> list[str]:
    """Recompute the verdict rows from the receipt's own case table."""
    problems = []
    d = r["derivation"]
    rows = {(row["reading"], row["n_channels"]): row for row in d["case_table"]}
    by_clause = {v["clause"]: v for v in d["verdicts"]}
    single = all(not rows[(name, 1)]["friction_feasible"]
                 for name in ("scene", "band_lo", "band_mid", "band_hi"))
    summary_clause = "single-channel static support (all readings)"
    if by_clause[summary_clause]["verdict"] != ("OUTSIDE" if single else "WITHIN"):
        problems.append(f"verdict_row_disagrees:{summary_clause}")
    for row in rows.values():
        recompute = row["support_N"] >= row["W_N"]
        if recompute != row["friction_feasible"]:
            problems.append(f"case_row_disagrees:{row['reading']}:{row['n_channels']}")
        if abs(row["support_N"] - row["n_channels"] * d["capacity"]["capacity_N_std_g"]) > 0.0:
            problems.append(f"support_scale_disagrees:{row['reading']}:{row['n_channels']}")
        clause = f"C19 case {row['reading']} n={row['n_channels']} ({row['reading_label']})"
        want = "WITHIN" if row["friction_feasible"] else "OUTSIDE"
        got = by_clause.get(clause, {}).get("verdict")
        if got != want:
            problems.append(f"per_case_verdict_disagrees:{clause}:{got}!={want}")
    wrap = d["wrap_comparison"]
    wrap_clause = "recorded-configuration wrap of the declared trunk"
    want = "OUTSIDE" if not wrap["recorded_configuration_wraps"] else "WITHIN"
    if by_clause[wrap_clause]["verdict"] != want:
        problems.append(f"verdict_row_disagrees:{wrap_clause}")
    return problems


def _check_named_variables(r: dict) -> list[str]:
    problems = []
    for name, var in r["derivation"]["named_variables"].items():
        if var.get("status") != "ABSENT":
            problems.append(f"absent_slot_marker_missing:{name}")
        for key, value in var.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                problems.append(f"synthetic_constant_in_absent_slot:{name}:{key}")
        if not var.get("provenance_verbatim"):
            problems.append(f"absence_provenance_missing:{name}")
    return problems


def _check_source_reproduction(r: dict) -> list[str]:
    problems = []
    cap = r["derivation"]["capacity"]
    if cap["capacity_kg"] != r["declared_quantities"]["s1"]["grip_capacity_kg"]:
        problems.append("capacity_not_bit_copied")
    if r["derivation"]["body_readings"]["scene"]["mass_kg"] != \
            r["declared_quantities"]["scene_carve_kg"]:
        problems.append("scene_mass_not_bit_copied")
    return problems


def _check_claim_tracing(r: dict) -> list[str]:
    problems = []
    known = {p["role"] for p in r["input_pins"]}
    for v in r["derivation"]["verdicts"]:
        if not v.get("citations"):
            problems.append(f"claim_without_record:{v['clause']}")
            continue
        for cite in v["citations"]:
            if cite not in known:
                problems.append(f"claim_citation_unknown:{v['clause']}:{cite}")
    return problems


def falsify() -> dict:
    receipt = _load_receipt()
    arms = []
    plans = [
        ("g01_fb1_verdict_tamper_bites", "g01_fb1_premature",
         "flip the single-channel verdict row OUTSIDE->WITHIN",
         _check_verdict_consistency),
        ("g01_fb2_synthetic_constant_bites", "g01_fb2_premature",
         "fill the absent slot x_reach with a synthetic numeric constant",
         _check_named_variables),
        ("g01_fb3_source_drift_bites", "g01_fb3_premature",
         "perturb the declared grip capacity in the receipt copy",
         _check_source_reproduction),
        ("g01_fb4_claim_without_record_bites", "g01_fb4_premature",
         "strip the citations from one verdict row",
         _check_claim_tracing),
    ]
    for arm, guard, mutation, detector in plans:
        clean = detector(receipt)
        clean_green = len(clean) == 0
        if not clean_green:
            refuse(guard, f"clean control not green: {clean}")
        tampered = json.loads(json.dumps(receipt))
        if arm.startswith("g01_fb1"):
            for v in tampered["derivation"]["verdicts"]:
                if v["clause"].startswith("single-channel static support"):
                    v["verdict"] = "WITHIN"
        elif arm.startswith("g01_fb2"):
            tampered["derivation"]["named_variables"]["x_reach"]["value"] = 0.5
        elif arm.startswith("g01_fb3"):
            tampered["derivation"]["capacity"]["capacity_kg"] = 30.0
        elif arm.startswith("g01_fb4"):
            tampered["derivation"]["verdicts"][0]["citations"] = []
        problems = detector(tampered)
        arms.append({
            "arm": arm,
            "guard": guard,
            "clean_control": {"green": clean_green, "problems": clean},
            "mutation": mutation,
            "caught": len(problems) > 0,
            "observed": problems,
        })
    receipt_out = {
        "schema": "chimera.g01.falsifier.v1",
        "card": CARD,
        "attempt_id": ATTEMPT_ID,
        "criteria_sha256": CRITERIA_SHA256,
        "arms": arms,
        "all_caught": all(a["caught"] for a in arms),
        "clean_controls_all_green": all(a["clean_control"]["green"] for a in arms),
    }
    out = HERE / "falsifier_receipt.json"
    out.write_bytes(canonical(receipt_out))
    print(f"wrote falsifier_receipt.json sha256 {sha256_bytes(canonical(receipt_out))}")
    if not receipt_out["all_caught"]:
        refuse("verdict_tamper_detected", "a falsifier arm did not bite")
    return receipt_out


def main(argv: list[str]) -> int:
    mode = argv[1] if len(argv) > 1 else "main"
    if mode == "main":
        write_receipt(HERE / "feasibility_receipt.json")
    elif mode == "rerun":
        write_receipt(HERE / "feasibility_receipt_rerun2.json")
    elif mode == "compare":
        a = (HERE / "feasibility_receipt.json").read_bytes()
        b = (HERE / "feasibility_receipt_rerun2.json").read_bytes()
        if a != b:
            refuse("determinism_x2_broken", "rerun receipt is not byte-identical")
        print(f"X2 byte-identical: {sha256_bytes(a)}")
    elif mode == "falsify":
        falsify()
    else:
        refuse("usage", f"unknown mode {mode}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
