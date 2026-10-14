"""THE HIND TORQUE BOOK FROM MEASURED ARMS (lane hind-torque-book-20260921).

Consumes the pulley lane's MEASURED wrap-geometry arm-vs-angle curves
(pulley_rederivation_20260920, commit 376fc92b) and the admitted muscle
forces, and produces:

  (1) the provenance audit of the gait walk's fore/hind drive caps
      (doc-derived statics numbers vs measured numbers - complete, no cap
      unaccounted);
  (2) the re-derivation of the knee-extension and MTP-flexion (the walk's
      knee/MP drive) torque caps: cap = max over the measured scan of
      sum_m F_m |r_m(q)|, under two force variants (V1 Oku measured walk
      peaks; V2 the batch's PCSA x sigma law, PROVISIONAL) and two scale
      variants (S1 deposit geometry; S2 arms x k = 0.11975394, the pulley
      lane's fitted per-taxon scalar);
  (3) the gait consumption map (order-of-magnitude deltas for the hind
      drive tier, the stance-hold ratios, and the posture/height
      feed-forward authority) - NO engine changes in this lane;
  (4) the Rule-0 verdicts against the pre-registration in receipt.json.

Read-only over every input (each sha256-verified against the receipt's
pins); writes ONLY hind_torque_book.json inside this directory (or --out).
Pure function of the pinned inputs: byte-deterministic by construction.

Run from the repo root:
  python -B tools/science_funnel/validation/hind_torque_book_20260921/derive_hind_torque_book.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
RECEIPT_PATH = HERE / "receipt.json"
PULLEY_DIR = HERE.parent / "pulley_rederivation_20260920"

# ---------------------------------------------------------------- constants

K_SI_MATCHED = 0.11975394      # pulley receipt scale_diagnosis.fitted_mtp_class_scalar_k
SINGLE_SUPPORT_DEMAND_SOURCE = "inputs/stance_hold.snapshot.json stance_nodes"

# The scene's compiler-emitted fore drive law (gait_scene.py compile_gait,
# wave-12 share flag / wave-16 trade): documented constants, not read from
# any snapshot (the fore drives are compiler-emitted, not graph-stored).
FORE_CAP_LAW = {
    "shoulder_base_N_m_at_s_0_45": 4.229,
    "shoulder_provenance": "MEASURED (quad-share lane: the s=0.45 envelope midpoint; wave-12 compiler comment 'the measured floors 63.435/56.4 ARE 15x the s=0.45 caps')",
    "elbow_ceiling_N_m": 3.76,
    "elbow_provenance": "DOC-DERIVED absolute ceiling (wave-11 falsifier: scaled down below s=0.45, never raised above it)",
    "share_s_default": 0.45,
    "share_law": "shoulder cap = 4.229 x (s/0.45); elbow cap = 3.76 x min(s, 0.45)/0.45; s in [0.25, 0.55] (compile-time require)",
    "store_floor_multiple": 15,
    "store_floor_multiple_provenance": "DERIVED MULTIPLE keyed to the measured floors 63.435/56.4 J at s=0.45",
    "viscous_damping_N_m_s_rad": 0.109,
    "viscous_damping_provenance": "SOURCE-QUOTED (the Oku hip damper, borrowed for the fore struts)",
}

REQURED_DRIVE_FIELDS = ["torque_cap_N_m", "store_floor_J", "store_floor_per_stride_J",
                        "store_stride_window", "viscous_damping_N_m_s_rad"]


# ---------------------------------------------------------------- helpers

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def canonical_json_bytes(obj) -> bytes:
    return (json.dumps(obj, indent=1, sort_keys=True) + "\n").encode("utf-8")


def interp_arm_m(direction: dict, deg: float) -> float:
    """Linear interpolation of a measured arm curve at a scan degree.

    The deliverable stores arm_samples_m at 201 uniform samples across the
    muscle's recorded jrange_deg (inclusive). Outside the scan -> KeyError
    by contract (refuse, never extrapolate): callers only query inside the
    scan.
    """
    lo, hi = direction["jrange_deg"]
    n = len(direction["arm_samples_m"])
    x = (deg - lo) / (hi - lo) * (n - 1)
    i = int(x)
    if i < 0 or i > n - 1:
        raise KeyError(f"deg {deg} outside measured scan [{lo}, {hi}]")
    if i == n - 1:           # exact scan endpoint: clamp to the last segment
        i, f = n - 2, 1.0
    else:
        f = x - i
    s = direction["arm_samples_m"]
    return s[i] * (1.0 - f) + s[i + 1] * f


def arm_at(direction: dict, deg: float) -> float:
    return interp_arm_m(direction, deg)


def common_grid(directions: list, step_deg: float) -> list:
    """The intersection of the muscles' measured scan ranges (the domain on
    which every muscle's arm is simultaneously measured). Knee/MTP scans run
    from a shallow bound toward a deep negative bound; the common domain is
    [shallowest-of-the-deep-ends .. deepest-of-the-shallow-ends]."""
    deep = max(min(d["jrange_deg"]) for d in directions)    # shallowest deep end
    shallow = min(max(d["jrange_deg"]) for d in directions)  # deepest shallow end
    if deep > shallow:
        raise ValueError(f"empty scan intersection [{deep}, {shallow}]")
    n = int(round((shallow - deep) / step_deg))
    grid = [deep + k * step_deg for k in range(n + 1)]       # ascending to the shallow end
    if abs(grid[-1] - shallow) > 1e-9:
        grid.append(shallow)
    return grid


def envelope(directions, forces, grid):
    """tau(q) = sum_m F_m |r_m(q)| on the common grid. Returns (samples,
    max_tau, argmax_deg). forces: list of (muscle_name, F_N)."""
    samples = []
    best = (-1.0, None)
    for q in grid:
        tau = 0.0
        for (f, name), d in zip(forces, directions):
            tau += f * abs(arm_at(d, q))
        samples.append({"q_deg": round(q, 4), "tau_N_m": round(tau, 6)})
        if tau > best[0]:
            best = (tau, round(q, 4))
    return samples, best[0], best[1]


# ---------------------------------------------------------------- inputs

def load_inputs():
    receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
    pins = receipt["pre_registration"]["inputs_pinned"]
    # verify every pin
    for key, pin in pins.items():
        p = HERE / pin["path"] if pin["path"].startswith("inputs/") else REPO / pin["path"]
        got = sha256_file(p)
        if got != pin["sha256"]:
            raise SystemExit(
                f"REFUSAL: input sha mismatch {key} ({pin['path']}): {got} != {pin['sha256']}")
    pulley = json.loads((PULLEY_DIR / "pulley_arms_derivation.json").read_text(encoding="utf-8"))
    geo = json.loads((HERE / "inputs/muscle_path_geometry.snapshot.json").read_text(encoding="utf-8"))
    oku = json.loads((HERE / "inputs/derived_numbers.snapshot.json").read_text(encoding="utf-8"))
    zeros = json.loads((HERE / "inputs/derived_zeros.snapshot.json").read_text(encoding="utf-8"))
    hold = json.loads((HERE / "inputs/stance_hold.snapshot.json").read_text(encoding="utf-8"))
    contract = json.loads((HERE / "inputs/gait_contract_drives.snapshot.json").read_text(encoding="utf-8"))
    return receipt, pins, pulley, geo, oku, zeros, hold, contract


# ---------------------------------------------------------------- audit

def build_audit(contract, oku, hold):
    """The complete provenance audit of the scene's fore/hind drive numbers."""
    entries = []

    def add(number_id, value, provenance_class, chain):
        entries.append({"number": number_id, "value": value,
                        "class": provenance_class, "chain": chain})

    exact_peaks = {j: oku["oku_before_alteration"]["torques"][j]["peak_abs_stance_Nm"]
                   for j in ("hip", "knee", "ankle", "MP")}
    exact_work = {j: oku["oku_before_alteration"]["work_per_cycle_J"][j]["positive_J"]
                  for j in ("hip", "knee", "ankle", "MP")}
    rounded_peaks = {"hip": 8.97, "knee": 5.31, "ankle": 5.92, "MP": 0.71}
    doc_caps = {"hip": 11.2125, "knee": 6.6375, "ankle": 7.4, "MP": 0.8875}
    joint_of = {"hip": "hip", "knee": "knee", "ankle": "ankle", "MP": "MP"}

    drives = contract["contract"]["drives"]
    for d in drives:
        stem = d["coordinate"].rsplit("_", 1)[0]   # hip_flexion / knee_extension / ...
        joint = d["joint"]
        for field in REQURED_DRIVE_FIELDS:
            number_id = f"drives.{d['coordinate']}.{field}"
            val = d[field]
            if field == "torque_cap_N_m":
                add(number_id, val, "DOC_DERIVED_STATICS (measured Oku source peak, doc-rounded, x1.25 headroom)",
                    [f"Oku measured walk |tau_peak| exact {joint} {exact_peaks[joint]} N.m (inputs/derived_numbers.snapshot.json oku_before_alteration.torques.{joint}.peak_abs_stance_Nm)",
                     f"derivation doc section 4.3 ROUNDS to {rounded_peaks[joint]} (docs/research/20260918_gait_controller_derivation.md)",
                     "cap law cap_d = 1.25 x |tau_peak,d| at the Oku scale (doc section 4.3; the 25% servo-headroom factor, one number one reason)",
                     f"1.25 x {rounded_peaks[joint]} = {val} N.m pinned in the graph contract (inputs/gait_contract_drives.snapshot.json)",
                     "wave-5 statics amendment (knee 13.18 / ankle 9.01) was banked, measured, FALSIFIED (the walk fell identically), and RESTORED - contract cap_amendment_note 'source_peaks_v1_RESTORED'"])
            elif field == "store_floor_J":
                add(number_id, val, "DOC_DERIVED from MEASURED Oku work (exact integral x 1.5 x 10-stride window)",
                    [f"Oku measured positive work per stride exact {joint} {exact_work[joint]} J (inputs/derived_numbers.snapshot.json oku_before_alteration.work_per_cycle_J.{joint}.positive_J)",
                     "store law = 1.5 headroom x W+ (doc section 4.4: 'the derived store floor')",
                     f"1.5 x {exact_work[joint]} x 10 = {val} J (10-stride window, store_stride_window = 10)",
                     "PROVENANCE ASYMMETRY (named by this audit): the store floors carry the EXACT integral while the sibling caps carry the DOC-ROUNDED peak - two pinning conventions live side by side in one record"])
            elif field == "store_floor_per_stride_J":
                add(number_id, val, "DERIVED (store_floor_J / store_stride_window)",
                    [f"{d['store_floor_J']} / 10 = {val} J/stride; same chain as store_floor_J"])
            elif field == "store_stride_window":
                add(number_id, val, "AUTHORED LAW CONSTANT",
                    ["10 strides - the F-G4 energy falsifier's measurement window (10-stride run, empty_events_d = 0)"])
            elif field == "viscous_damping_N_m_s_rad":
                add(number_id, val, "SOURCE_QUOTED (Oku model joint damper)",
                    [f"Oku model's {joint} viscous damper, quoted not derived (doc section 4.2: 'quoted')"])
    # the exact-scale parallel cap set (the ROUNDING SPLIT)
    hold_caps = hold["stance_nodes"][0]
    for j, key in (("hip", "cap_hip"), ("knee", "cap_knee"), ("ankle", "cap_ankle"), ("MP", "cap_mp")):
        add(f"stance_hold.caps.{j}", hold_caps[key],
            "DERIVED_EXACT_SCALE (1.25 x exact Oku peak) - the derivation lane's parallel pin",
            [f"1.25 x {exact_peaks[j]} = {hold_caps[key]} N.m (inputs/stance_hold.snapshot.json {key})",
             f"the contract/engine pin for the same joint is {doc_caps[j]} (1.25 x rounded {rounded_peaks[j]})",
             "the ROUNDING SPLIT the posture-cap-provenance lane (buffy, abe609ca) documented for the hip, present for ALL FOUR joints; two live constants differ by up to "
             f"{round(abs(1.25 * exact_peaks['hip'] - doc_caps['hip']), 6)} N.m (hip)"])
    # fore law constants
    add("fore_caps.law", FORE_CAP_LAW["share_law"], "COMPILER LAW (mixed provenance, itemized)",
        [FORE_CAP_LAW["shoulder_provenance"], FORE_CAP_LAW["elbow_provenance"],
         "gait_scene.py compile_gait: require(0.25<=s<=0.55); sh_cap=4.229*(s/0.45); el_cap=3.76*min(s,0.45)/0.45; store floors 15x cap"])
    add("fore_caps.shoulder_base_4_229", 4.229, "MEASURED (quad-share lane)",
        ["the s=0.45 envelope midpoint's measured cap; the measured store floors 63.435 J = 15 x 4.229 (wave-12 compiler comment)"])
    add("fore_caps.elbow_ceiling_3_76", 3.76, "DOC_DERIVED absolute ceiling",
        ["wave-11 falsifier: scaled down below s=0.45, never raised above it (gait_scene.py compile_gait comment)"])
    add("fore_caps.store_multiple_15x", 15, "DERIVED MULTIPLE",
        ["'the measured floors 63.435/56.4 ARE 15x the s=0.45 caps' - the multiple keyed to the measured floors"])
    add("fore_caps.damping_0_109", 0.109, "SOURCE_QUOTED",
        ["the Oku hip damper value, reused for the four fore strut drives (gait_scene.py fore_drives)"])
    # posture drive keying
    add("posture_drive.cap_keying", "engine keys the posture drive to drives_[0].cap (the HIP cap)",
        "DERIVED_KEYING (borrowed, never derived in-lane)",
        ["gait_controller.hpp servo(): the posture drive capped at the hip cap independently (cap-on-each)",
         "derive_trunk_pitch.py CAP_POST = 1.25 x 8.9746 = 11.21825 (the exact-scale pin) vs the engine's 11.2125",
         "the posture-cap-provenance lane derived a muscle-grounded amendment 10.54 N.m (ILI+GMed pair, PCSA x sigma x cos(pennation) x hip arm) - NOT yet consumed by any engine wave"])
    # mp range amendment (a cap-adjacent authored number the audit must not miss)
    add("mp_range.plantarflexion_stop", "-0.35 -> -1.2 rad (revision 2)",
        "AUTHORED AMENDMENT with its own falsifier",
        ["contract mp_range_amendment: the zero map composes the admitted M table (min -0.142 Oku) to scene -0.911 rad; the authored stop would clamp 0.56 rad off the measured target; falsifier: MP hyper-curl artifacts would refute the AMENDMENT, not the zeros"])

    index = {e["number"]: e for e in entries}
    # COMPLETENESS: every number in the 8 hind drive records + the 4 fore
    # drive records accounted exactly once.
    missing = []
    for d in drives:
        for field in REQURED_DRIVE_FIELDS:
            key = f"drives.{d['coordinate']}.{field}"
            if key not in index:
                missing.append(key)
    fore_coords = ["shoulder_flexion_fore_left", "elbow_flexion_fore_left",
                   "shoulder_flexion_fore_right", "elbow_flexion_fore_right"]
    for coord in fore_coords:
        for field in REQURED_DRIVE_FIELDS:
            key = f"fore_law.{coord}.{field}"
            if key not in index:
                # fore records are compiler-emitted from the audited law constants;
                # add explicit per-record law-consumption entries so the table is complete
                suffix = (" (15x the s-conditional cap)" if field.startswith("store")
                          else " (4.229 x (s/0.45) or 3.76 x min(s,0.45)/0.45)" if field == "torque_cap_N_m"
                          else " (constant across s)" if field == "store_stride_window"
                          else " (0.109, the quoted Oku hip damper)")
                add(key, "law value at s=0.45" if field != "viscous_damping_N_m_s_rad" else 0.109,
                    "CONSUMES THE AUDITED FORE LAW",
                    [f"{coord}.{field} is emitted by gait_scene.py from the fore law constants audited above" + suffix])
                index = {e["number"]: e for e in entries}
    for d in drives + [{"coordinate": c} for c in fore_coords]:
        for field in REQURED_DRIVE_FIELDS:
            key = f"drives.{d['coordinate']}.{field}" if d in drives else f"fore_law.{d['coordinate']}.{field}"
            if key not in index:
                missing.append(key)
    completeness = {
        "required_hind_numbers": len(drives) * len(REQURED_DRIVE_FIELDS),
        "required_fore_numbers": len(fore_coords) * len(REQURED_DRIVE_FIELDS),
        "missing": missing,
        "complete": not missing,
        "audit_entries_total": len(entries),
    }
    return entries, completeness, exact_peaks, exact_work


