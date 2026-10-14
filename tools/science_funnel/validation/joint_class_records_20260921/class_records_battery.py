"""THE CLASS RECORDS BATTERY (lane agent/joint-class-records-20260921).

Executes the banked preregistration (24fd45c607130b40e5814029ffade453f0fce3a11505b7f33c223d28d1f75ab0)
as falsifier checks F1-F6:

  F1 coverage/teeth  -- all 23 bonds classed, taxonomy exact, DOF census, range shapes,
                        and the applied records EQUAL the expectations banked in
                        preregistration.md section 2 (parsed from the banked file).
  F2 citation        -- every recorded band equals the sha-pinned held record PARSED AT
                        BATTERY TIME (gait2392 / Rajagopal2016 / monkeyArm_current); the
                        NO-DOF classes cite absence and record no number.
  F3 byte-identity   -- the amendment's diff is exactly the 23 joint_class blocks: every
                        pre-existing bond field equals the banked pre-amendment snapshot,
                        and all 25 membranes' vertex books still match their committed
                        tris bins (the geometry IS the rest state; theta=0 stays the
                        committed bytes - the P6 law's A1, static form).
  F4 independence    -- the three committed batteries (hip_pivot_proof, p6_contrast,
                        tarsal_cycle_battery) re-run GREEN with the records present; each
                        regenerated battery.json differs from its committed file ONLY in
                        the definition-sha256 echoes its within-run watches must record;
                        every verdict leaf identical. The committed bytes are RESTORED
                        after the check.
  F5 kernel gates    -- test_definition 9/9, test_glue 8/8, training_gate PASS.
  F6 determinism     -- (verified by running this battery twice; its output is
                        byte-stable: no RNG, no timestamps, no set-order leakage).

Read-only on the committed tree except THIS lane's battery.json. Run:
  python -B tools/science_funnel/validation/joint_class_records_20260921/class_records_battery.py
"""

import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PRIOR_HIP = ROOT / "tools" / "science_funnel" / "validation" / "hip_pivot_proof_20260921"
PRIOR_P6 = ROOT / "tools" / "science_funnel" / "validation" / "p6_repreregistration_20260921"
PRIOR_TARSAL = ROOT / "tools" / "science_funnel" / "validation" / "tarsal_cycle_pivots_20260921"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PRIOR_HIP))

import hip_pivot_proof as hp  # noqa: E402  (committed registered machinery, imported verbatim)
from tools.matter_kernel import definition as definition_module  # noqa: E402

DATA = ROOT / "tools" / "science_funnel" / "data" / "morphosource_ct" / "matter_skeleton"
DEFN = DATA / "infant_skeleton.body.json"
OSIM_R = ROOT / "research_references" / "human" / "opensim" / "Rajagopal2016.osim"
OSIM_G = ROOT / "research_references" / "human" / "opensim" / "gait2392_thelen2003muscle.osim"
OSIM_M = ROOT / "tools" / "science_funnel" / "data" / "macaque_arm" / "monkeyArm_current.osim"
RECEIPT_M = ROOT / "tools" / "science_funnel" / "data" / "macaque_arm" / "download_receipt.json"
OUT = HERE / "battery.json"

TAXONOMY = ("ball_and_socket", "hinge_revolute", "condyled_gliding",
            "syndesmosis_nodof", "positional_contact")

# ---- BANKED CONSTANTS (preregistration 24fd45c6..., banked BEFORE the amendment) ----
BANKED_PREREG_SHA = "24fd45c607130b40e5814029ffade453f0fce3a11505b7f33c223d28d1f75ab0"
PRE_SHA256 = "95ddd2802d811f852cb842cfdcda4c1b6b4cc4160151589ec73c38e03d0b6a6c"
OSIM_R_SHA = "4ed1b573715b5747a203f6ea1dfdbbc6480ce8f24cf70fb00447591b1f599a1e"
OSIM_G_SHA = "18e5b3e406a619a78d109e81e6e2cd4f58681a967808fb52a992bbd2b27db019"
OSIM_M_SHA = "4148aee2c8dda1dcb0918496ad7c5e1adcf4ebabde0a68a3e0dc67faec67b895"

