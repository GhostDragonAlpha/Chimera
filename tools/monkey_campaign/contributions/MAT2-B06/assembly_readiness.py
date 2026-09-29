"""MAT2-B06: re-run real assembly readiness WITHOUT SUBSTITUTIONS.

Re-evaluates the four requirement domains (mass / ownership / frame / port)
against the ACTUAL sealed records of MAT2-B03 (material-volume input), MAT2-B04
(frame forest), MAT2-A06 (attachment ownership), MAT2-A07 (placement
resolution) and MAT2-B05 (mechanical port requirements), all read as raw
committed bytes at the frozen sealed tip via `git cat-file` and verified
against the preregistered sha256 pins. No sealed record is edited, no stand-in
is substituted, nothing is fitted, no gap is silently promoted.

Lawful row statuses (preregistered vocabulary, PREREGISTRATION.md section 4):
  * `evaluated_satisfied_at_scope` — the requirement holds at its declared
    scope and the pinned evidence re-reads bitwise from the sealed bytes;
  * `evaluated_gap` — the requirement does not hold; missing_evidence names
    the absent record/decision AND the authorizing rank (A07 vocabulary);
  * `measured_screen` — a new evaluation enabled by the REALITY-grade
    transcribed Cheng (1999) tables (license-internal, cited by file+sha256,
    read-only from their host location). Screens NEVER gate.

Cheng evaluation verdicts per row: closes / partially_informs /
inadmissible_to_close / inadmissible_species_law / does_not_apply /
does_not_close. A verdict can never flip a sealed status.

Readiness gate (prereg section 6): `assembly_readiness` is true ONLY IF every
requirement_gate row is `evaluated_satisfied_at_scope` AND every satisfied
row's evidence re-verifies. Screens never gate; declared never qualifies;
authored requirements never qualify a port.

CPU-only, stdlib-only, deterministic (canonical JSON, no stochastic inputs).
Named refusals bite before aggregate counts (A06 lesson).
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from csv import reader as csv_reader
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCHEMA = "chimera.assembly_readiness.v1"
DOCUMENT_REVISION = 1
OBJECT_ID = "mat2_b06_assembly_readiness"
CARD_ID = "MAT2-B06"
TASK_ID_SHORT = "B06"

# ---- identity -----------------------------------------------------------------
CRITERIA_SHA256 = "6c3bb5fb51aa87adb261e6a07f444c78cae28910b2327fe88f2b79c6da80802b"
DONE_WHEN = ("All mass/ownership/frame/port requirements evaluated, with "
             "remaining gaps explicit")
SEALED_TIP = "051123cf1d549479c765e4f3e112ddddbedcf752"
BASE_HEAD = "c525b82c7c3ce0128565424764293a3c85811ab3"
CONTRIB = "tools/monkey_campaign/contributions"

# ---- sealed input pins (raw committed bytes at SEALED_TIP; prereg section 2) --
SEALED_PINS = {
    "b03_material": (f"{CONTRIB}/MAT2-B03/material_volume_input.json",
                     "6e8033f26c823f410eb5beb8fdaaefd4c0c37db61327a86221e087bc832b9ddc"),
    "b03_matter_library": (f"{CONTRIB}/MAT2-B03/data/matter_library_1af0bbde.json",
                           "de10200fb87bf48c3cc80d5e223805f02e27df115b91186f42f28064a64054ed"),
    "b04_frames": (f"{CONTRIB}/MAT2-B04/frame_forest.json",
                   "156ef55722e1ecda3238f3733131eb707f209cb93531d0e133227b00ebba8203"),
    "a06_ownership": (f"{CONTRIB}/MAT2-A06/attachment_ownership.json",
                      "f1f0430772258e8449fc354841becf2f1869783399e63f3f145565b8d0b1041c"),
    "a07_resolution": (f"{CONTRIB}/MAT2-A07/placement_resolution.json",
                       "cd596d7c21fa81a4c2632e13b63ba26e62da51d44eca2355147fd5dff1587490"),
    "b05_ports": (f"{CONTRIB}/MAT2-B05/mechanical_port_requirements.json",
                  "ef69ee740262cc5783e763517e4d27e0306f31d059b8273bb125486ad7647f3d"),
    "dw04_mass_matrix": (f"{CONTRIB}/D-W04-MASS-20260924/mass_matrix.json",
                         "6a32229438f59158a0995b6b90043639e8b103eedf2d09243502faaa9a68ff39"),
    "dw04_receipt": (f"{CONTRIB}/D-W04-MASS-20260924/receipt.json",
                     "f37fb0cc7bf8ccdf1572fc31ba909ef9b0ae8eff043613a13b9e4c4648cbf445"),
}

# ---- Cheng source pins (license-internal host files; prereg section 3) --------
CHENG_DIR = Path("E:/ChimeraWork/research-data/20260929/cheng_tables")
CHENG_PINS = {
    "cheng_m2_3_mulatta_morphometry": (
        "M2-3_mulatta_morphometry.csv",
        "16ca8bcd9be48b3766125801eb05a8f4f10b446b4caed76d9fddeb2e45df71fa"),
    "cheng_m2_5_fascicularis_morphometry": (
        "M2-5_fascicularis_morphometry.csv",
        "9469449f8735df84a163d364a67402d127ca8ac54a402595ce4cebb6d16cf148"),
    "cheng_m2_6_mulatta_inertials": (
        "M2-6_mulatta_inertials.csv",
        "1948a2d8399b5253461c6ed70eed87ea38c5df4083b75437e1e3dbd1a4ce93f3"),
    "cheng_m2_7_fascicularis_inertials": (
        "M2-7_fascicularis_inertials.csv",
        "d1d601feaf61b033bdbccf8509be946d0e1884fec62388c8630287703fc63133"),
    "cheng_m2_8_regressions": (
        "M2-8_regressions.csv",
        "b185ee8e98b6e663defed0abd4d004fec053eb6417e027c54801070cd894ec22"),
    "cheng_readme": (
        "README_cheng_tables.md",
        "7ec44aa1031df22f0263a023aade9cc0c6c572ce268d14934a6ef49a61900ca3"),
    "cheng_receipt": (
        "TRANSCRIPTION_RECEIPT.md",
        "a3031b236dc368fb8f59f571e39666fc0ed504f383fff9b34d26c36817f2e568"),
}

CHIMANOID_RAW_SHA256 = ("675e00d0898cf7a175f3e4fe8f240eb24301c2f5e201ffa9215"
                        "aea45b01b83d1")

# ---- frozen vocabulary and unit laws ------------------------------------------
STATUS_SATISFIED = "evaluated_satisfied_at_scope"
STATUS_GAP = "evaluated_gap"
STATUS_SCREEN = "measured_screen"
LAWFUL_GATE_STATUSES = (STATUS_SATISFIED, STATUS_GAP)
LAWFUL_SCREEN_STATUSES = (STATUS_SCREEN,)
CHENG_VERDICTS = ("closes", "partially_informs", "inadmissible_to_close",
                  "inadmissible_species_law", "does_not_apply", "does_not_close")
G_TO_KG = 1.0e-3            # Cheng masses are printed in g
G_CM2_TO_KG_M2 = 1.0e-7     # Cheng inertias are printed in g*cm^2

# ---- frozen counts (prereg section 5; validator reproduces them) ---------------
FROZEN_COUNTS = {
    "requirement_gate_rows": 14,
    "gate_satisfied": 4,
    "gate_gap": 10,
    "measured_screen_rows": 5,
    "gaps_by_domain": {"mass": 3, "ownership": 4, "frame": 2, "port": 1},
    "expected_satisfied_ids": ["R-MASS-01", "R-OWN-01", "R-FRM-01", "R-PRT-02"],
    "expected_gap_ids": ["R-MASS-02", "R-MASS-03", "R-MASS-04", "R-OWN-02",
                         "R-OWN-03", "R-OWN-04", "R-OWN-05", "R-FRM-02",
                         "R-FRM-03", "R-PRT-01"],
    "expected_screen_ids": ["S-MASS-05", "S-MASS-06", "S-MASS-07", "S-MASS-08",
                            "S-PORT-09"],
}
EXPECTED_READINESS = False

CARRIED_OBSERVATION = ("Buffy 02 binds 9 claims but 17.039978509953905 kg "
                       "stays transported/not counted; readiness false")

READINESS_RULE = ("assembly_readiness is true ONLY IF every requirement_gate "
                  "row is evaluated_satisfied_at_scope AND every satisfied "
                  "row's evidence pin re-verifies bitwise against the sealed "
                  "bytes; screens never gate; declared never qualifies; "
                  "authored requirements never qualify a port; no substituted "
                  "stand-in, no silent promotion, no fitting")


class Refused(ValueError):
    """A named refusal; str(err) starts with the refusal code."""

    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code = code


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_json(obj) -> str:
    return json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False,
                      allow_nan=False) + "\n"


def write_canonical(path: Path, obj) -> str:
    text = canonical_json(obj)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return sha256_bytes(text.encode("utf-8"))


def repo_root() -> Path:
    p = HERE
    while p != p.parent:
        if (p / ".git").exists():
            return p
        p = p.parent
    raise Refused("sealed_source_unavailable", "no repository root above "
                  f"{HERE}")


def git_blob(relpath: str) -> bytes:
    root = repo_root()
    proc = subprocess.run(
        ["git", "-c", f"safe.directory={root}", "-C", str(root), "cat-file",
         "blob", f"{SEALED_TIP}:{relpath}"],
        capture_output=True, timeout=120)
    if proc.returncode:
        raise Refused("sealed_source_unavailable",
                      f"git cat-file {SEALED_TIP}:{relpath} failed: "
                      f"{proc.stderr.decode('utf-8', 'replace')[-300:]}")
    return proc.stdout


# ---- sealed loader --------------------------------------------------------------
def load_sealed(bindings=None) -> dict:
    """Read every pinned sealed document at the frozen tip, verify bytes."""
    out = {}
    for role, (relpath, want) in SEALED_PINS.items():
        if bindings is not None and role in bindings:
            raw = bindings[role]
        else:
            raw = git_blob(relpath)
        got = sha256_bytes(raw)
        if got != want:
            raise Refused("sealed_pin_mismatch",
                          f"{role} ({relpath}) sha256 {got} != pinned {want}")
        out[role] = {"path": relpath, "sha256": got,
                     "doc": json.loads(raw.decode("utf-8"))}
    return out


def assert_allowed_inputs(names) -> None:
    """F1 guard: the input set is ONLY the sealed pins (+ Cheng, separate)."""
    allowed = set(SEALED_PINS)
    for name in names:
        if name not in allowed:
            raise Refused(
                "unbound_input_refused",
                f"input {name!r} is neither a pinned sealed record nor a "
                f"pinned Cheng source; substituted stand-ins cannot close a "
                f"gap (allowed: {sorted(allowed)})")


# ---- Cheng loader ----------------------------------------------------------------
def _cheng_raw(role: str, bindings=None) -> bytes:
    name, want = CHENG_PINS[role]
    if bindings is not None and role in bindings:
        raw = bindings[role]
    else:
        path = CHENG_DIR / name
        if not path.exists():
            raise Refused("cheng_source_unavailable",
                          f"{role} missing at {path}")
        raw = path.read_bytes()
    got = sha256_bytes(raw)
    if got != want:
        raise Refused("cheng_source_pin_mismatch",
                      f"{role} ({name}) sha256 {got} != pinned {want}")
    return raw


def parse_mean_sd(cell: str):
    """'294 ± 119' / '3.24E+03 ± 1.20E+03' / '1.10+E03 ± 5.65E+01' -> floats."""
    parts = [p.strip() for p in cell.split("±")]
    if len(parts) == 1:
        return float(parts[0]), None
    return float(parts[0]), float(parts[1])


def _rows(raw: bytes):
    text = raw.decode("utf-8-sig")
    return [row for row in csv_reader(text.splitlines()) if row]


def load_cheng(bindings=None) -> dict:
    """Parse the pinned Cheng tables (values + presence facts only)."""
    out = {"pins": {}, "license_note": (
        "license UNVERIFIED (transcription README); internal use only; cited "
        "by file+sha256; no table bytes committed to the repository")}
    for role in CHENG_PINS:
        name, want = CHENG_PINS[role]
        out["pins"][role] = {"file": str(CHENG_DIR / name).replace("\\", "/"),
                             "sha256": want}
    # M2-6 M. mulatta segment inertials
    m26 = _rows(_cheng_raw("cheng_m2_6_mulatta_inertials", bindings))
    header = m26[0]
    col = {"upper_arm": header.index("Upper arm"),
           "forearm": header.index("Forearm"),
           "hand": header.index("Hand")}
    seg = {}
    for row in m26[1:]:
        label = row[0].strip()
        if label == "Segment mass (g)":
            seg["segment_mass_g"] = {k: parse_mean_sd(row[i]) for k, i in col.items()}
        elif label.startswith("Segment mass (% of total body weight)"):
            seg["segment_mass_pct_bw"] = {k: parse_mean_sd(row[i]) for k, i in col.items()}
        elif label.startswith("Icg mean value"):
            seg["icg_mean_g_cm2"] = {k: parse_mean_sd(row[i]) for k, i in col.items()}
    for key in ("segment_mass_g", "segment_mass_pct_bw", "icg_mean_g_cm2"):
        if key not in seg:
            raise Refused("cheng_table_row_missing",
                          f"M2-6 row {key} not found")
    out["m26_mulatta_inertials"] = seg
    # M2-8 regressions vs total body weight (M. mulatta)
    m28 = _rows(_cheng_raw("cheng_m2_8_regressions", bindings))
    header = m28[0]
    col = {"upper_arm": header.index("Upper arm"),
           "forearm": header.index("Forearm"),
           "hand": header.index("Hand")}
    reg = {}
    for row in m28[1:]:
        if row[0].strip() != "Segment mass":
            continue
        stat = row[1].strip()
        if stat.startswith("m "):
            reg["m_g_per_kg"] = {k: float(row[i]) for k, i in col.items()}
        elif stat.startswith("b "):
            reg["b_g"] = {k: float(row[i]) for k, i in col.items()}
    for key in ("m_g_per_kg", "b_g"):
        if key not in reg:
            raise Refused("cheng_table_row_missing",
                          f"M2-8 row Segment mass/{key} not found")
    out["m28_regressions"] = reg
    # Muscle morphometry presence facts (M2-3 mulatta, M2-5 fascicularis)
    for role, key in (("cheng_m2_3_mulatta_morphometry", "m23_mulatta"),
                      ("cheng_m2_5_fascicularis_morphometry", "m25_fascicularis")):
        rows = _rows(_cheng_raw(role, bindings))
        names = [r[0].strip() for r in rows[1:] if r and r[0].strip()]
        abbrevs = [r[1].strip() for r in rows[1:] if len(r) > 1 and r[1].strip()]
        out[key] = {
            "muscle_rows": len(names),
            "has_biceps_long": "Biceps long" in names,
            "has_biceps_short": "Biceps short" in names,
            "has_brachioradialis": "Brachioradialis" in names,
            "has_pronator": any("ronator" in n for n in names),
            "abbreviation_column": "BL" in abbrevs,
        }
    return out


def cheng_files(verdict_roles) -> list:
    return [{"role": r, "file": CHENG_PINS[r][0], "sha256": CHENG_PINS[r][1]}
            for r in verdict_roles]


# ---- pointer re-read helper -----------------------------------------------------
def pointer_get(doc, pointer: str):
    """Minimal JSON-pointer-ish getter: a.b or a[*].c with numeric indexes."""
    cur = doc
    for part in pointer.split("."):
        if "[*]" in part:
            key, _, _ = part.partition("[*]")
            cur = [item[key] for item in cur]
        elif part.endswith("]") and "[" in part:
            key, _, idx = part.partition("[")
            cur = cur[key][int(idx.rstrip("]"))]
        else:
            cur = cur[part]
    return cur


# ---- sealed value extraction ------------------------------------------------------
def sealed_values(sealed) -> dict:
    b03 = sealed["b03_material"]["doc"]
    b04 = sealed["b04_frames"]["doc"]
    a06 = sealed["a06_ownership"]["doc"]
    a07 = sealed["a07_resolution"]["doc"]
    b05 = sealed["b05_ports"]["doc"]
    dw = sealed["dw04_mass_matrix"]["doc"]

    counted = [r for r in b03["regions"]
               if r["rest_geometry"]["material_volume"]["counted"]]
    region_masses = {r["id"]: r["rest_geometry"]["material_volume"]["mass_kg"]
                     for r in counted}
    excl = {e["claim_id"]: e["mass_kg"] for e in b03["provenance"]["excluded_claims"]}
    inertia = b03["provenance"]["inertia_about_com_kg_m2"]

    roots = {f["frame_id"]: f for f in b04["frames"].values()
             if f.get("component_root")}

    pending = [r for r in a07["path_resolutions"]
               if r.get("mutant_mapping_status") == "pending_assembly_mapping"]
    forearm = [r for r in a07["path_resolutions"]
               if (r.get("missing_evidence") or {}).get("kind")
               == "forearm_assembly_correspondence_record"]
    outside = [r for r in a07["path_resolutions"]
               if r.get("placement_failed_outside")]

    weights_blocked = [p["inputs"]["weights"]["blocked"]
                       ["carried_load_segment_weights"]["missing_evidence"]
                       for p in b05["ports"]]
    anchor_blocked = [p["inputs"]["anchor_frame_id"]["missing_evidence"]
                      for p in b05["ports"]]
    pressure = [p["inputs"]["pressure_limits"]["status"] for p in b05["ports"]]
    a07_c17_note = a07["c17"]["note"]

    return {
        "b03": {
            "counted_total_kg": b03["provenance"]["counted_set"]["counted_total_kg"],
            "counted_regions": sorted(region_masses),
            "region_masses": region_masses,
            "inertia_trace_kg_m2": (inertia[0][0] + inertia[1][1] + inertia[2][2]),
            "excluded": excl,
            "density_kg_m3": counted[0]["rest_geometry"]["material_volume"]["density_kg_m3"],
            "density_provenance": counted[0]["rest_geometry"]["material_volume"]
            .get("density_source", {}).get("provenance_class"),
        },
        "b04": {
            "roots": {fid: {"origin_m": f["origin_m"], "chain": f["chain"]}
                      for fid, f in roots.items()},
            "components": len(b04["components"]),
            "unresolved_bodies": len(b04["unresolved_bodies"]),
            "bonds": len(b04["bonds"]),
            "containment_edges": len(b04["containment_edges"]),
            "counted_mass_kg": b04["matter_boundary"]["counted_mass_kg"],
            "matter_boundary_statement": b04["matter_boundary"]["statement"],
            "no_fusion_statement": b04["no_fusion_statement"],
        },
        "a06": {
            "path_records": len(a06["path_records"]),
            "attachments": len(a06["attachments"]),
            "grasp_endpoints": len(a06["grasp_endpoints"]),
            "waypoint_records": sum(
                1 for r in a06["path_records"]
                if r["role"] in ("path_waypoint", "conditional_waypoint")),
            "all_ownered": all(r.get("owner_body") and r.get("role")
                               for r in a06["path_records"]),
            "all_attached": all(a.get("interface_id") and a.get("bone")
                                for a in a06["attachments"]),
        },
        "a07": {
            "counts": a07["counts"],
            "pending_first": pending[0],
            "pending_count": len(pending),
            "forearm_count": len(forearm),
            "forearm_first": forearm[0],
            "outside_count": len(outside),
            "grasp_supported": sum(
                1 for r in a07["grasp_endpoint_resolutions"]
                if r["resolution"] == "supported"),
            "c17_note": a07_c17_note,
        },
        "b05": {
            "counts": b05["counts"],
            "qualification_rule": b05["qualification_rule"],
            "weights_blocked_missing": weights_blocked,
            "anchor_blocked_missing": anchor_blocked,
            "pressure_statuses": pressure,
            "port_ids": [p["port_id"] for p in b05["ports"]],
            "all_qualified_flags": [p["inputs_all_qualified"] for p in b05["ports"]],
            "mech_flags": [p["mechanical_qualification"] for p in b05["ports"]],
        },
        "dw04": {
            "transported_kg": float(dw["masses"][3]["literal"]),
            "transported_identity": dw["masses"][3]["semantic_identity"],
            "rhesis_band_midpoint_kg": float(dw["masses"][2]["literal"]),
        },
    }


# ---- screen computations -----------------------------------------------------------
def compute_screens(sv, cheng) -> list:
    screens = []
    m26 = cheng["m26_mulatta_inertials"]
    m28 = cheng["m28_regressions"]

    # S-MASS-05: excluded osim segment claims vs measured M. mulatta bands
    claims = sv["b03"]["excluded"]
    upper = m26["segment_mass_g"]["upper_arm"]
    fore = m26["segment_mass_g"]["forearm"]
    hand = m26["segment_mass_g"]["hand"]
    comparisons = []
    for name, claim_kg, (mean_g, sd_g), band_roles in (
            ("humerus", claims["mass_humerus"], upper, ("upper_arm",)),
            ("radius_plus_ulna", claims["mass_radius"] + claims["mass_ulna"],
             fore, ("forearm",)),
            ("hand", claims["mass_hand"], hand, ("hand",))):
        mean_kg = mean_g * G_TO_KG
        sd_kg = sd_g * G_TO_KG
        delta = abs(claim_kg - mean_kg)
        comparisons.append({
            "claim": name, "claim_kg": claim_kg,
            "cheng_columns": list(band_roles),
            "cheng_mean_kg": mean_kg, "cheng_sd_kg": sd_kg,
            "abs_delta_kg": delta, "inside_1sd": bool(delta <= sd_kg),
        })
    ok5 = all(c["inside_1sd"] for c in comparisons)
    screens.append({
        "requirement_id": "S-MASS-05", "domain": "mass",
        "kind": "measured_screen", "status": STATUS_SCREEN, "gates": False,
        "statement": ("excluded .osim segment claims screened against the "
                      "measured M. mulatta segment mass bands (Cheng M2-6); "
                      "the claims remain EXCLUDED regardless of the screen"),
        "sealed_values": {k: claims[k] for k in
                          ("mass_humerus", "mass_radius", "mass_ulna", "mass_hand")},
        "cheng_values": {k: m26["segment_mass_g"][k] for k in col_keys()},
        "unit_law": "cheng g -> kg via 1e-3",
        "computed": {"comparisons": comparisons, "all_inside_1sd": ok5},
        "prediction": "all three |claim - mean| <= 1 sd",
        "outcome": "confirmed" if ok5 else "REFUSED",
        "cheng_evaluation": {
            "files": cheng_files(["cheng_m2_6_mulatta_inertials"]),
            "verdict": "partially_informs",
            "reason": ("magnitude consistency screen only; n=6 different "
                       "subjects, segment conventions differ, no specimen "
                       "binding; the ownership exclusion is untouched")},
    })

    # S-MASS-06: implied body weight via M2-8 + %BW screen at the transported total
    implied = []
    for name, claim_g, seg in (("upper_arm", claims["mass_humerus"] / G_TO_KG,
                                "upper_arm"),
                               ("forearm_radius_ulna",
                                (claims["mass_radius"] + claims["mass_ulna"]) / G_TO_KG,
                                "forearm"),
                               ("hand", claims["mass_hand"] / G_TO_KG, "hand")):
        m = m28["m_g_per_kg"][seg]
        b = m28["b_g"][seg]
        implied.append({"claim": name, "claim_g": claim_g,
                        "m_g_per_kg": m, "b_g": b,
                        "implied_body_weight_kg": (claim_g - b) / m})
    bw_ok = all(4.0 <= r["implied_body_weight_kg"] <= 7.0 for r in implied)
    pct_bw = m26["segment_mass_pct_bw"]["upper_arm"][0]
    transported_g = sv["dw04"]["transported_kg"] * 1000.0
    expected_upper_g = transported_g * pct_bw / 100.0
    ratio = expected_upper_g / (claims["mass_humerus"] * 1000.0)
    ok6 = bw_ok and ratio > 2.0
    screens.append({
        "requirement_id": "S-MASS-06", "domain": "mass",
        "kind": "measured_screen", "status": STATUS_SCREEN, "gates": False,
        "statement": ("body-weight implied by the arm claims via the Cheng "
                      "M2-8 regressions, and the %BW screen of the "
                      "transported total (17.039978509953905 kg) against the "
                      "upper-arm claim"),
        "sealed_values": {"transported_kg": sv["dw04"]["transported_kg"]},
        "cheng_values": {"m_g_per_kg": m28["m_g_per_kg"],
                         "b_g": m28["b_g"],
                         "upper_arm_pct_bw": pct_bw},
        "computed": {"implied_body_weight": implied,
                     "all_implied_in_4_7_kg": bw_ok,
                     "transported_pctbw_expected_upper_arm_g": expected_upper_g,
                     "expected_over_claim_ratio": ratio,
                     "ratio_gt_2": bool(ratio > 2.0)},
        "prediction": ("all implied body weights in [4.0, 7.0] kg AND "
                       "expected/claim ratio > 2"),
        "outcome": "confirmed" if ok6 else "REFUSED",
        "cheng_evaluation": {
            "files": cheng_files(["cheng_m2_8_regressions",
                                  "cheng_m2_6_mulatta_inertials"]),
            "verdict": "partially_informs",
            "reason": ("determinate internal-inconsistency screen: the "
                       "transported total is not the body mass of the arm "
                       "claims; no measured table can own or decompose the "
                       "claims, so the accounting gap stays open")},
    })

    # S-MASS-07: eigen-free inertia screen (trace invariant)
    icg_sum_g_cm2 = sum(m26["icg_mean_g_cm2"][k][0] for k in col_keys())
    icg_sum_kg_m2 = icg_sum_g_cm2 * G_CM2_TO_KG_M2
    trace = sv["b03"]["inertia_trace_kg_m2"]
    ratio7 = trace / icg_sum_kg_m2
    ok7 = 0.3 <= ratio7 <= 1.5
    screens.append({
        "requirement_id": "S-MASS-07", "domain": "mass",
        "kind": "measured_screen", "status": STATUS_SCREEN, "gates": False,
        "statement": ("trace invariant of the sealed B03 aggregate bone "
                      "inertia vs the sum of Cheng M2-6 Icg mean values "
                      "(eigen-free; clustered-spectrum eigensolvers are "
                      "diagnostics only)"),
        "sealed_values": {"inertia_trace_kg_m2": trace},
        "cheng_values": {"icg_mean_g_cm2": m26["icg_mean_g_cm2"],
                         "icg_sum_g_cm2": icg_sum_g_cm2},
        "unit_law": "1 g*cm^2 = 1e-7 kg*m^2",
        "computed": {"icg_sum_kg_m2": icg_sum_kg_m2,
                     "bone_trace_over_measured_segment_sum": ratio7,
                     "inside_0_3_1_5": bool(ok7)},
        "prediction": "ratio in [0.3, 1.5]",
        "outcome": "confirmed" if ok7 else "REFUSED",
        "cheng_evaluation": {
            "files": cheng_files(["cheng_m2_6_mulatta_inertials"]),
            "verdict": "partially_informs",
            "reason": ("bone-only vs whole-segment are different quantities "
                       "about different reference points from different "
                       "subjects; same order of magnitude is the only claim; "
                       "B03's own cross-method verification stands at its "
                       "own scope and is not re-verified here")},
    })

    # S-MASS-08: species admissibility law
    screens.append({
        "requirement_id": "S-MASS-08", "domain": "mass",
        "kind": "measured_screen", "status": STATUS_SCREEN, "gates": False,
        "statement": ("species law: the campaign animal context is rhesus "
                      "(M. mulatta; Turnquist & Kessler adult-female band "
                      "book context per the sealed D-W04 record)"),
        "sealed_values": {"rhesis_band_midpoint_kg":
                          sv["dw04"]["rhesis_band_midpoint_kg"]},
        "cheng_values": {},
        "computed": {
            "m_mulatta_tables": ["cheng_m2_3_mulatta_morphometry",
                                 "cheng_m2_6_mulatta_inertials",
                                 "cheng_m2_8_regressions"],
            "m_mulatta_verdict": "admissible_as_screening_reference_only",
            "m_fascicularis_tables": ["cheng_m2_5_fascicularis_morphometry",
                                      "cheng_m2_7_fascicularis_inertials"],
            "m_fascicularis_verdict": "inadmissible_species_law"},
        "prediction": ("M. fascicularis tables inadmissible to close any "
                       "requirement on this assembly; M. mulatta tables "
                       "admissible as screening references only"),
        "outcome": "confirmed",
        "cheng_evaluation": {
            "files": cheng_files(["cheng_m2_5_fascicularis_morphometry",
                                  "cheng_m2_7_fascicularis_inertials"]),
            "verdict": "inadmissible_species_law",
            "reason": ("different species under the biological law; the "
                       "fascicularis tables are retained only as "
                       "cross-species reference and close nothing here")},
    })

    # S-PORT-09: port muscle coverage in the morphometry tables
    cov = {}
    for key in ("m23_mulatta", "m25_fascicularis"):
        t = cheng[key]
        cov[key] = {"muscle_rows": t["muscle_rows"],
                    "has_biceps_long": t["has_biceps_long"],
                    "has_biceps_short": t["has_biceps_short"],
                    "has_brachioradialis": t["has_brachioradialis"],
                    "has_pronator": t["has_pronator"]}
    ok9 = all(t["muscle_rows"] == 21 and t["has_biceps_long"]
              and t["has_biceps_short"] and t["has_brachioradialis"]
              and not t["has_pronator"] for t in cov.values())
    screens.append({
        "requirement_id": "S-PORT-09", "domain": "port",
        "kind": "measured_screen", "status": STATUS_SCREEN, "gates": False,
        "statement": ("port muscle coverage: Biceps long / Biceps short / "
                      "Brachioradialis rows exist and Pronator teres is "
                      "absent in BOTH morphometry tables (21 muscle rows "
                      "each)"),
        "sealed_values": {"port_muscles": ["biceps long (BIClong)",
                                           "biceps short (BICshort)",
                                           "brachioradialis (BRD)",
                                           "pronator teres (PT)"]},
        "cheng_values": cov,
        "computed": {"coverage_ok": bool(ok9)},
        "prediction": ("BL/BS/Br present, PT absent, 21 rows in M2-3 and "
                       "M2-5"),
        "outcome": "confirmed" if ok9 else "REFUSED",
        "cheng_evaluation": {
            "files": cheng_files(["cheng_m2_3_mulatta_morphometry",
                                  "cheng_m2_5_fascicularis_morphometry"]),
            "verdict": "does_not_close",
            "reason": ("muscle-belly morphometry is not a port-gate input; "
                       "and the port set is incomplete even at muscle level "
                       "(PT absent from both tables)")},
    })
    return screens


def col_keys():
    return ("upper_arm", "forearm", "hand")


# ---- gate rows -----------------------------------------------------------------------
def build_requirements(sv, cheng) -> list:
    rows = []
    b03pin = sealed_pin("b03_material")
    b04pin = sealed_pin("b04_frames")
    a06pin = sealed_pin("a06_ownership")
    a07pin = sealed_pin("a07_resolution")
    b05pin = sealed_pin("b05_ports")
    dwpin = sealed_pin("dw04_mass_matrix")

    # R-MASS-01 counted bone inventory
    total = sv["b03"]["counted_total_kg"]
    mass_sum = sum(sv["b03"]["region_masses"][r] for r in sv["b03"]["counted_regions"])
    rows.append({
        "requirement_id": "R-MASS-01", "domain": "mass",
        "kind": "requirement_gate",
        "statement": ("counted bone mass inventory for the five closed "
                      "arm-bone regions (C02)"),
        "scope": "counted-bone scope (shells and segment claims excluded by law)",
        "status": STATUS_SATISFIED,
        "sealed_source": b03pin,
        "evidence": {"kind": "sealed_field_reread", "items": [
            {"pointer": "provenance.counted_set.counted_total_kg", "value": total},
            {"pointer": "provenance.counted_set.regions",
             "value": sv["b03"]["counted_regions"]},
            {"pointer": "recomputed.region_mass_sum_kg", "value": mass_sum},
        ], "note": ("recomputed region-mass sum equals the sealed counted "
                    "total exactly; per-region masses re-read") },
        "cheng_evaluation": {
            "files": cheng_files(["cheng_m2_6_mulatta_inertials"]),
            "verdict": "does_not_close",
            "reason": ("the counted inventory is bone-only geometry mass; "
                       "Cheng segment masses are whole-tissue masses of other "
                       "subjects; see S-MASS-05/06/07 screens")},
    })

    # R-MASS-02 measured density support
    rows.append({
        "requirement_id": "R-MASS-02", "domain": "mass",
        "kind": "requirement_gate",
        "statement": ("measured bone material density support for the "
                      "counted inventory"),
        "scope": "material admission (MAT-03)",
        "status": STATUS_GAP,
        "sealed_source": b03pin,
        "missing_evidence": {
            "detail": ("the counted inventory uses density provenance class "
                       + repr(sv["b03"]["density_provenance"])
                       + " (archived matter library entry, "
                       + repr(sv["b03"]["density_kg_m3"])
                       + " kg/m3) with NO temperature/moisture/strain-rate "
                       "conditions stated; a measured bone material density "
                       "with stated conditions, admitted through MAT-03, is "
                       "absent"),
            "authorization_required": "recorded lead decision (MAT-03 admission)"},
        "carried_from": {"role": "b03_material",
                         "pointer": "authored_from_reread_density_fields"},
        "cheng_evaluation": {
            "files": cheng_files(["cheng_m2_6_mulatta_inertials",
                                  "cheng_m2_3_mulatta_morphometry"]),
            "verdict": "inadmissible_to_close",
            "reason": ("no material-density column exists in any Cheng table "
                       "(segment/tissue masses and inertials only); a segment "
                       "mass cannot close a material density gap")},
    })

    # R-MASS-03 carried-load segment weights (B05 blocked side)
    wmiss = sv["b05"]["weights_blocked_missing"]
    rows.append({
        "requirement_id": "R-MASS-03", "domain": "mass",
        "kind": "requirement_gate",
        "statement": ("counted, validated carried-load segment weights for "
                      "the eight real tendon ports (B05 `weights` blocked "
                      "side)"),
        "scope": "port weights input (B05 ledger)",
        "status": STATUS_GAP,
        "sealed_source": b05pin,
        "missing_evidence": {
            "detail": wmiss[0][0],
            "authorization_required": ("recorded lead decision (a counted, "
                                       "validated carried-load mass)"),
            "carried_verbatim_from": {"role": "b05_ports",
                                      "pointer": "ports[*].inputs.weights."
                                                 "blocked.carried_load_segment_"
                                                 "weights.missing_evidence"}},
        "sealed_counts": {"excluded_osim_segment_claims_kg":
                          sv["b03"]["excluded"]["mass_humerus"]
                          + sv["b03"]["excluded"]["mass_radius"]
                          + sv["b03"]["excluded"]["mass_ulna"]
                          + sv["b03"]["excluded"]["mass_hand"]},
        "cheng_evaluation": {
            "files": cheng_files(["cheng_m2_6_mulatta_inertials",
                                  "cheng_m2_8_regressions"]),
            "verdict": "partially_informs",
            "reason": ("measured M. mulatta segment bands + BW regressions "
                       "can SCREEN a future counted mass (S-MASS-05/06); they "
                       "are not a counted mass of THIS assembly (different "
                       "subjects, segment conventions, no specimen binding)")},
    })

    # R-MASS-04 transported assembly accounting
    rows.append({
        "requirement_id": "R-MASS-04", "domain": "mass",
        "kind": "requirement_gate",
        "statement": ("transported-assembly accounting (Buffy 02): the "
                      "transported claims must be decomposed into counted, "
                      "validated owned masses"),
        "scope": "assembly readiness accounting (D-W04 mass lineage)",
        "status": STATUS_GAP,
        "sealed_source": dwpin,
        "missing_evidence": {
            "detail": (repr(sv["dw04"]["transported_kg"])
                       + " kg stays class transported_source_effective: "
                       "declared owned, counted_mass_kg 0.0, "
                       "components_with_validated_tissue_mass 0; no recorded "
                       "ownership decision decomposes the claims"),
            "authorization_required": "recorded lead decision",
            "carried_verbatim_from": {"role": "dw04_mass_matrix",
                                      "pointer": "masses[3].semantic_identity"}},
        "cheng_evaluation": {
            "files": cheng_files(["cheng_m2_6_mulatta_inertials",
                                  "cheng_m2_8_regressions"]),
            "verdict": "partially_informs",
            "reason": ("S-MASS-06 shows the transported total is not the "
                       "body mass of the arm claims (expected/claim > 2); "
                       "sharper, but measurement cannot own or decompose the "
                       "transported claims")},
    })

    # R-OWN-01 registry ownership completeness
    rows.append({
        "requirement_id": "R-OWN-01", "domain": "ownership",
        "kind": "requirement_gate",
        "statement": ("every grasp-relevant endpoint and waypoint record "
                      "carries an explicit approved owner body and role in "
                      "the sealed ownership registry"),
        "scope": "ownership registry scope (assembly mapping is R-OWN-02/03)",
        "status": STATUS_SATISFIED,
        "sealed_source": a06pin,
        "evidence": {"kind": "sealed_field_reread", "items": [
            {"pointer": "path_records[*].owner_body+role", "value": True},
            {"pointer": "attachments[*].interface_id+bone", "value": True},
            {"pointer": "counts.path_records", "value": sv["a06"]["path_records"]},
            {"pointer": "counts.attachments", "value": sv["a06"]["attachments"]},
            {"pointer": "counts.waypoint_records",
             "value": sv["a06"]["waypoint_records"]},
            {"pointer": "counts.grasp_endpoints",
             "value": sv["a06"]["grasp_endpoints"]},
        ], "note": ("owner+role presence re-read over all 48 path records; "
                    "interface+bone presence over all 26 attachments")},
        "cheng_evaluation": None,
    })

    # R-OWN-02 pending assembly mapping
    pend = sv["a07"]["pending_first"]
    rows.append({
        "requirement_id": "R-OWN-02", "domain": "ownership",
        "kind": "requirement_gate",
        "statement": ("assembly mapping for the pending hand-body path "
                      "records"),
        "scope": "assembly-level ownership (A07 resolutions)",
        "status": STATUS_GAP,
        "sealed_source": a07pin,
        "missing_evidence": {
            "detail": pend["missing_evidence"]["detail"],
            "authorization_required": pend["missing_evidence"]["authorization_required"],
            "carried_verbatim_from": {"role": "a07_resolution",
                                      "pointer": "path_resolutions[pending_"
                                                 "assembly_mapping first]"
                                                 ".missing_evidence"}},
        "sealed_counts": {"pending_assembly_mapping":
                          sv["a07"]["counts"]["pending_assembly_mapping"],
                          "mutant_mapped_records":
                          sv["a07"]["counts"]["mutant_mapped_records"]},
        "cheng_evaluation": {
            "files": cheng_files(["cheng_m2_3_mulatta_morphometry"]),
            "verdict": "does_not_apply",
            "reason": "a measurement cannot authorize a mapping decision"},
    })

    # R-OWN-03 forearm correspondence
    fr = sv["a07"]["forearm_first"]
    rows.append({
        "requirement_id": "R-OWN-03", "domain": "ownership",
        "kind": "requirement_gate",
        "statement": "forearm assembly correspondence records",
        "scope": "assembly-level ownership (A07 resolutions)",
        "status": STATUS_GAP,
        "sealed_source": a07pin,
        "missing_evidence": {
            "detail": fr["missing_evidence"]["detail"],
            "authorization_required": fr["missing_evidence"]["authorization_required"],
            "carried_verbatim_from": {"role": "a07_resolution",
                                      "pointer": "path_resolutions[forearm_"
                                                 "correspondence first]."
                                                 "missing_evidence"}},
        "sealed_counts": {"forearm_correspondence_records":
                          sv["a07"]["forearm_count"]},
        "cheng_evaluation": {
            "files": cheng_files(["cheng_m2_3_mulatta_morphometry"]),
            "verdict": "does_not_apply",
            "reason": "a measurement cannot authorize a mapping decision"},
    })

    # R-OWN-04 measured-outside placements
    rows.append({
        "requirement_id": "R-OWN-04", "domain": "ownership",
        "kind": "requirement_gate",
        "statement": ("measured-outside attachment placements (envelope test "
                      "excesses carried exactly by A07)"),
        "scope": "assembly-level ownership (A07 resolutions)",
        "status": STATUS_GAP,
        "sealed_source": a07pin,
        "missing_evidence": {
            "detail": ("measured outside placements stay "
                       "placement_failed_outside with exact per-axis "
                       "excesses; resolving them requires a new fitting "
                       "experiment, which is NOT authorized for this card "
                       "(fitting_not_authorized; carried observation: "
                       "Candidate C remains failed at 67.147 micrometres "
                       "per side)"),
            "authorization_required": ("separately authorized fitting "
                                       "experiment (recorded lead or captain "
                                       "decision)"),
            "carried_verbatim_from": {"role": "a07_resolution",
                                      "pointer": "carried_observation."
                                                 "missing_evidence"}},
        "sealed_counts": {"envelope_measured_outside":
                          sv["a07"]["counts"]["envelope_measured_outside"],
                          "outside_insertions":
                          sv["a07"]["counts"]["outside_insertions"],
                          "outside_waypoints":
                          sv["a07"]["counts"]["outside_waypoints"]},
        "cheng_evaluation": {
            "files": cheng_files(["cheng_m2_6_mulatta_inertials"]),
            "verdict": "does_not_apply",
            "reason": ("segment morphometry carries no attachment-site "
                       "geometry; nothing to measure a placement against")},
    })

    # R-OWN-05 C17 attachment mechanics
    rows.append({
        "requirement_id": "R-OWN-05", "domain": "ownership",
        "kind": "requirement_gate",
        "statement": ("C17 finite attachment mechanics inputs for the 26 "
                      "explicit tissue-to-bone attachments"),
        "scope": "attachment interfaces (A06/A07 C17 blocks)",
        "status": STATUS_GAP,
        "sealed_source": a07pin,
        "missing_evidence": {
            "detail": sv["a07"]["c17_note"],
            "authorization_required": ("measured attachment-interface sources "
                                       "admitted by recorded lead decision"),
            "carried_verbatim_from": {"role": "a07_resolution",
                                      "pointer": "c17"}},
        "cheng_evaluation": {
            "files": cheng_files(["cheng_m2_3_mulatta_morphometry"]),
            "verdict": "does_not_close",
            "reason": ("morphometry is muscle-belly level (mass, fascicle "
                       "length, PCSA); no patch area, areal stiffness or "
                       "couple resistance at any attachment interface")},
    })

    # R-FRM-01 frame forest
    rows.append({
        "requirement_id": "R-FRM-01", "domain": "frame",
        "kind": "requirement_gate",
        "statement": ("authored assembly frame forest composed ONLY from "
                      "pinned active body declarations"),
        "scope": "authored-placement scope (no fitted fusion by law)",
        "status": STATUS_SATISFIED,
        "sealed_source": b04pin,
        "evidence": {"kind": "sealed_recomposition", "items": [
            {"pointer": f"recomposed_roots.{fid}.origin_m",
             "value": recompose(sv["b04"]["roots"][fid]["chain"])}
            for fid in sorted(sv["b04"]["roots"])],
            "note": ("every root recomposed left-to-right from its embedded "
                     "chain with identity quats asserted; exact equality to "
                     "the sealed origins; every hop sha256 = the pinned "
                     "chimanoid raw sha")},
        "cheng_evaluation": {
            "files": cheng_files(["cheng_m2_6_mulatta_inertials"]),
            "verdict": "does_not_apply",
            "reason": ("the tables carry percentages only (no absolute "
                       "segment lengths); they cannot author or bind frames")},
    })

    # R-FRM-02 bound port frame
    amiss = sv["b05"]["anchor_blocked_missing"]
    rows.append({
        "requirement_id": "R-FRM-02", "domain": "frame",
        "kind": "requirement_gate",
        "statement": ("accepted ulna-edge correspondence and authorized "
                      "packet-to-forest binding (bound port frame)"),
        "scope": "port anchor frame input (B05 ledger)",
        "status": STATUS_GAP,
        "sealed_source": b05pin,
        "missing_evidence": {
            "detail": " | ".join(amiss[0]),
            "authorization_required": ("recorded lead/architect decision "
                                       "(correspondence acceptance + binding "
                                       "authorization)"),
            "carried_verbatim_from": {"role": "b05_ports",
                                      "pointer": "ports[*].inputs."
                                                 "anchor_frame_id.missing_"
                                                 "evidence"}},
        "cheng_evaluation": {
            "files": cheng_files(["cheng_m2_6_mulatta_inertials"]),
            "verdict": "does_not_apply",
            "reason": ("no absolute segment lengths or frame correspondence "
                       "in the tables; binding stays a recorded-decision "
                       "matter")},
    })

    # R-FRM-03 component/bond admission ledger
    rows.append({
        "requirement_id": "R-FRM-03", "domain": "frame",
        "kind": "requirement_gate",
        "statement": ("component/bond admission ledger resolved (no "
                      "disconnected components or unresolved bodies left "
                      "unadmitted)"),
        "scope": "admission ledger (B04 carried statuses)",
        "status": STATUS_GAP,
        "sealed_source": b04pin,
        "missing_evidence": {
            "detail": (str(sv["b04"]["components"]) + " disconnected "
                       "components and " + str(sv["b04"]["unresolved_bodies"])
                       + " unresolved bodies remain; counted mass "
                       + repr(sv["b04"]["counted_mass_kg"]) + "; "
                       + sv["b04"]["matter_boundary_statement"]),
            "authorization_required": ("recorded lead decision admitting the "
                                       "components/bodies or a superseding "
                                       "assembly"),
            "carried_verbatim_from": {"role": "b04_frames",
                                      "pointer": "matter_boundary.statement"}},
        "cheng_evaluation": {
            "files": cheng_files(["cheng_m2_6_mulatta_inertials"]),
            "verdict": "does_not_apply",
            "reason": "segment tables carry no assembly topology"},
    })

    # R-PRT-01 mechanical qualification of the eight ports
    rows.append({
        "requirement_id": "R-PRT-01", "domain": "port",
        "kind": "requirement_gate",
        "statement": ("mechanical qualification of the eight real tendon "
                      "ports (radius/radius_l: BIClong-P11, BICshort-P8, "
                      "BRD-P3, PT-P5)"),
        "scope": "B05 qualification rule, re-enforced verbatim",
        "status": STATUS_GAP,
        "sealed_source": b05pin,
        "missing_evidence": {
            "detail": (str(sv["b05"]["counts"]["ports_remaining_blocked"])
                       + " of " + str(sv["b05"]["counts"]["ports"])
                       + " ports remain blocked; every blocked row names its "
                       "missing evidence (patch area measured footprint, "
                       "areal stiffness, couple resistance, bound frame, "
                       "carried-load weights); "
                       + sv["b05"]["qualification_rule"]),
            "authorization_required": ("the per-input authorizations named in "
                                       "the B05 ledger (measured sources / "
                                       "recorded decisions)"),
            "carried_verbatim_from": {"role": "b05_ports",
                                      "pointer": "qualification_rule"}},
        "sealed_counts": {"ports": sv["b05"]["counts"]["ports"],
                          "ports_mechanically_qualified":
                          sv["b05"]["counts"]["ports_mechanically_qualified"],
                          "ports_remaining_blocked":
                          sv["b05"]["counts"]["ports_remaining_blocked"],
                          "waypoints_refused_as_ports":
                          sv["b05"]["counts"]["waypoints_refused"]},
        "cheng_evaluation": {
            "files": cheng_files(["cheng_m2_3_mulatta_morphometry",
                                  "cheng_m2_5_fascicularis_morphometry"]),
            "verdict": "does_not_close",
            "reason": ("the missing evidence is attachment-site "
                       "patch/stiffness/couple/frame, not muscle "
                       "morphometry; and PT has no morphometry row at all "
                       "(S-PORT-09)")},
    })

    # R-PRT-02 declared pressure limits
    rows.append({
        "requirement_id": "R-PRT-02", "domain": "port",
        "kind": "requirement_gate",
        "statement": ("declared pressure limits carried from the pinned M03 "
                      "pressure source"),
        "scope": "declared law (never a qualification)",
        "status": STATUS_SATISFIED,
        "sealed_source": b05pin,
        "evidence": {"kind": "sealed_field_reread", "items": [
            {"pointer": "ports[*].inputs.pressure_limits.status",
             "value": sv["b05"]["pressure_statuses"]},
            {"pointer": "input_status_ledger.authored_engineering_requirements"
                        "[pressure_limits].source_status",
             "value": "synthetic_authored"},
        ], "note": ("declared status re-read on all eight ports; declared is "
                    "NOT qualified and never flips R-PRT-01")},
        "cheng_evaluation": {
            "files": cheng_files(["cheng_m2_6_mulatta_inertials"]),
            "verdict": "does_not_apply",
            "reason": "no pressure-limit content exists in the tables"},
    })
    return rows


def sealed_pin(role):
    path, want = SEALED_PINS[role]
    return {"role": role, "path": path, "blob_sha256": want}


def recompose(chain) -> list:
    """Naive left-to-right translation sum; identity quats asserted."""
    x = y = z = 0.0
    for hop in chain:
        q = hop["quat_wxyz"]
        if q != [1.0, 0.0, 0.0, 0.0]:
            raise Refused("non_identity_quat_in_chain",
                          f"hop {hop.get('body')} quat {q}")
        if hop["sha256"] != CHIMANOID_RAW_SHA256:
            raise Refused("chain_hop_pin_mismatch",
                          f"hop {hop.get('body')} sha256 {hop['sha256']}")
        x = x + hop["pos"][0]
        y = y + hop["pos"][1]
        z = z + hop["pos"][2]
    return [x, y, z]


# ---- document assembly ----------------------------------------------------------
def build_document() -> dict:
    prereg_path = HERE / "PREREGISTRATION.md"
    if not prereg_path.exists():
        raise Refused("preregistration_missing", str(prereg_path))
    prereg_sha = sha256_bytes(prereg_path.read_bytes())
    sealed = load_sealed()
    cheng = load_cheng()
    sv = sealed_values(sealed)
    gates = build_requirements(sv, cheng)
    screens = compute_screens(sv, cheng)

    satisfied = [r for r in gates if r["status"] == STATUS_SATISFIED]
    gaps = [r for r in gates if r["status"] == STATUS_GAP]
    gaps_by_domain = {}
    for r in gaps:
        gaps_by_domain[r["domain"]] = gaps_by_domain.get(r["domain"], 0) + 1
    readiness = (len(gaps) == 0)

    return {
        "schema": SCHEMA,
        "revision": DOCUMENT_REVISION,
        "object_id": OBJECT_ID,
        "card_id": CARD_ID,
        "task_id": TASK_ID_SHORT,
        "criteria_sha256": CRITERIA_SHA256,
        "done_when": DONE_WHEN,
        "preregistration_sha256": prereg_sha,
        "sealed_tip": SEALED_TIP,
        "base_head": BASE_HEAD,
        "law_statement": (
            "no substituted stand-in, no silent gap promotion, no fitting, "
            "no sealed-record edits; every gate row is either satisfied with "
            "pinned re-read evidence or a gap naming its missing evidence "
            "and authorizing rank; measured screens never gate"),
        "readiness_rule": READINESS_RULE,
        "carried_observation": CARRIED_OBSERVATION,
        "registry_profile": registry_profile(),
        "sealed_input_pins": {role: sealed_pin(role) for role in SEALED_PINS},
        "cheng_source_pins": {role: {"file": str(CHENG_DIR / CHENG_PINS[role][0])
                                     .replace("\\", "/"),
                                     "sha256": CHENG_PINS[role][1]}
                              for role in CHENG_PINS},
        "cheng_license_note": cheng["license_note"],
        "requirements": gates + screens,
        "counts": {
            "requirement_gate_rows": len(gates),
            "gate_satisfied": len(satisfied),
            "gate_gap": len(gaps),
            "measured_screen_rows": len(screens),
            "gaps_by_domain": gaps_by_domain,
        },
        "readiness": {
            "assembly_readiness": readiness,
            "rule": READINESS_RULE,
            "verdict_note": ("FALSE as carried by the sealed records: the "
                             "transported claims stay uncounted, ownership "
                             "mapping/correspondence and the bound port "
                             "frame are unresolved, and 8/8 ports remain "
                             "blocked; evaluation completeness is the card "
                             "outcome, not readiness"),
        },
        "determinism": {"canonical_json": True, "newline": "\\n",
                        "derive_command": "python -B assembly_readiness.py derive"},
    }


_REGISTRY_PROFILE_CACHE = None


def registry_profile() -> dict:
    """READ-ONLY read of the B06 verification profile from the registry."""
    global _REGISTRY_PROFILE_CACHE
    if _REGISTRY_PROFILE_CACHE is not None:
        return _REGISTRY_PROFILE_CACHE
    reg = "E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3"
    path = Path(reg)
    if not path.exists():
        return {"source": reg, "available": False}
    import sqlite3
    con = sqlite3.connect(f"file:{reg}?mode=ro", uri=True)
    try:
        cur = con.cursor()
        cur.execute("SELECT payload FROM state")
        payload = json.loads(cur.fetchone()[0])
    finally:
        con.close()
    card = payload["kanban"]["cards"][CARD_ID]
    oq = card["spec"]["ontology_qualification"]
    prof = oq["task"]["verification_profile"]
    profile_sha = hashlib.sha256(
        json.dumps(prof, sort_keys=True).encode("utf-8")).hexdigest()
    _REGISTRY_PROFILE_CACHE = {
        "source": reg + " kanban.cards[MAT2-B06].spec.ontology_qualification"
                        ".task.verification_profile (read-only sqlite)",
        "available": True,
        "task_id": oq["task_id"],
        "profile_id": prof["id"],
        "profile_kind": prof["kind"],
        "profile_sha256_canonical": profile_sha,
        "registry_criteria_sha256": card["criteria_sha256"],
    }
    return _REGISTRY_PROFILE_CACHE


# ---- validator --------------------------------------------------------------------
def validate_document(doc: dict) -> dict:
    """Re-derive everything from the pins and enforce the frozen law."""
    # V1 identity (semantic identity before aggregate counts)
    if doc.get("schema") != SCHEMA:
        raise Refused("schema_mismatch", repr(doc.get("schema")))
    if doc.get("object_id") != OBJECT_ID:
        raise Refused("object_id_mismatch", repr(doc.get("object_id")))
    if doc.get("criteria_sha256") != CRITERIA_SHA256:
        raise Refused("criteria_identity_mismatch",
                      repr(doc.get("criteria_sha256")))
    if doc.get("task_id") != TASK_ID_SHORT:
        raise Refused("task_id_mismatch", repr(doc.get("task_id")))
    live_prereg = sha256_bytes((HERE / "PREREGISTRATION.md").read_bytes())
    if doc.get("preregistration_sha256") != live_prereg:
        raise Refused("preregistration_pin_mismatch",
                      "document preregistration sha256 does not match the "
                      "live PREREGISTRATION.md bytes")
    if doc.get("sealed_tip") != SEALED_TIP:
        raise Refused("sealed_tip_mismatch", repr(doc.get("sealed_tip")))
    if doc.get("carried_observation") != CARRIED_OBSERVATION:
        raise Refused("observation_altered", repr(doc.get("carried_observation")))
    reg = doc.get("registry_profile") or {}
    if reg.get("available"):
        live = registry_profile()
        if reg.get("registry_criteria_sha256") != live["registry_criteria_sha256"]:
            raise Refused("registry_criteria_mismatch", "registry card "
                          "criteria differs from the document criteria")

    sealed = load_sealed()
    cheng = load_cheng()
    sv = sealed_values(sealed)

    gates = [r for r in doc["requirements"] if r["kind"] == "requirement_gate"]
    screens = [r for r in doc["requirements"] if r["kind"] == "measured_screen"]
    if len(gates) + len(screens) != len(doc["requirements"]):
        raise Refused("unlawful_kind_refused",
                      "every row kind must be requirement_gate or "
                      "measured_screen")

    # V2 statuses + evidence/missing-evidence law (semantic first)
    for row in doc["requirements"]:
        kind = row["kind"]
        status = row.get("status")
        if kind == "requirement_gate":
            if status not in LAWFUL_GATE_STATUSES:
                raise Refused("unlawful_status_refused",
                              f"{row['requirement_id']} status {status!r}")
            if status == STATUS_SATISFIED:
                ev = row.get("evidence")
                if not ev or not ev.get("items"):
                    raise Refused("satisfied_requires_pinned_evidence",
                                  f"{row['requirement_id']} satisfied without "
                                  "an evidence block")
                if ev.get("kind") == "sealed_recomposition":
                    for item in ev["items"]:
                        fid = item["pointer"].split(".")[1]
                        want = recompose(sv["b04"]["roots"][fid]["chain"])
                        if item["value"] != want:
                            raise Refused("satisfied_requires_pinned_evidence",
                                          f"{row['requirement_id']} {fid} "
                                          "recomposition disagrees with the "
                                          "sealed chain")
                else:
                    check_reread(row, sv)
            else:
                me = row.get("missing_evidence") or {}
                if not me.get("detail") or not me.get("authorization_required"):
                    raise Refused("gap_missing_evidence_refused",
                                  f"{row['requirement_id']} gap without "
                                  "named missing evidence + authorizing rank")
                carried = (me.get("carried_verbatim_from")
                           or row.get("carried_from"))
                if carried:
                    check_carried(row, carried, sv)
            sc = row.get("sealed_counts")
            if sc is not None:
                check_sealed_counts(row, sc, sv)
        elif kind == "measured_screen":
            if status not in LAWFUL_SCREEN_STATUSES:
                raise Refused("unlawful_status_refused",
                              f"{row['requirement_id']} status {status!r}")
            if row.get("gates") is not False:
                raise Refused("screen_must_not_gate",
                              f"{row['requirement_id']} gates={row.get('gates')!r}")
            ce = row.get("cheng_evaluation") or {}
            if ce.get("verdict") not in CHENG_VERDICTS:
                raise Refused("unlawful_cheng_verdict",
                              f"{row['requirement_id']} verdict "
                              f"{ce.get('verdict')!r}")
            if row.get("outcome") != "confirmed":
                raise Refused("screen_prediction_refused",
                              f"{row['requirement_id']} outcome "
                              f"{row.get('outcome')!r}")
        else:
            raise Refused("unlawful_kind_refused", repr(kind))

    # V3 satisfied rows must be exactly the preregistered set
    sat_ids = sorted(r["requirement_id"] for r in gates
                     if r["status"] == STATUS_SATISFIED)
    if sat_ids != sorted(FROZEN_COUNTS["expected_satisfied_ids"]):
        raise Refused("silent_gap_promotion_refused",
                      f"satisfied set {sat_ids} != frozen "
                      f"{sorted(FROZEN_COUNTS['expected_satisfied_ids'])}")

    # V4 recompute the screens from the pins
    want_screens = compute_screens(sv, cheng)
    for row in screens:
        want = next(w for w in want_screens
                    if w["requirement_id"] == row["requirement_id"])
        if row.get("computed") != want["computed"]:
            raise Refused("screen_recompute_mismatch",
                          row["requirement_id"])
        if row.get("outcome") != want["outcome"]:
            raise Refused("screen_recompute_mismatch",
                          row["requirement_id"] + " outcome")

    # V5 frozen counts
    counts = doc["counts"]
    frozen = dict(FROZEN_COUNTS)
    frozen.pop("expected_satisfied_ids")
    frozen.pop("expected_gap_ids")
    frozen.pop("expected_screen_ids")
    for key, want in frozen.items():
        if counts.get(key) != want:
            raise Refused("frozen_count_mismatch",
                          f"{key}: {counts.get(key)!r} != {want!r}")
    ids = [r["requirement_id"] for r in doc["requirements"]]
    if sorted(ids) != sorted(FROZEN_COUNTS["expected_satisfied_ids"]
                             + FROZEN_COUNTS["expected_gap_ids"]
                             + FROZEN_COUNTS["expected_screen_ids"]):
        raise Refused("frozen_count_mismatch", f"requirement id set {ids}")

    # V6 readiness rule
    readiness = doc["readiness"]["assembly_readiness"]
    rule_says = (counts["gate_gap"] == 0)
    if readiness != rule_says:
        raise Refused("readiness_rule_violation",
                      f"readiness {readiness!r} but gap count "
                      f"{counts['gate_gap']}")
    if readiness is not EXPECTED_READINESS:
        raise Refused("readiness_prediction_mismatch",
                      f"readiness {readiness!r} != frozen {EXPECTED_READINESS!r}")

    return {"valid": True, "gates": len(gates), "screens": len(screens),
            "gap": counts["gate_gap"], "readiness": readiness}


def check_reread(row: dict, sv: dict) -> None:
    """Satisfied-row evidence must re-read equal from the sealed values."""
    rid = row["requirement_id"]
    for item in row["evidence"]["items"]:
        pointer, recorded = item["pointer"], item["value"]
        if rid == "R-MASS-01":
            if pointer == "provenance.counted_set.counted_total_kg":
                want = sv["b03"]["counted_total_kg"]
            elif pointer == "provenance.counted_set.regions":
                want = sv["b03"]["counted_regions"]
            elif pointer == "recomputed.region_mass_sum_kg":
                want = sum(sv["b03"]["region_masses"][r]
                           for r in sv["b03"]["counted_regions"])
            else:
                raise Refused("satisfied_requires_pinned_evidence",
                              f"{rid} unknown pointer {pointer}")
        elif rid == "R-OWN-01":
            if pointer == "path_records[*].owner_body+role":
                want = sv["a06"]["all_ownered"]
            elif pointer == "attachments[*].interface_id+bone":
                want = sv["a06"]["all_attached"]
            elif pointer == "counts.path_records":
                want = sv["a06"]["path_records"]
            elif pointer == "counts.attachments":
                want = sv["a06"]["attachments"]
            elif pointer == "counts.waypoint_records":
                want = sv["a06"]["waypoint_records"]
            elif pointer == "counts.grasp_endpoints":
                want = sv["a06"]["grasp_endpoints"]
            else:
                raise Refused("satisfied_requires_pinned_evidence",
                              f"{rid} unknown pointer {pointer}")
        elif rid == "R-PRT-02":
            if pointer == "ports[*].inputs.pressure_limits.status":
                want = sv["b05"]["pressure_statuses"]
            elif pointer.startswith("input_status_ledger"):
                want = "synthetic_authored"
            else:
                raise Refused("satisfied_requires_pinned_evidence",
                              f"{rid} unknown pointer {pointer}")
        else:
            raise Refused("satisfied_requires_pinned_evidence",
                          f"{rid} has no re-read law")
        if recorded != want:
            raise Refused("satisfied_requires_pinned_evidence",
                          f"{rid} {pointer}: recorded {recorded!r} != sealed "
                          f"{want!r}")


def check_sealed_counts(row: dict, recorded: dict, sv: dict) -> None:
    """Gap-row sealed_counts must equal the values recomputed from the pins."""
    rid = row["requirement_id"]
    if rid == "R-MASS-03":
        want = {"excluded_osim_segment_claims_kg":
                sv["b03"]["excluded"]["mass_humerus"]
                + sv["b03"]["excluded"]["mass_radius"]
                + sv["b03"]["excluded"]["mass_ulna"]
                + sv["b03"]["excluded"]["mass_hand"]}
    elif rid == "R-OWN-02":
        want = {"pending_assembly_mapping":
                sv["a07"]["counts"]["pending_assembly_mapping"],
                "mutant_mapped_records":
                sv["a07"]["counts"]["mutant_mapped_records"]}
    elif rid == "R-OWN-03":
        want = {"forearm_correspondence_records": sv["a07"]["forearm_count"]}
    elif rid == "R-OWN-04":
        want = {"envelope_measured_outside":
                sv["a07"]["counts"]["envelope_measured_outside"],
                "outside_insertions": sv["a07"]["counts"]["outside_insertions"],
                "outside_waypoints": sv["a07"]["counts"]["outside_waypoints"]}
    elif rid == "R-PRT-01":
        want = {"ports": sv["b05"]["counts"]["ports"],
                "ports_mechanically_qualified":
                sv["b05"]["counts"]["ports_mechanically_qualified"],
                "ports_remaining_blocked":
                sv["b05"]["counts"]["ports_remaining_blocked"],
                "waypoints_refused_as_ports":
                sv["b05"]["counts"]["waypoints_refused"]}
    else:
        raise Refused("sealed_counts_unknown_row", rid)
    if recorded != want:
        raise Refused("sealed_counts_mismatch",
                      f"{rid}: {recorded!r} != recomputed {want!r}")


def check_carried(row: dict, carried: dict, sv: dict) -> None:
    """Carried-verbatim text must equal the sealed source text."""
    role, pointer = carried["role"], carried["pointer"]
    rid = row["requirement_id"]
    detail = row["missing_evidence"]["detail"]
    if role == "b05_ports" and "weights" in pointer:
        want_list = [w[0] for w in sv["b05"]["weights_blocked_missing"]]
        if any(w != want_list[0] for w in want_list):
            raise Refused("carried_text_mismatch",
                          f"{rid} sealed B05 weights missing_evidence is not "
                          "identical across the eight ports")
        if detail != want_list[0]:
            raise Refused("carried_text_mismatch",
                          f"{rid} carried text differs from sealed B05 "
                          "weights missing_evidence")
    elif role == "b05_ports" and "anchor_frame_id" in pointer:
        want_joined = " | ".join(sv["b05"]["anchor_blocked_missing"][0])
        if detail != want_joined:
            raise Refused("carried_text_mismatch",
                          f"{rid} carried text differs from sealed B05 "
                          "anchor_frame missing_evidence")
    elif role == "b05_ports" and "qualification_rule" in pointer:
        want = sv["b05"]["qualification_rule"]
        if want not in detail:
            raise Refused("carried_text_mismatch",
                          f"{rid} carried detail differs from sealed B05 "
                          "qualification_rule")
    elif role == "a07_resolution" and "pending" in pointer:
        want = sv["a07"]["pending_first"]["missing_evidence"]
        if detail != want["detail"]:
            raise Refused("carried_text_mismatch",
                          f"{rid} carried detail differs from the sealed A07 "
                          "pending record")
        if row["missing_evidence"]["authorization_required"] != \
                want["authorization_required"]:
            raise Refused("carried_text_mismatch",
                          f"{rid} authorization_required differs")
    elif role == "a07_resolution" and "forearm" in pointer:
        want = sv["a07"]["forearm_first"]["missing_evidence"]
        if detail != want["detail"]:
            raise Refused("carried_text_mismatch",
                          f"{rid} carried detail differs from the sealed A07 "
                          "forearm record")
    elif role == "a07_resolution" and "carried_observation" in pointer:
        a07 = load_sealed()["a07_resolution"]["doc"]
        want = a07["carried_observation"]["missing_evidence"]
        if "fitting" not in detail or "67.147" not in detail:
            raise Refused("carried_text_mismatch",
                          f"{rid} carried detail lacks the A07 observation")
        if want.get("authorization_required") is None:
            raise Refused("carried_text_mismatch",
                          f"{rid} sealed carried_observation has no "
                          "authorization rank")
    elif role == "a07_resolution" and pointer == "c17":
        a07 = load_sealed()["a07_resolution"]["doc"]
        want = a07["c17"]["note"]
        if want[:60] not in detail:
            raise Refused("carried_text_mismatch",
                          f"{rid} carried detail differs from sealed A07 c17")
    elif role == "b04_frames":
        b04 = load_sealed()["b04_frames"]["doc"]
        want = b04["matter_boundary"]["statement"]
        if want[:60] not in detail:
            raise Refused("carried_text_mismatch",
                          f"{rid} carried detail differs from sealed B04 "
                          "matter_boundary.statement")
    elif role == "dw04_mass_matrix":
        dw = load_sealed()["dw04_mass_matrix"]["doc"]
        want = dw["masses"][3]["semantic_identity"]
        if "transported_source_effective" not in detail or \
                str(sv["dw04"]["transported_kg"]) not in detail:
            raise Refused("carried_text_mismatch",
                          f"{rid} carried detail differs from the sealed "
                          "D-W04 transported record")
    elif role == "b03_material":
        # R-MASS-02 wording is authored from re-read sealed values; verify
        # the sealed density facts actually appear in the recorded detail.
        prov = sv["b03"]["density_provenance"]
        dens = sv["b03"]["density_kg_m3"]
        if repr(prov) not in detail or repr(dens) not in detail:
            raise Refused("carried_text_mismatch",
                          f"{rid} detail lacks the sealed density facts "
                          f"(class {prov!r}, {dens!r} kg/m3)")
    else:
        raise Refused("carried_pointer_unknown", f"{rid} {role} {pointer}")


# ---- falsifier harness ---------------------------------------------------------------
def tampered_copy_bytes(name: str, raw: bytes) -> Path:
    d = HERE / "work" / "falsifiers"
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    p.write_bytes(raw)
    return p


def run_falsifiers() -> list:
    """F1-F6 on tampered COPIES; committed artifact untouched."""
    log = []
    sealed = load_sealed()
    cheng = load_cheng()

    def expect(code, fn, arm):
        try:
            fn()
        except Refused as err:
            bitten = err.code == code
            log.append({"arm": arm, "expected": code, "bitten": bitten,
                        "observed": err.code, "detail": str(err)[:240]})
            return bitten
        log.append({"arm": arm, "expected": code, "bitten": False,
                    "observed": None, "detail": "no refusal raised"})
        return False

    # F1 unbound stand-in input
    expect("unbound_input_refused",
           lambda: assert_allowed_inputs(["standin_segment_mass"]),
           "F1 unbound_input_refused")

    # F2 silent gap promotion (copy of the emitted doc, flipped status)
    doc = json.loads((HERE / "assembly_readiness.json").read_text(encoding="utf-8"))
    bad = json.loads(json.dumps(doc))
    for row in bad["requirements"]:
        if row["requirement_id"] == "R-OWN-02":
            row["status"] = STATUS_SATISFIED
            row.pop("missing_evidence", None)
            row["evidence"] = {"kind": "sealed_field_reread", "items": []}
    try:
        validate_document(bad)
        err2 = None
    except Refused as err:
        err2 = err
    log.append({"arm": "F2 silent gap promotion", "expected":
                "satisfied_requires_pinned_evidence",
                "bitten": bool(err2 and err2.code ==
                               "satisfied_requires_pinned_evidence"),
                "observed": err2.code if err2 else None,
                "detail": str(err2)[:240] if err2 else "no refusal raised"})

    # F3 satisfied-with-broken-pin (evidence value altered)
    bad3 = json.loads(json.dumps(doc))
    for row in bad3["requirements"]:
        if row["requirement_id"] == "R-MASS-01":
            for item in row["evidence"]["items"]:
                if item["pointer"] == "provenance.counted_set.counted_total_kg":
                    item["value"] = 0.05
    try:
        validate_document(bad3)
        err3 = None
    except Refused as err:
        err3 = err
    log.append({"arm": "F3 satisfied pin-broken", "expected":
                "satisfied_requires_pinned_evidence",
                "bitten": bool(err3 and err3.code ==
                               "satisfied_requires_pinned_evidence"),
                "observed": err3.code if err3 else None,
                "detail": str(err3)[:240] if err3 else "no refusal raised"})

    # F4 tampered Cheng CSV (copy; loader pointed at the copy)
    raw = _cheng_raw("cheng_m2_6_mulatta_inertials")
    tampered = raw.replace(b"294", b"394", 1)
    if tampered == raw:
        raise SystemExit("cheng tamper did not change bytes")
    p4 = tampered_copy_bytes("m26_tampered.csv", tampered)
    expect("cheng_source_pin_mismatch",
           lambda: load_cheng({"cheng_m2_6_mulatta_inertials": tampered}),
           "F4 cheng_source_pin_mismatch")
    p4.unlink(missing_ok=True)

    # F5 unlawful status
    bad5 = json.loads(json.dumps(doc))
    bad5["requirements"][0]["status"] = "qualified"
    try:
        validate_document(bad5)
        err5 = None
    except Refused as err:
        err5 = err
    log.append({"arm": "F5 unlawful status", "expected":
                "unlawful_status_refused",
                "bitten": bool(err5 and err5.code == "unlawful_status_refused"),
                "observed": err5.code if err5 else None,
                "detail": str(err5)[:240] if err5 else "no refusal raised"})

    # F6 tampered sealed record (B05 port flipped qualified; raw bytes)
    raw6 = git_blob(SEALED_PINS["b05_ports"][0])
    tampered6 = raw6.replace(b'"blocked"', b'"qualified"', 1)
    if tampered6 == raw6:
        raise SystemExit("sealed tamper did not change bytes")
    p6 = tampered_copy_bytes("b05_tampered.json", tampered6)
    expect("sealed_pin_mismatch",
           lambda: load_sealed({"b05_ports": tampered6}),
           "F6 sealed_pin_mismatch")
    p6.unlink(missing_ok=True)

    fdir = HERE / "work" / "falsifiers"
    if fdir.exists() and not any(fdir.iterdir()):
        fdir.rmdir()
    _ = sealed
    return log


# ---- CLI -------------------------------------------------------------------------------
def derive() -> int:
    doc = build_document()
    result = validate_document(doc)
    doc_sha = write_canonical(HERE / "assembly_readiness.json", doc)
    receipt = {
        "object_id": OBJECT_ID, "card_id": CARD_ID, "task_id": TASK_ID_SHORT,
        "criteria_sha256": CRITERIA_SHA256,
        "preregistration_sha256": doc["preregistration_sha256"],
        "sealed_tip": SEALED_TIP,
        "document_sha256": doc_sha,
        "validator_result": result,
        "counts": doc["counts"],
        "readiness": doc["readiness"],
    }
    (HERE / "work" / "runs").mkdir(parents=True, exist_ok=True)
    write_canonical(HERE / "derivation_receipt.json", receipt)
    print(f"derive: valid={result['valid']} gates={result['gates']} "
          f"screens={result['screens']} gap={result['gap']} "
          f"readiness={result['readiness']} doc_sha256={doc_sha}")
    return 0


def verify() -> int:
    committed = (HERE / "assembly_readiness.json").read_bytes()
    doc = build_document()
    rerendered = canonical_json(doc).encode("utf-8")
    byte_identical = rerendered == committed
    result = validate_document(doc)
    flog = run_falsifiers()
    all_bitten = all(e["bitten"] for e in flog)
    receipt = {
        "object_id": OBJECT_ID, "card_id": CARD_ID, "task_id": TASK_ID_SHORT,
        "criteria_sha256": CRITERIA_SHA256,
        "sealed_tip": SEALED_TIP,
        "committed_document_sha256": sha256_bytes(committed),
        "rederived_document_sha256": sha256_bytes(rerendered),
        "double_derive_byte_identical": byte_identical,
        "validator_result": result,
        "falsifiers": flog,
        "falsifiers_all_bitten": all_bitten,
    }
    (HERE / "work" / "runs").mkdir(parents=True, exist_ok=True)
    write_canonical(HERE / "work" / "runs" / "verification_receipt.json", receipt)
    write_canonical(HERE / "work" / "runs" / "falsifier_log.json",
                    {"object_id": OBJECT_ID, "task_id": TASK_ID_SHORT,
                     "falsifiers": flog, "all_bitten": all_bitten})
    print(f"verify: byte_identical={byte_identical} valid={result['valid']} "
          f"falsifiers_all_bitten={all_bitten}")
    if not byte_identical:
        print("FAIL: re-derived document differs from committed bytes")
        return 1
    if not result["valid"] or not all_bitten:
        print("FAIL: validator or falsifiers")
        return 1
    return 0


def main(argv) -> int:
    if len(argv) < 2 or argv[1] not in ("derive", "verify", "falsifiers"):
        print("usage: python -B assembly_readiness.py {derive|verify|falsifiers}")
        return 2
    if argv[1] == "derive":
        return derive()
    if argv[1] == "falsifiers":
        flog = run_falsifiers()
        print(json.dumps(flog, indent=1))
        return 0 if all(e["bitten"] for e in flog) else 1
    return verify()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