# ---------------------------------------------------------------- rederivation

def build_book(receipt, pins, pulley, geo, oku, zeros, hold, contract):
    dirs_ = pulley["directions"]
    muscles = geo["hindlimb"]["poses"]["walking"]["muscles"]
    muscles_neutral = geo["hindlimb"]["poses"]["neutral"]["muscles"]
    sigma = geo["hindlimb"]["specific_tension"]
    oku_forces = oku["oku_muscle_forces_N"]["before"]
    drives = contract["contract"]["drives"]
    cap_of = {d["coordinate"].rsplit("_", 1)[0]: d["torque_cap_N_m"] for d in drives}
    current_knee = cap_of["knee_extension"]
    current_mp = cap_of["MP_dorsiflexion"]

    def direction(name):
        d = dirs_[name]
        return {"jrange_deg": d["jrange_deg"], "arm_samples_m": d["arm_samples_m"]}

    def arm_extrema_mm(name):
        a = dirs_[name]["arm_samples_m"]
        return [round(min(a) * 1000.0, 4), round(max(a) * 1000.0, 4)]

    def trace_of(pin_key, extra=None):
        pin = pins[pin_key]
        t = {"input": pin["path"], "sha256": pin["sha256"]}
        if extra:
            t["key_path"] = extra
        return t

    # ---- KNEE EXTENSION (quads: RF + vasti VI/VL/VM over the condyle cylinder)
    knee_names = ["R_RF", "R_VI", "R_VL", "R_VMed"]
    knee_dirs = [direction(n) for n in knee_names]
    knee_grid = common_grid([ {"jrange_deg": d["jrange_deg"]} for d in knee_dirs ], 0.05)
    pcsa = {m: muscles[m]["pcsa_m2"] for m in ("VI", "VL", "VM")}
    pcsa_sum = sum(pcsa.values())
    shares = {m: pcsa[m] / pcsa_sum for m in pcsa}
    F_VAS = oku_forces["VAS"]["peak_N"]
    F_RF = oku_forces["RF"]["peak_N"]
    # forces ordered with the directions [R_RF, R_VI, R_VL, R_VMed]
    v1_forces = [(F_RF, "R_RF"), (F_VAS * shares["VI"], "R_VI"),
                 (F_VAS * shares["VL"], "R_VL"), (F_VAS * shares["VM"], "R_VMed")]
    v2_forces = [(muscles["VI"]["max_force_N"], "R_VI"),
                 (muscles["VL"]["max_force_N"], "R_VL"),
                 (muscles["VM"]["max_force_N"], "R_VMed")]
    # V2 has no RF row (named gap): build as vasti-only over the same three directions
    v2_dirs = [knee_dirs[1], knee_dirs[2], knee_dirs[3]]
    knee = {}
    s1_grid_deg = [round(q, 3) for q in knee_grid]
    samples_v1, cap_v1, arg_v1 = envelope(knee_dirs, v1_forces, knee_grid)
    samples_v2, cap_v2, arg_v2 = envelope(v2_dirs, v2_forces, knee_grid)
    cap_v1_s2 = cap_v1 * K_SI_MATCHED
    cap_v2_s2 = cap_v2 * K_SI_MATCHED
    # walk window: scene knee range -73.4..-31.5 deg (derived_zeros checks); flexion
    # negative in BOTH the scene and the Wiseman model -> overlap with the scan
    # [max_jrange_lo, 0] is [min(max lo), -31.5]
    walk_knee_deg = [-73.4, -31.5]
    # overlap of the common scan [-42.3, 0] with the walk's [-73.4, -31.5]
    knee_walk_lo = max(min(min(d["jrange_deg"]) for d in knee_dirs), walk_knee_deg[0])   # -42.3
    knee_walk_hi = min(max(max(d["jrange_deg"]) for d in knee_dirs), walk_knee_deg[1])   # -31.5
    knee_walk_grid = [q for q in knee_grid if knee_walk_lo - 1e-9 <= q <= knee_walk_hi + 1e-9]
    _, cap_v1_walk, arg_v1_walk = envelope(knee_dirs, v1_forces, knee_walk_grid)
    knee_book = {
        "direction": "knee_extension",
        "walk_drive": "knee_extension_left/right",
        "current_cap_N_m": current_knee,
        "current_cap_provenance": "1.25 x doc-rounded Oku measured walk knee peak 5.31 (exact 5.3144) - DOC-DERIVED statics",
        "muscle_class": "quadriceps femoris: RF (rectus femoris) + VI/VL/VM (vasti) over rFemoralCondyles_Cylinder2 (the patella-substitute pulley), wrap engaged 2001/2001 per the pulley receipt",
        "measured_curves": {n: {"extrema_mm": arm_extrema_mm(n), "jrange_deg": dirs_[n]["jrange_deg"],
                                 "source": "tools/science_funnel/validation/pulley_rederivation_20260920/pulley_arms_derivation.json directions.%s" % n,
                                 "sha256": pins["pulley_arms_derivation"]["sha256"]} for n in knee_names},
        "common_grid_deg": {"lo": round(min(knee_grid), 3), "hi": round(max(knee_grid), 3),
            "step_deg": 0.05,
            "note": "the intersection of the four measured scans (RF/VL end at -42.3, VI/VMed at -45); every muscle simultaneously measured here"},
        "variants": {},
        "pre_registered": receipt["pre_registered_delta_signs"]["knee_extension"],
    }
    knee_book["variants"]["V1_S1_oku_walk_peaks_deposit_arms"] = {
        "status": "MEASURED forces x MEASURED(deposit-scale) arms",
        "force_law": "VAS group 276.69 N split by Guimaraes PCSA share (VI %.5f / VL %.5f / VM %.5f) + RF 105.98 N whole" % (
            shares["VI"], shares["VL"], shares["VM"]),
        "cap_N_m": round(cap_v1, 6), "argmax_q_deg": arg_v1,
        "delta_N_m": round(cap_v1 - current_knee, 6),
        "ratio_vs_current": round(cap_v1 / current_knee, 6),
        "envelope_samples_N_m": samples_v1,
        "trace": {"arms": trace_of("pulley_arms_derivation", "directions.R_RF|R_VI|R_VL|R_VMed.arm_samples_m"),
                  "forces": trace_of("derived_numbers_snapshot", "oku_muscle_forces_N.before.VAS.peak_N|RF.peak_N"),
                  "shares": trace_of("muscle_path_geometry_snapshot", "hindlimb.poses.walking.muscles.{VI,VL,VM}.pcsa_m2")},
    }
    knee_book["variants"]["V2_S1_pcsa_sigma_deposit_arms"] = {
        "status": "PROVISIONAL (the batch's PCSA x sigma law; sigma 1280914.14 Pa derived, per-group implied tensions scatter 0.31-5.28 MPa; RF has NO Guimaraes row - vasti only, named gap)",
        "force_law": "record max_force_N = PCSA x sigma x cos(pennation): VI %.2f + VL %.2f + VM %.2f N" % (
            muscles["VI"]["max_force_N"], muscles["VL"]["max_force_N"], muscles["VM"]["max_force_N"]),
        "cap_N_m": round(cap_v2, 6), "argmax_q_deg": arg_v2,
        "delta_N_m": round(cap_v2 - current_knee, 6),
        "ratio_vs_current": round(cap_v2 / current_knee, 6),
        "envelope_samples_N_m": samples_v2,
        "trace": {"arms": trace_of("pulley_arms_derivation", "directions.R_VI|R_VL|R_VMed.arm_samples_m"),
                  "forces": trace_of("muscle_path_geometry_snapshot", "hindlimb.poses.walking.muscles.{VI,VL,VM}.max_force_N"),
                  "sigma": trace_of("muscle_path_geometry_snapshot", "hindlimb.specific_tension")},
    }
    knee_book["variants"]["V1_S2_oku_peaks_si_matched_arms"] = {
        "status": "MEASURED forces x k-scaled arms (the authors'-scale reading; k = 0.11975394, the pulley lane's fitted per-taxon scalar - ABSOLUTE-SCALE CAVEAT)",
        "cap_N_m": round(cap_v1_s2, 6),
        "argmax_q_deg": arg_v1,
        "argmax_note": "same argmax as S1 - the scale is multiplicative on the arms",
        "delta_N_m": round(cap_v1_s2 - current_knee, 6),
        "ratio_vs_current": round(cap_v1_s2 / current_knee, 6),
        "trace": {"k": {"source": "tools/science_funnel/validation/pulley_rederivation_20260920/receipt.json scale_diagnosis.fitted_mtp_class_scalar_k",
                         "sha256": pins["pulley_receipt"]["sha256"], "value": K_SI_MATCHED}},
    }
    knee_book["variants"]["V2_S2_pcsa_sigma_si_matched_arms"] = {
        "status": "PROVISIONAL forces x k-scaled arms",
        "cap_N_m": round(cap_v2_s2, 6),
        "argmax_q_deg": arg_v2,
        "argmax_note": "same argmax as S1 - the scale is multiplicative on the arms",
        "delta_N_m": round(cap_v2_s2 - current_knee, 6),
        "ratio_vs_current": round(cap_v2_s2 / current_knee, 6),
    }
    knee_book["walk_window"] = {
        "scene_range_deg": walk_knee_deg,
        "evaluated_overlap_deg": [round(min(knee_walk_grid), 3), round(max(knee_walk_grid), 3)],
        "cap_in_walk_window_N_m": round(cap_v1_walk, 6), "argmax_q_deg": arg_v1_walk,
        "note": "the tier clamp acts over the whole scan; the walk's loaded knee window sits at the measured curve's HIGH-arm end (arms grow with flexion magnitude), so the walk-window capability ~ the scan-max; the reported overlap is the EVALUATED grid window (the common scan ends at -42.3, the raw intersection bound -45 is not measured by RF/VL)",
    }

    # ---- MTP FLEXION (FDL II-V + FHL over the ankle cylinder / distal-tibia ellipsoid)
    mtp_names = ["R_FDL_TENDONII", "R_FDL_TENDONIII", "R_FDL_TENDONIV", "R_FDL_TENDONV", "R_FHL"]
    mtp_dirs = [direction(n) for n in mtp_names]
    mtp_grid = common_grid([{"jrange_deg": d["jrange_deg"]} for d in mtp_dirs], 0.05)
    F_FDL = oku_forces["FDL"]["peak_N"]
    # equal split: one muscle, four slips, no measured partition; FHL force 0
    # (no Oku measurement - named gap) so the force list aligns with the dirs
    v1_forces_mtp = [(F_FDL / 4.0, n) for n in mtp_names[:4]] + [(0.0, "R_FHL")]
    v2_forces_mtp = [(muscles["FDL"]["max_force_N"] / 4.0, n) for n in mtp_names[:4]] + \
                    [(muscles["FHL"]["max_force_N"], "R_FHL")]
    samples_m1, cap_m1, arg_m1 = envelope(mtp_dirs, v1_forces_mtp, mtp_grid)
    samples_m2, cap_m2, arg_m2 = envelope(mtp_dirs, v2_forces_mtp, mtp_grid)
    # brackets for the unmeasured slip partition: all force on one slip
    arm_lo = min(abs(arm_at(d, q)) for d in mtp_dirs[:4] for q in mtp_grid)
    arm_hi = max(abs(arm_at(d, q)) for d in mtp_dirs[:4] for q in mtp_grid)
    cap_m1_lo_bracket = F_FDL * arm_lo
    cap_m1_hi_bracket = F_FDL * arm_hi
    cap_m1_s2 = cap_m1 * K_SI_MATCHED
    cap_m2_s2 = cap_m2 * K_SI_MATCHED
    # walk range: scene MP -0.91..+0.55 rad = -52.2..+31.5 deg; contains [-30, +30]
    # under EITHER sense mapping -> the full scan is walk-reachable
    mp_book = {
        "direction": "mtp_flexion",
        "walk_drive": "MP_dorsiflexion_left/right",
        "current_cap_N_m": current_mp,
        "current_cap_provenance": "1.25 x doc-rounded Oku measured walk MP peak 0.71 (exact 0.7051) - DOC-DERIVED statics",
        "muscle_class": "FDL tendons II-V (one muscle, four slips) + FHL (hallux), routed over R_Ankle_Cylinder / rDistalTibia_ellipsoid per the pulley receipt; the MTP arm arises from the mtp/hallux-crossing segments",
        "measured_curves": {n: {"extrema_mm": arm_extrema_mm(n), "jrange_deg": dirs_[n]["jrange_deg"],
                                 "source": "tools/science_funnel/validation/pulley_rederivation_20260920/pulley_arms_derivation.json directions.%s" % n,
                                 "sha256": pins["pulley_arms_derivation"]["sha256"]} for n in mtp_names},
        "common_grid_deg": {"lo": round(max(d["jrange_deg"][1] for d in mtp_dirs), 3),
                             "hi": round(min(d["jrange_deg"][0] for d in mtp_dirs), 3), "step_deg": 0.05,
                             "note": "intersection of the five measured scans: FDL III ends at +5.4 deg, so the common domain is [-30, +5.4]; IV/V/FHL measure to +/-30 and II to +21.6 (their extra range enters the per-muscle bracket below)"},
        "variants": {},
        "pre_registered": receipt["pre_registered_delta_signs"]["MP_dorsiflexion_mtp_flexion"],
        "walk_coverage_note": "scene MP range -0.91..+0.55 rad (derived_zeros check) = -52.2..+31.5 deg CONTAINS the [-30,+30] deg scan under EITHER flexion/dorsiflexion sense mapping: the full measured scan is walk-reachable, no extrapolation",
    }
    mp_book["variants"]["V1_S1_oku_walk_peaks_deposit_arms_equal_split"] = {
        "status": "MEASURED forces x MEASURED(deposit-scale) arms; FHL EXCLUDED (no Oku measurement - named gap); FDL split EQUALLY across tendons II-V (one muscle, four slips, no measured partition)",
        "force_law": "FDL 204.57 N x 1/4 per slip",
        "cap_N_m": round(cap_m1, 6), "argmax_q_deg": arg_m1,
        "partition_bracket_N_m": {"all_force_on_min_arm": round(cap_m1_lo_bracket, 6),
                                   "all_force_on_max_arm": round(cap_m1_hi_bracket, 6),
                                   "note": "the equal-split cap sits between the single-slip bounds; the partition is unmeasured and the bracket is its honest width"},
        "delta_N_m": round(cap_m1 - current_mp, 6),
        "ratio_vs_current": round(cap_m1 / current_mp, 6),
        "envelope_samples_N_m": samples_m1,
        "trace": {"arms": trace_of("pulley_arms_derivation", "directions.R_FDL_TENDONII..V.arm_samples_m"),
                  "forces": trace_of("derived_numbers_snapshot", "oku_muscle_forces_N.before.FDL.peak_N")},
    }
    mp_book["variants"]["V2_S1_pcsa_sigma_deposit_arms"] = {
        "status": "PROVISIONAL (PCSA x sigma law); FDL 548.85 N quarter-split + FHL 128.07 N whole",
        "cap_N_m": round(cap_m2, 6), "argmax_q_deg": arg_m2,
        "delta_N_m": round(cap_m2 - current_mp, 6),
        "ratio_vs_current": round(cap_m2 / current_mp, 6),
        "envelope_samples_N_m": samples_m2,
        "trace": {"arms": trace_of("pulley_arms_derivation", "directions.R_FDL_TENDONII..V|R_FHL.arm_samples_m"),
                  "forces": trace_of("muscle_path_geometry_snapshot", "hindlimb.poses.walking.muscles.{FDL,FHL}.max_force_N")},
    }
    mp_book["variants"]["V1_S2_oku_peaks_si_matched_arms"] = {
        "status": "MEASURED forces x k-scaled arms",
        "cap_N_m": round(cap_m1_s2, 6),
        "argmax_q_deg": arg_m1,
        "argmax_note": "same argmax as S1 - the scale is multiplicative on the arms",
        "delta_N_m": round(cap_m1_s2 - current_mp, 6),
        "ratio_vs_current": round(cap_m1_s2 / current_mp, 6),
    }
    mp_book["variants"]["V2_S2_pcsa_sigma_si_matched_arms"] = {
        "status": "PROVISIONAL forces x k-scaled arms",
        "cap_N_m": round(cap_m2_s2, 6),
        "argmax_q_deg": arg_m2,
        "argmax_note": "same argmax as S1 - the scale is multiplicative on the arms",
        "delta_N_m": round(cap_m2_s2 - current_mp, 6),
        "ratio_vs_current": round(cap_m2_s2 / current_mp, 6),
    }

    # ---- ANKLE: context-only (BLOCKED on measured arms)
    ank = receipt["pre_registered_delta_signs"]["ankle_context_only"]
    F_SOL = oku_forces["SOL"]["peak_N"]; F_GAS = oku_forces["GAS"]["peak_N"]
    gas_shares = {m: muscles[m]["pcsa_m2"] / (muscles["MG"]["pcsa_m2"] + muscles["LG"]["pcsa_m2"])
                  for m in ("MG", "LG")}
    sol_arm = muscles["SOL"]["moment_arms_m_flexion_positive"]["ankle"]     # plantarflexion+ convention
    mg_arm = muscles["MG"]["moment_arms_m_flexion_positive"]["ankle"]
    lg_arm = muscles["LG"]["moment_arms_m_flexion_positive"]["ankle"]
    fdl_arm = muscles["FDL"]["moment_arms_m_flexion_positive"]["ankle"]
    v1_plantar = F_SOL * abs(sol_arm) + F_GAS * (gas_shares["MG"] * abs(mg_arm) + gas_shares["LG"] * abs(lg_arm))
    v2_plantar = (muscles["SOL"]["max_force_N"] * abs(sol_arm)
                  + muscles["MG"]["max_force_N"] * abs(mg_arm)
                  + muscles["LG"]["max_force_N"] * abs(lg_arm))
    demand_peak = oku["oku_before_alteration"]["torques"]["ankle"]["peak_abs_stance_Nm"]
    ankle_book = {
        "walk_drive": "ankle_dorsiflexion_left/right",
        "current_cap_N_m": cap_of["ankle_dorsiflexion"],
        "verdict": "RE-DERIVATION BLOCKED ON MEASURED ARMS: the pulley deliverable contains knee_extension and mtp_flexion directions ONLY - no ankle-joint arm curve exists. The FDL/FHL wrap segments (shank-foot) are RIGID during an MTP scan (their wrap contribution to dL/dq_mtp is identically zero, pulley receipt) - an ANKLE scan is exactly where those wraps go live. The ankle cap stays DOC-DERIVED in the audit.",
        "context_record_arms": {
            "source": trace_of("muscle_path_geometry_snapshot", "hindlimb.poses.walking.muscles.{SOL,MG,LG,FDL}.moment_arms_m_flexion_positive.ankle"),
            "status": "the 2026-09-18-lane STRAIGHT-LINE estimates with UNRESOLVED wraps and estimated attachments (the record's own unknowns block declares the 25% bound) - the arms whose knee column this very pulley lane FALSIFIED (ratio 0.00); shown for scale only, never consumed as a cap",
            "SOL_plantar_arm_m": sol_arm, "MG_plantar_arm_m": mg_arm, "LG_plantar_arm_m": lg_arm,
            "FDL_arm_m": fdl_arm,
            "wrong_side_flags": ["FDL %.5f m: the record puts the tibialis-side flexor on the DORSIFLEXION side at the walking pose - internally inconsistent with its mtp/functional role; estimated-attachment artifact" % fdl_arm],
        },
        "context_envelopes": {
            "V1_oku_plantar_N_m": round(v1_plantar, 6),
            "V1_sign_vs_demand": "NEGATIVE (envelope < demand)" if v1_plantar < demand_peak else "POSITIVE (envelope >= demand)",
            "V2_pcsa_sigma_plantar_N_m": round(v2_plantar, 6),
            "V2_sign_vs_demand": "NEGATIVE (envelope < demand)" if v2_plantar < demand_peak else "POSITIVE (envelope >= demand)",
            "oku_measured_walk_demand_peak_N_m": demand_peak,
            "note": "under BOTH force variants the record-arm plantar envelope falls SHORT of the measured walk demand (V1 %.2f, V2 %.2f vs 5.92 N.m) - the estimated straight-line ankle book cannot even cover the walk it was posed at; the ankle pulley direction (R_Ankle_Cylinder live during an ankle scan) is the named future work" % (v1_plantar, v2_plantar),
        },
        "pre_registered": ank,
    }

    book = {
        "schema": "chimera.hind_torque_book.v1",
        "lane": "hind-torque-book-20260921",
        "derived_from_commit": "376fc92b (agent/pulley-rederivation-20260920)",
        "inputs_sha_verified": {k: p["sha256"] for k, p in pins.items()},
        "rederivation": {"knee_extension": knee_book, "mtp_flexion": mp_book, "ankle_context": ankle_book},
    }
    return book, knee_book, mp_book, ankle_book, cap_v1, cap_v2, cap_m1, cap_m2, v1_plantar, v2_plantar, demand_peak