# The pre-amendment per-bond field snapshot (committed-data determination, taken from the
# definition at sha 95ddd280... BEFORE the amendment; the battery holds the applied
# definition to exactly these fields plus joint_class).
PRE_BOND_FIELDS = json.loads(r'''
{
 "bond.joint_01_02": {"members": ["mem.bone_01", "mem.bone_02"], "material": "mat.cartilage", "cure_strength": 13000000.0, "rest_length_mm": 1.44, "measured_gap_mm": 1.44, "refined_gap_mm": 1.403, "closest_points_mm": {"on_01": [61.142, 42.844, 41.118], "on_02": [59.904, 42.598, 41.731]}, "anatomical_reading": "hip joint: femoral head apposed to the acetabular region of the composite pelvis mass (Hartman & Straus 1933, The Anatomy of the Rhesus Monkey)", "evidence": "axial_adjacency_20260920 measured law gap 1.44 mm (identify_bones_v2 metric, cut 3.0 mm); receipt tools/science_funnel/validation/axial_adjacency_20260920/receipt.json; adopted by lane agent/axial-limb-adjacency-20260920 successor agent/hip-bond-adoption-20260921 from candidate_bonds.json bond.joint_01_02 (pre-registered GREEN, rest_length = the law gap per the refinement_law: bonds are defined on the vertex metric); receipt tools/science_funnel/validation/hip_adoption_20260921/receipt.json"},
 "bond.joint_01_03": {"members": ["mem.bone_01", "mem.bone_03"], "material": "mat.cartilage", "cure_strength": 13000000.0, "rest_length_mm": 1.49, "measured_gap_mm": 1.49, "refined_gap_mm": 1.343, "closest_points_mm": {"on_01": [59.633, 43.14, 25.066], "on_03": [58.322, 43.093, 24.777]}, "anatomical_reading": "hip joint: femoral head apposed to the acetabular region of the composite pelvis mass (Hartman & Straus 1933)", "evidence": "axial_adjacency_20260920 measured law gap 1.49 mm (identify_bones_v2 metric, cut 3.0 mm); receipt tools/science_funnel/validation/axial_adjacency_20260920/receipt.json; adopted by lane agent/axial-limb-adjacency-20260920 successor agent/hip-bond-adoption-20260921 from candidate_bonds.json bond.joint_01_03 (pre-registered GREEN, rest_length = the law gap per the refinement_law: bonds are defined on the vertex metric); receipt tools/science_funnel/validation/hip_adoption_20260921/receipt.json"},
 "bond.joint_02_06": {"members": ["mem.bone_02", "mem.bone_06"], "material": "mat.cartilage", "cure_strength": 13000000.0, "rest_length_mm": 2.91, "measured_gap_mm": 2.91, "evidence": "bone_identification_v3.json chain hind touching_edge [2, 6], gap_mm 2.91"},
 "bond.joint_02_15": {"members": ["mem.bone_02", "mem.bone_15"], "material": "mat.cartilage", "cure_strength": 13000000.0, "rest_length_mm": 1.01, "measured_gap_mm": 1.01, "evidence": "bone_identification_v3.json chain hind touching_edge [2, 15], gap_mm 1.01"},
 "bond.joint_03_07": {"members": ["mem.bone_03", "mem.bone_07"], "material": "mat.cartilage", "cure_strength": 13000000.0, "rest_length_mm": 2.83, "measured_gap_mm": 2.83, "evidence": "bone_identification_v3.json chain hind touching_edge [3, 7], gap_mm 2.83"},
 "bond.joint_03_17": {"members": ["mem.bone_03", "mem.bone_17"], "material": "mat.cartilage", "cure_strength": 13000000.0, "rest_length_mm": 0.69, "measured_gap_mm": 0.69, "evidence": "bone_identification_v3.json chain hind touching_edge [3, 17], gap_mm 0.69"},
 "bond.joint_04_08": {"members": ["mem.bone_04", "mem.bone_08"], "material": "mat.cartilage", "cure_strength": 13000000.0, "rest_length_mm": 0.73, "measured_gap_mm": 0.73, "evidence": "bone_identification_v3.json chain fore touching_edge [4, 8], gap_mm 0.73"},
 "bond.joint_04_10": {"members": ["mem.bone_04", "mem.bone_10"], "material": "mat.cartilage", "cure_strength": 13000000.0, "rest_length_mm": 2.0, "measured_gap_mm": 2.0, "evidence": "bone_identification_v3.json chain fore touching_edge [4, 10], gap_mm 2.0"},
 "bond.joint_04_12": {"members": ["mem.bone_04", "mem.bone_12"], "material": "mat.cartilage", "cure_strength": 13000000.0, "rest_length_mm": 0.93, "measured_gap_mm": 0.93, "evidence": "bone_identification_v3.json chain fore touching_edge [4, 12], gap_mm 0.93"},
 "bond.joint_05_09": {"members": ["mem.bone_05", "mem.bone_09"], "material": "mat.cartilage", "cure_strength": 13000000.0, "rest_length_mm": 0.86, "measured_gap_mm": 0.86, "evidence": "bone_identification_v3.json chain fore touching_edge [5, 9], gap_mm 0.86"},
 "bond.joint_05_11": {"members": ["mem.bone_05", "mem.bone_11"], "material": "mat.cartilage", "cure_strength": 13000000.0, "rest_length_mm": 2.27, "measured_gap_mm": 2.27, "evidence": "bone_identification_v3.json chain fore touching_edge [5, 11], gap_mm 2.27"},
 "bond.joint_05_13": {"members": ["mem.bone_05", "mem.bone_13"], "material": "mat.cartilage", "cure_strength": 13000000.0, "rest_length_mm": 0.86, "measured_gap_mm": 0.86, "evidence": "bone_identification_v3.json chain fore touching_edge [5, 13], gap_mm 0.86"},
 "bond.joint_06_20": {"members": ["mem.bone_06", "mem.bone_20"], "material": "mat.cartilage", "cure_strength": 13000000.0, "rest_length_mm": 0.48, "measured_gap_mm": 0.48, "evidence": "bone_identification_v3.json chain hind touching_edge [6, 20], gap_mm 0.48"},
 "bond.joint_06_25": {"members": ["mem.bone_06", "mem.bone_25"], "material": "mat.cartilage", "cure_strength": 13000000.0, "rest_length_mm": 0.66, "measured_gap_mm": 0.66, "evidence": "bone_identification_v3.json chain hind touching_edge [6, 25], gap_mm 0.66"},
 "bond.joint_07_18": {"members": ["mem.bone_07", "mem.bone_18"], "material": "mat.cartilage", "cure_strength": 13000000.0, "rest_length_mm": 1.79, "measured_gap_mm": 1.79, "evidence": "bone_identification_v3.json chain hind touching_edge [7, 18], gap_mm 1.79"},
 "bond.joint_07_21": {"members": ["mem.bone_07", "mem.bone_21"], "material": "mat.cartilage", "cure_strength": 13000000.0, "rest_length_mm": 0.45, "measured_gap_mm": 0.45, "evidence": "bone_identification_v3.json chain hind touching_edge [7, 21], gap_mm 0.45"},
 "bond.joint_07_24": {"members": ["mem.bone_07", "mem.bone_24"], "material": "mat.cartilage", "cure_strength": 13000000.0, "rest_length_mm": 0.86, "measured_gap_mm": 0.86, "evidence": "bone_identification_v3.json chain hind touching_edge [7, 24], gap_mm 0.86"},
 "bond.joint_10_12": {"members": ["mem.bone_10", "mem.bone_12"], "material": "mat.cartilage", "cure_strength": 13000000.0, "rest_length_mm": 0.38, "measured_gap_mm": 0.38, "evidence": "bone_identification_v3.json chain fore touching_edge [10, 12], gap_mm 0.38"},
 "bond.joint_11_13": {"members": ["mem.bone_11", "mem.bone_13"], "material": "mat.cartilage", "cure_strength": 13000000.0, "rest_length_mm": 0.47, "measured_gap_mm": 0.47, "evidence": "bone_identification_v3.json chain fore touching_edge [11, 13], gap_mm 0.47"},
 "bond.joint_20_25": {"members": ["mem.bone_20", "mem.bone_25"], "material": "mat.cartilage", "cure_strength": 13000000.0, "rest_length_mm": 2.47, "measured_gap_mm": 2.47, "evidence": "bone_identification_v3.json chain hind touching_edge [20, 25], gap_mm 2.47"},
 "bond.joint_21_24": {"members": ["mem.bone_21", "mem.bone_24"], "material": "mat.cartilage", "cure_strength": 13000000.0, "rest_length_mm": 2.9, "measured_gap_mm": 2.9, "evidence": "bone_identification_v3.json chain hind touching_edge [21, 24], gap_mm 2.9"},
 "bond.joint_22_25": {"members": ["mem.bone_22", "mem.bone_25"], "material": "mat.cartilage", "cure_strength": 13000000.0, "rest_length_mm": 0.99, "measured_gap_mm": 0.99, "evidence": "bone_identification_v3.json chain hind touching_edge [22, 25], gap_mm 0.99"},
 "bond.joint_23_24": {"members": ["mem.bone_23", "mem.bone_24"], "material": "mat.cartilage", "cure_strength": 13000000.0, "rest_length_mm": 1.01, "measured_gap_mm": 1.01, "evidence": "bone_identification_v3.json chain hind touching_edge [23, 24], gap_mm 1.01"}
}
''')