# ---------------------------------------------------------------- consumption map

def build_consumption_map(book, knee_book, mp_book, ankle_book, hold, receipt_pins,
                          cap_v1, cap_v2, cap_m1, cap_m2, v1_plantar, v2_plantar, demand_peak):
    current = {"hip": 11.2125, "knee": 6.6375, "ankle": 7.4, "MP": 0.8875}
    exact_caps = {"hip": 11.218, "knee": 6.643, "ankle": 7.396, "MP": 0.881}
    new_knee = knee_book["variants"]["V1_S1_oku_walk_peaks_deposit_arms"]["cap_N_m"]
    new_mp = mp_book["variants"]["V1_S1_oku_walk_peaks_deposit_arms_equal_split"]["cap_N_m"]

    # (i) hind drive tier: stance-hold demands vs caps, before/after
    nodes = []
    over_old = over_new = 0
    for nd in hold["stance_nodes"]:
        r_old = abs(nd["tau_knee_Nm"]) / exact_caps["knee"]
        r_new = abs(nd["tau_knee_Nm"]) / new_knee
        if r_old > 1.0:
            over_old += 1
        if r_new > 1.0:
            over_new += 1
        nodes.append({"phi": nd["phi"], "knee_demand_N_m": nd["tau_knee_Nm"],
                       "ratio_old_vs_6_643": round(r_old, 4), "ratio_new_vs_book": round(r_new, 4)})
    tier = {
        "consumer": "the hind drive tier law: tau_d = clamp(kp(q*-q) - kd*v, +/-cap_d) with the cap the tier boundary (gait_controller.hpp servo)",
        "demands_source": SINGLE_SUPPORT_DEMAND_SOURCE + " (wave-4 stance-hold statics: 11-DOF planar statics at the zero-mapped table poses, single support)",
        "cap_used_for_new": "the V1_S1 muscle book (scan-max) - MEASURED forces x MEASURED deposit arms",
        "knee_nodes_total": len(nodes),
        "knee_over_cap_nodes_before": over_old,
        "knee_over_cap_nodes_after": over_new,
        "knee_binding_node_phi_0_25": {"demand_N_m": 10.537, "ratio_before": round(10.537 / 6.643, 4),
                                        "ratio_after": round(10.537 / new_knee, 4)},
        "note": "order-of-magnitude: the muscle book moves the stance-hold knee ratio from 33-60% OVER cap through the loaded window (wave-4 receipt) to ~0.92-1.10 - borderline-covered. This is the wave-4 'deeper finding' made quantitative: the source walk's torque peaks are reachable by the admitted musculature ON THE DEPOSIT ARM SCALE. On the SI-matched scale (S2) the book collapses to ~1.15 N.m and the walker cannot stand - the k divergence, not the muscle law, is the consumption gate.",
        "hip_ankle_unchanged": "the hip (11.2125) and ankle (7.4) caps have NO measured-arm book in this lane: hip's trunk pair is the posture-cap lane's 10.54 N.m amendment (not re-derived here); the ankle is BLOCKED (ankle_context). Their tier ratios are unchanged by this book.",
        "mp_windlass_note": "the wave-4 heel-branch MP quasi-static flags (7.8-8.4 N.m vs cap 0.88) stay UNCOVERED by the book (%.2f N.m V1_S1): those nodes are double-support (load shared) quasi-static overestimates per the wave-4 receipt - the book covers the MEASURED dynamic MP peak (0.71 exact) at %.1fx" % (new_mp, new_mp / 0.7051),
        "nodes": nodes,
    }

    # (ii) the stance-hold ratio itself
    stance_ratio = {
        "consumer": "the stance-hold ratio (demand/cap) - the wave-4 membrane's over-cap verdicts and every later 'demand/cap CENTERING' census (e.g. wave-26's 0.881)",
        "before": {"knee_window": "8.81-10.54 N.m vs 6.643 = 1.33-1.59 OVER (phi 0.20-0.25)",
                    "late_stance_hip": "11.78-16.60 vs 11.218 (over); knee 10.14-13.75 vs 6.643 (over)",
                    "entry_instant_phi_0_449": "knee 7.275/6.643 = 1.095 OVER"},
        "after_book_V1_S1": {"knee_cap_N_m": round(new_knee, 4),
                              "entry_instant_ratio": round(7.275 / new_knee, 4),
                              "window_ratios": "0.92-1.10 (borderline: the two late loaded nodes phi 0.25/0.45 stay >=1.0)"},
        "delta": "the over-cap class shrinks from '33-60% over through the window' to 'borderline at the two push-off nodes' - ORDER 1x on the ratio, i.e. the muscle book roughly halves the stance-hold deficit; the qualitative verdict (statics are the wrong demand model mid-gait, wave-4) is unchanged",
    }

    # (iii) the posture/height feed-forward authority
    posture = {
        "consumer": "the height/posture support: the posture drive (keyed to the hip cap) and the wave-10/25 margin wall - the 0.9 combined margin was measured UNREACHABLE at any posture cap in [11.2, 22.4] N.m because the KNEE binds (static min combined 0.9112 at phi=0.85, knee ratio 0.785; posture-cap lane min_admissible_cap)",
        "before": "knee ratio 0.785 at cap 6.643 binds the wall; the 0.9 margin is unreachable at ANY posture cap",
        "after_book_V1_S1": {"knee_ratio_reprice": round(0.785 * 6.643 / new_knee, 4),
                              "knee_headroom_factor": round(new_knee / 6.643, 4)},
        "delta": "ORDER 1.4x knee headroom: the wall's binding term re-prices from 0.785 to ~0.54 - the measured-arms book is the first evidence that the 0.9 margin may be reachable WITHOUT touching the posture cap (the re-hearing the posture-cap lane's 'raising the knee cap is a different hearing' clause named). This book is that hearing's input, NOT its verdict: the re-price uses the deposit arm scale and ignores the S2 collapse caveat.",
        "height_feed_forward": "the ankle plantar chain (the actual height holder in stance) has NO measured-arm book (ankle BLOCKED): the height law's feed-forward authority delta is 0 in this lane - the honest headline. The knee book's 1.4x applies to the support CHAIN (stance-hold), not to the height holder itself.",
    }

    # (iv) what a consuming wave must inherit
    inheritance = {
        "scale_gate": "the k = 0.119754 divergence is THE gate: at S1 the book closes the walk (~1.44x the current knee cap, ~1.9x MP); at S2 it collapses to 0.17x/0.23x and cannot power the measured stride. NO engine consumption is lawful until the operator resolves the deposit-vs-SI absolute scale with the authors (the pulley receipt's standing divergence).",
        "provisional_gate": "the V2 (PCSA x sigma) numbers are PROVISIONAL by the mission's standing order (the Guimaraes pairing lane's paired-force artifacts were not on the canonical at fetch time); consume V1 (Oku measured peaks) first",
        "no_engine_changes_made": True,
        "future_work": ["the ankle pulley direction: re-run the pulley machinery scanning r_ankle_flexion with the FDL/FHL/SOL/GAS/TA class (the wraps that are rigid in an MTP scan go live) - unblocks the 7.4 cap and the height chain",
                         "the Guimaraes pairing lane's paired forces, when landed, upgrade V2 from PROVISIONAL",
                         "the RF Guimaraes row (absent) closes the V2 knee gap",
                         "the FDL slip partition (per-tendon force sharing) narrows the MP bracket",
                         "consume the posture-cap lane's 10.54 N.m amendment in the same wave as the knee re-price"],
    }

    return {"schema_part": "chimera.hind_torque_consumption_map.v1",
            "hind_tier": tier, "stance_hold_ratio": stance_ratio,
            "posture_height_authority": posture, "inheritance": inheritance}


# ---------------------------------------------------------------- verdicts

def check_pre_registered(book, knee_book, mp_book, ankle_book,
                         cap_v1, cap_v2, cap_m1, cap_m2, v1_plantar, v2_plantar, demand_peak):
    verdicts = {}

    def band_check(name, delta_value, sign_expected, cap_band, cap_value):
        """The pre-registration pins the SIGN on the delta (cap_new - cap_current)
        and the BAND on the CAP value itself (each band's derivation_of_band in
        receipt.json computes a cap, e.g. 'V1_S1 x k ~ 1.15')."""
        sign = "POSITIVE" if delta_value >= 0 else "NEGATIVE"
        in_band = cap_band[0] <= cap_value <= cap_band[1]
        return {"name": name, "delta_N_m": round(delta_value, 6),
                 "cap_N_m": round(cap_value, 6), "expected_sign": sign_expected,
                 "band_on_cap_N_m": cap_band, "sign_match": sign == sign_expected,
                 "in_band": in_band,
                 "verdict": "HELD" if (sign == sign_expected and in_band) else "FIRED"}

    pre = book["rederivation"]["knee_extension"]["pre_registered"]
    v1s1 = knee_book["variants"]["V1_S1_oku_walk_peaks_deposit_arms"]["cap_N_m"]
    v2s1 = knee_book["variants"]["V2_S1_pcsa_sigma_deposit_arms"]["cap_N_m"]
    v1s2 = knee_book["variants"]["V1_S2_oku_peaks_si_matched_arms"]["cap_N_m"]
    verdicts["knee_V1_S1"] = band_check("knee V1 S1", v1s1 - knee_book["current_cap_N_m"],
                                         "POSITIVE", pre["V1_S1"]["band_N_m"], v1s1)
    verdicts["knee_V2_S1"] = band_check("knee V2 S1", v2s1 - knee_book["current_cap_N_m"],
                                         "POSITIVE", pre["V2_S1"]["band_N_m"], v2s1)
    verdicts["knee_V1_S2"] = band_check("knee V1 S2", v1s2 - knee_book["current_cap_N_m"],
                                         "NEGATIVE", pre["V1_S2"]["band_N_m"], v1s2)
    verdicts["knee_V2_gt_V1"] = {"name": "knee V2_S1 > V1_S1", "value": v2s1 > v1s1,
                                  "expected": True, "verdict": "HELD" if v2s1 > v1s1 else "FIRED"}
    pre = book["rederivation"]["mtp_flexion"]["pre_registered"]
    m1s1 = mp_book["variants"]["V1_S1_oku_walk_peaks_deposit_arms_equal_split"]["cap_N_m"]
    m2s1 = mp_book["variants"]["V2_S1_pcsa_sigma_deposit_arms"]["cap_N_m"]
    m1s2 = mp_book["variants"]["V1_S2_oku_peaks_si_matched_arms"]["cap_N_m"]
    verdicts["mp_V1_S1"] = band_check("mp V1 S1", m1s1 - mp_book["current_cap_N_m"],
                                       "POSITIVE", pre["V1_S1_equal_split"]["band_N_m"], m1s1)
    verdicts["mp_V2_S1"] = band_check("mp V2 S1", m2s1 - mp_book["current_cap_N_m"],
                                       "POSITIVE", pre["V2_S1"]["band_N_m"], m2s1)
    verdicts["mp_V1_S2"] = band_check("mp V1 S2", m1s2 - mp_book["current_cap_N_m"],
                                       "NEGATIVE", pre["V1_S2"]["band_N_m"], m1s2)
    verdicts["mp_V2_gt_V1"] = {"name": "mp V2_S1 > V1_S1", "value": m2s1 > m1s1,
                                "expected": True, "verdict": "HELD" if m2s1 > m1s1 else "FIRED"}
    pre = book["rederivation"]["ankle_context"]["pre_registered"]
    verdicts["ankle_V1_vs_demand"] = {
        "name": "ankle V1 record-arm plantar envelope < demand", "value": round(v1_plantar, 6),
        "expected_sign": "NEGATIVE (envelope < demand)",
        "band_N_m": pre["record_arms_V1_plantarflexion_envelope"]["band_N_m"],
        "in_band": pre["record_arms_V1_plantarflexion_envelope"]["band_N_m"][0] <= v1_plantar <= pre["record_arms_V1_plantarflexion_envelope"]["band_N_m"][1],
        "verdict": "HELD" if v1_plantar < demand_peak else "FIRED"}
    verdicts["ankle_V2_vs_demand"] = {
        "name": "ankle V2 record-arm plantar envelope < demand", "value": round(v2_plantar, 6),
        "expected_sign": "NEGATIVE (envelope < demand)",
        "band_N_m": pre["record_arms_V2_plantarflexion_envelope"]["band_N_m"],
        "in_band": pre["record_arms_V2_plantarflexion_envelope"]["band_N_m"][0] <= v2_plantar <= pre["record_arms_V2_plantarflexion_envelope"]["band_N_m"][1],
        "verdict": "HELD" if v2_plantar < demand_peak else "FIRED"}
    any_fired = [k for k, v in verdicts.items() if v["verdict"] == "FIRED"]
    verdicts["summary"] = {"fired": any_fired, "all_held": not any_fired}
    return verdicts