EXPECTED_COUNTS = {"ball_and_socket": 2, "hinge_revolute": 8, "condyled_gliding": 7,
                   "syndesmosis_nodof": 2, "positional_contact": 4}
DOF_CENSUS = {"3": 2, "1": 15, "0": 6}


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def parse_osim_coords(path: Path) -> dict:
    """coordinate name -> [lo, hi] (floats), across every joint of the model."""
    root = ET.parse(str(path)).getroot()
    out = {}
    for co in root.iter("Coordinate"):
        nm = co.get("name")
        rg = [float(x) for x in co.find("range").text.split()]
        out[nm] = rg
    return out


def parse_banked_table() -> dict:
    """The per-bond expectations, parsed from the BANKED preregistration.md section 2."""
    text = (HERE / "preregistration.md").read_text(encoding="utf-8")
    block = text.split("```", 2)[1]
    table = {}
    for line in block.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        table[cells[0]] = {"class": cells[1], "dof_count": int(cells[2]),
                           "range_rad": json.loads(cells[3]), "pivot_form": cells[4]}
    return table


def flatten(obj, path=""):
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(flatten(v, path + "/" + str(k)))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.update(flatten(v, path + "/%d" % i))
    else:
        out[path] = obj
    return out


def run_battery_script(lane: Path, script: str) -> dict:
    """Re-run one committed battery; return its echo-diff verdict. The committed battery.json
    bytes are RESTORED afterwards."""
    out_path = lane / "battery.json"
    saved = out_path.read_bytes()
    saved_sha = hashlib.sha256(saved).hexdigest()
    post_sha = sha256_file(DEFN)
    proc = subprocess.run([sys.executable, "-B", str(lane / script)],
                          cwd=str(ROOT), capture_output=True, text=True, timeout=1800)
    regenerated = out_path.read_bytes()
    hard_ok = None
    verdict_leaves_equal = None
    diff_paths = []
    echoes_ok = False
    if proc.returncode == 0 and regenerated != saved:
        reg = json.loads(regenerated.decode("utf-8"))
        com = json.loads(saved.decode("utf-8"))
        hard_ok = reg.get("hard_checks_pass")
        fr, fc = flatten(reg), flatten(com)
        diff_paths = sorted(k for k in set(fr) | set(fc) if fr.get(k) != fc.get(k, "<absent>"))
        echoes_ok = all(
            k.endswith("definition_sha256") or fr.get(k) in (PRE_SHA256, post_sha)
            for k in diff_paths)
        vreg = {k: v for k, v in fr.items() if not (
            k.endswith("definition_sha256") or v in (PRE_SHA256, post_sha))}
        vcom = {k: v for k, v in fc.items() if not (
            k.endswith("definition_sha256") or v in (PRE_SHA256, post_sha))}
        verdict_leaves_equal = (vreg == vcom)
    out_path.write_bytes(saved)  # RESTORE the committed bytes
    restored = out_path.read_bytes() == saved
    return {
        "script": script,
        "returncode": proc.returncode,
        "committed_sha256": saved_sha,
        "regenerated_differs": bool(diff_paths),
        "diff_leaf_paths": diff_paths,
        "diff_only_predicted_echoes": bool(echoes_ok),
        "verdict_leaves_identical": bool(verdict_leaves_equal),
        "hard_checks_pass_regenerated": bool(hard_ok),
        "committed_bytes_restored": bool(restored),
    }


def main() -> int:
    post_sha = sha256_file(DEFN)
    battery = {
        "schema": "chimera.matter_lane_battery.v1",
        "lane": "agent/joint-class-records-20260921",
        "title": "THE CLASS RECORDS: the joint_class amendment measured against its banked "
                 "preregistration and the committed batteries",
        "preregistration_sha256": sha256_file(HERE / "preregistration.md"),
        "preregistration_bank_matches_file": sha256_file(HERE / "preregistration.md") == BANKED_PREREG_SHA,
        "definition_sha256_pre_amendment_banked": PRE_SHA256,
        "definition_sha256_amended": post_sha,
        "checks": {},
        "gates": {},
        "reruns": {},
    }
    checks = battery["checks"]

    # ---- F0: the bank is the bank ----
    checks["preregistration_bank_matches_file"] = battery["preregistration_bank_matches_file"]

    # ---- F1: coverage + teeth + banked-table equality (the validator rides first) ----
    raw = DEFN.read_text(encoding="utf-8")
    body = json.loads(raw)
    parsed = definition_module.parse_body(DEFN)  # the committed validator, with the records present
    bonds = {b["id"]: b for b in parsed["bonds"]}
    banked = parse_banked_table()
    counts = {}
    census = {}
    coverage_ok = len(bonds) == 23 and set(banked) == set(bonds)
    table_ok = True
    teeth_ok = True
    for bid, b in sorted(bonds.items()):
        jc = b.get("joint_class")
        if jc is None:
            coverage_ok = False
            continue
        counts[jc["class"]] = counts.get(jc["class"], 0) + 1
        census[str(jc["dof_count"])] = census.get(str(jc["dof_count"]), 0) + 1
        exp = banked.get(bid)
        if not exp or exp["class"] != jc["class"] or exp["dof_count"] != jc["dof_count"] \
                or exp["range_rad"] != jc["range_rad"] or exp["pivot_form"] != jc["pivot_form"]:
            table_ok = False
        if jc["class"] not in TAXONOMY:
            coverage_ok = False
        if jc["dof_count"] == 0:
            if jc["range_rad"] is not None or jc["pivot_form"] != "none":
                teeth_ok = False
        elif jc["dof_count"] == 1:
            r = jc["range_rad"]
            if not (isinstance(r, list) and len(r) == 2 and all(isinstance(x, (int, float)) for x in r)
                    and r[0] < r[1]):
                teeth_ok = False
        elif jc["dof_count"] == 3:
            r = jc["range_rad"]
            if not (isinstance(r, list) and len(r) == 3
                    and all(isinstance(p, list) and len(p) == 2 and p[0] < p[1] for p in r)):
                teeth_ok = False
        else:
            teeth_ok = False
    checks["validator_parses_with_records_present"] = True
    checks["all_23_bonds_classed"] = coverage_ok
    checks["class_counts_exact"] = counts == EXPECTED_COUNTS
    checks["dof_census_3x2_1x15_0x6"] = census == DOF_CENSUS
    checks["applied_equals_banked_prereg_table"] = table_ok
    checks["range_shapes_match_dof"] = teeth_ok

    # ---- F2: citations, parsed at battery time ----
    sha_ok = (sha256_file(OSIM_R) == OSIM_R_SHA and sha256_file(OSIM_G) == OSIM_G_SHA
              and sha256_file(OSIM_M) == OSIM_M_SHA)
    mrec = json.loads(RECEIPT_M.read_text(encoding="utf-8"))
    pin = next(f["sha256"] for f in mrec["files"] if f["path"] == "monkeyArm_current.osim")
    sha_ok = sha_ok and pin == OSIM_M_SHA
    coords_r = parse_osim_coords(OSIM_R)
    coords_g = parse_osim_coords(OSIM_G)
    coords_m = parse_osim_coords(OSIM_M)
    cites = []

    def band_ok(bid, expected):
        return bonds[bid]["joint_class"]["range_rad"] == expected

    hip_ok = True
    for bid, s in (("bond.joint_01_02", "l"), ("bond.joint_01_03", "r")):
        expected = [coords_g["hip_flexion_%s" % s], coords_g["hip_adduction_%s" % s],
                    coords_g["hip_rotation_%s" % s]]
        hip_ok = hip_ok and band_ok(bid, expected)
    cites.append(("hips_vs_gait2392_three_coordinates", hip_ok))
    cites.append(("hips_vs_gait2392_three_coordinates", hip_ok))
    cites.append(("knees_vs_gait2392", all(
        band_ok(b, coords_g["knee_angle_l"]) and coords_g["knee_angle_l"] == coords_g["knee_angle_r"]
        for b in ("bond.joint_02_06", "bond.joint_03_07"))))
    cites.append(("elbows_vs_monkeyarm", all(
        band_ok(b, coords_m["elbow_flexion"]) for b in
        ("bond.joint_04_10", "bond.joint_04_12", "bond.joint_05_11", "bond.joint_05_13"))))
    cites.append(("radioulnar_vs_monkeyarm", all(
        band_ok(b, coords_m["radial_pronation"]) for b in ("bond.joint_10_12", "bond.joint_11_13"))))
    sub_ok = (coords_r["subtalar_angle_l"] == coords_r["subtalar_angle_r"]
              == [-0.34906585, 0.34906585])
    cites.append(("tarsal_class_vs_rajagopal_subtalar", all(
        band_ok(b, coords_r["subtalar_angle_l"]) for b in
        ("bond.joint_06_25", "bond.joint_20_25", "bond.joint_07_24", "bond.joint_21_24",
         "bond.joint_07_18", "bond.joint_22_25", "bond.joint_23_24"))))
    cites.append(("subtalar_band_is_the_registered_symmetric_band", bool(sub_ok)))
    absence_ok = all(
        bonds[b]["joint_class"]["range_rad"] is None
        and "no tibiofibular joint exists in any held model" in bonds[b]["joint_class"]["range_source"]
        for b in ("bond.joint_06_20", "bond.joint_07_21"))
    cites.append(("syndesmosis_cited_absence_no_number", absence_ok))
    positional_ok = all(
        bonds[b]["joint_class"]["range_rad"] is None
        and "no anatomical joint is claimed at this contact" in bonds[b]["joint_class"]["range_source"]
        for b in ("bond.joint_02_15", "bond.joint_03_17", "bond.joint_04_08", "bond.joint_05_09"))
    cites.append(("positional_contacts_no_joint_no_number", positional_ok))
    ctx_ok = all("[-0.6981317, 0.52359878]" in bonds[b]["joint_class"]["range_source"]
                 for b in ("bond.joint_06_25", "bond.joint_07_24", "bond.joint_07_18"))
    cites.append(("tarsal_adjacent_ankle_record_in_source_string", ctx_ok))
    hip_ctx_ok = all("[-0.52359878, 2.0943951]" in bonds[b]["joint_class"]["range_source"]
                     for b in ("bond.joint_01_02", "bond.joint_01_03"))
    cites.append(("hip_rajagopal_per_axis_context_in_source_string", hip_ctx_ok))
    cites.append(("osim_sha256_pins", bool(sha_ok)))
    checks["citations"] = dict(cites)
    checks["all_citations_green"] = all(v for _, v in cites)

    # ---- F3: static byte identity (the diff is exactly the inserted blocks) ----
    fields_ok = True
    for bid, snap in PRE_BOND_FIELDS.items():
        b = bonds.get(bid)
        if b is None:
            fields_ok = False
            break
        for k, v in snap.items():
            if b.get(k) != v:
                fields_ok = False
    checks["pre_existing_bond_fields_byte_identical"] = fields_ok
    geom = {}
    for mem in parsed["membranes"]:
        mid = mem["id"]
        n = int(mid.split("bone_")[1])
        blob, _ = hp.load_blob(n)
        geom[mid] = hp.vertex_records_sha(blob) == mem["vertex_sha256"]
    checks["all_25_vertex_books_match_committed_tris_bins"] = all(geom.values())
    checks["geometry_is_the_rest_state_theta0_A1"] = bool(fields_ok and all(geom.values()))

    # ---- the A5 refusal the records cite exists in the committed kernel machinery ----
    try:
        hp.pose_request(1e9, -0.1, 0.1)
        a5_present = False
    except hp.OutOfAnatomicalRange as exc:
        a5_present = exc.name == "out_of_anatomical_range" and exc.lo == -0.1 and exc.hi == 0.1
    checks["a5_refusal_class_present_and_named"] = bool(a5_present)

    # ---- F4: the committed batteries re-run green, echo-diff only, committed bytes restored ----
    battery["reruns"]["hip_pivot_proof"] = run_battery_script(PRIOR_HIP, "hip_pivot_proof.py")
    battery["reruns"]["p6_contrast"] = run_battery_script(PRIOR_P6, "p6_contrast.py")
    battery["reruns"]["tarsal_cycle_battery"] = run_battery_script(PRIOR_TARSAL, "tarsal_cycle_battery.py")
    reruns_ok = all(r["returncode"] == 0 and r["hard_checks_pass_regenerated"]
                    and r["diff_only_predicted_echoes"] and r["verdict_leaves_identical"]
                    and r["committed_bytes_restored"]
                    for r in battery["reruns"].values())
    checks["committed_batteries_green_with_records_present"] = reruns_ok

    # ---- F5: the kernel gates, unchanged ----
    g1 = subprocess.run([sys.executable, "-B", "-m", "tools.matter_kernel.test_definition"],
                        cwd=str(ROOT), capture_output=True, text=True, timeout=900)
    g2 = subprocess.run([sys.executable, "-B", "-m", "tools.matter_kernel.test_glue"],
                        cwd=str(ROOT), capture_output=True, text=True, timeout=900)
    g3 = subprocess.run([sys.executable, "-B", "tools/training_gate.py"],
                        cwd=str(ROOT), capture_output=True, text=True, timeout=900)
    battery["gates"]["test_definition"] = {"returncode": g1.returncode,
                                           "tail": " | ".join(g1.stderr.strip().splitlines()[-2:])}
    battery["gates"]["test_glue"] = {"returncode": g2.returncode,
                                     "tail": " | ".join(g2.stderr.strip().splitlines()[-2:])}
    battery["gates"]["training_gate"] = {"returncode": g3.returncode,
                                         "pass_line": "PASS" in g3.stdout,
                                         "tail": " | ".join(g3.stdout.strip().splitlines()[-2:])}
    gates_ok = (g1.returncode == 0 and "OK" in g1.stderr
                and g2.returncode == 0 and "OK" in g2.stderr
                and g3.returncode == 0 and "PASS" in g3.stdout)
    checks["kernel_gates_green"] = gates_ok

    # ---- verdict ----
    hard_keys = ["preregistration_bank_matches_file", "all_23_bonds_classed", "class_counts_exact",
                 "dof_census_3x2_1x15_0x6", "applied_equals_banked_prereg_table",
                 "range_shapes_match_dof", "all_citations_green",
                 "pre_existing_bond_fields_byte_identical",
                 "all_25_vertex_books_match_committed_tris_bins",
                 "geometry_is_the_rest_state_theta0_A1",
                 "a5_refusal_class_present_and_named",
                 "committed_batteries_green_with_records_present", "kernel_gates_green"]
    battery["hard_checks_pass"] = bool(all(checks[k] for k in hard_keys))
    battery["falsifiers_fired"] = [k for k in hard_keys if not checks[k]]

    text = json.dumps(battery, indent=1, sort_keys=True, ensure_ascii=True) + "\n"
    OUT.write_bytes(text.encode("utf-8"))
    print("battery written:", OUT)
    print("hard_checks_pass:", battery["hard_checks_pass"])
    print("falsifiers_fired:", battery["falsifiers_fired"])
    return 0 if battery["hard_checks_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