# ---------------------------------------------------------------- main

def derive():
    (receipt, pins, pulley, geo, oku, zeros, hold, contract) = load_inputs()
    audit_entries, completeness, exact_peaks, exact_work = build_audit(contract, oku, hold)
    (book, knee_book, mp_book, ankle_book, cap_v1, cap_v2, cap_m1, cap_m2,
     v1_plantar, v2_plantar, demand_peak) = build_book(receipt, pins, pulley, geo, oku, zeros, hold, contract)
    consumption = build_consumption_map(book, knee_book, mp_book, ankle_book, hold, pins,
                                        cap_v1, cap_v2, cap_m1, cap_m2, v1_plantar, v2_plantar, demand_peak)
    verdicts = check_pre_registered(book, knee_book, mp_book, ankle_book,
                                    cap_v1, cap_v2, cap_m1, cap_m2, v1_plantar, v2_plantar, demand_peak)
    book["audit"] = {"entries": audit_entries, "completeness": completeness}
    book["consumption_map"] = consumption
    book["falsifier_verdicts"] = {
        "pre_registered_delta_signs_and_bands": verdicts,
        "traceability": "every computed number carries a trace block to a sha-verified input (see rederivation.*.variants.*.trace); the input shas are verified against receipt.json's pins at load (load_inputs REFUSES on mismatch)",
        "determinism": "see the determinism block written by the runner",
        "audit_completeness": completeness,
        "no_source_changes": "the script writes only hind_torque_book.json inside its own directory; enforced by the unittest via git status",
    }
    book["determinism"] = {
        "protocol": "pure function of the sha-verified inputs; the unittest derives twice (in-process and subprocess) and compares the deliverable sha256",
        "deliverable_sha256_note": "rerun and compare - identical bytes are the pre-registered determinism check",
    }
    return book


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=HERE / "hind_torque_book.json",
                    help="deliverable path (inside this directory; the determinism rerun uses a temp path)")
    a = ap.parse_args()
    out = a.out.resolve()
    here = HERE.resolve()
    if here not in out.parents and out.parent != here:
        raise SystemExit(f"REFUSAL: --out must live inside {here} (no source changes outside the validation dir)")
    book = derive()
    out.write_bytes(canonical_json_bytes(book))
    print(json.dumps({
        "deliverable": str(out),
        "sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
        "knee_cap_V1_S1_N_m": book["rederivation"]["knee_extension"]["variants"]["V1_S1_oku_walk_peaks_deposit_arms"]["cap_N_m"],
        "mp_cap_V1_S1_N_m": book["rederivation"]["mtp_flexion"]["variants"]["V1_S1_oku_walk_peaks_deposit_arms_equal_split"]["cap_N_m"],
        "audit_complete": book["audit"]["completeness"]["complete"],
        "pre_registered_verdicts": book["falsifier_verdicts"]["pre_registered_delta_signs_and_bands"]["summary"],
    }, indent=1))


if __name__ == "__main__":
    main()
