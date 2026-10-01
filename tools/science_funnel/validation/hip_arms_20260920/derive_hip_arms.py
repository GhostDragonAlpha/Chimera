"""Hip moment-arm derivation from the deposit's own geometry (2026-09-20 lane).

Re-runs the k-fill lane's hip-extension context book and the rear-up class C* verdict
with DERIVED -dL/dq moment-arm curves replacing the record's straight-line arm scalars.

Machinery: the pulley_rederivation_20260920 lane's exact -dL/dq derivation
(parse_model / forward_kinematics / path_length), imported UNMODIFIED (F5).
The scanned paths: the k-fill primary class (R_BFL, R_GMax, R_SM, R_ST) plus the
admitted hip crossers (R_AL, R_AM, R_GRA, R_PECT secondary; R_ILI, R_GMed, R_GMin,
R_PIRI inventory). Quarantined hip crossers (R_RF, R_SAR, R_AB) stay named gaps -
their forces are never admitted (the k-fill substitution policy, inherited).

Scan protocol (record.md D1/D2): coordinate hip_flexion_r over the deposit's own
declared range [-1.5708, 1.5708] rad, 2001 samples, all other coordinates at
model-file defaults; r = -dL/dq central differences, step 1e-4 rad (the lane's step);
r > 0 = flexor torque, r < 0 = extensor torque. Windows read off the one curve:
WALK = the Oku before-alteration recorded hip range (consumed from the pinned
derived_numbers.snapshot.json), REAR-UP = the extension side of the declared range
[-1.5708, 0] rad. Cap law unchanged from the k-fill books: cap = max over the window
of SUM F_m |r_m(q)| with the per-muscle per-q sign gate (the ankle book's sign law).
The ONLY consumer-side change in this lane: r_m(q) is the derived curve instead of
the record's straight-line scalar.

Determinism: pure float64 numpy, fixed grids, sort_keys JSON, no clock input.
"""

import hashlib
import importlib
import json
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

LANE_DIR = Path(__file__).resolve().parent
REPO = LANE_DIR.parents[3]
OUT_JSON = LANE_DIR / "hip_arms_book.json"

MACHINERY_DIR = REPO / "tools/science_funnel/validation/pulley_rederivation_20260920"
sys.path.insert(0, str(MACHINERY_DIR))
dp = importlib.import_module("derive_pulley_arms")  # UNMODIFIED (F5)

MODEL_PATH = REPO / "tools/science_funnel/data/wiseman2026/models/Macaque_model.osim"
K_FILL_BOOK = REPO / "tools/science_funnel/validation/k_fill_20260920/k_fill_book.json"
RECORD_GEO = REPO / "tools/science_funnel/validation/muscle_paths_20260918/muscle_path_geometry.json"
DERIVED_NUMBERS = REPO / "tools/science_funnel/validation/hind_torque_book_20260921/inputs/derived_numbers.snapshot.json"
STANDING_POSE = REPO / "tools/science_funnel/validation/standing_pose_20260921/pose.json"

EXPECTED_SHA = {
    "model": (MODEL_PATH, "d5c65cbc0a72bd2d5c2258c6bd018fe850ae25cce6fb07c1f268b91e598c88e9"),
    "k_fill_book": (K_FILL_BOOK, "252105017e5fd87728cea0ec77058c08c7244a66e2a78aeff7841296c57eb55c"),
    "record_geo": (RECORD_GEO, "ca0e890ec69e74d9589c08224d74e74defa53bbc058d371f784175cfca50cb22"),
    "derived_numbers": (DERIVED_NUMBERS, "013810f87a6ca7c1e01916ef7a5454e61e8d0e88f8d6a589fbfdd1514017a173"),
    "standing_pose": (STANDING_POSE, "27e6fd9e95a057af276f63859af65c6a8a4d20a35d0cedf7b495ea9c9ffa0053"),
    "machinery": (MACHINERY_DIR / "derive_pulley_arms.py",
                  "ce93c114c4e89d2726dc4c04b15416518e16208ffadfe14595f9cb14cde5cfa1"),
}

FD_STEP = dp.FD_STEP          # 1e-4 rad, the lane's step
N_SCAN = dp.N_SCAN            # 2001 samples, the lane's scan size
HIP_RANGE_RAD = (-1.5708, 1.5708)   # the deposit's own declared hip_flexion_r range
REARUP_HI_RAD = 0.0           # the rear-up window is the extension side of the declared range
# Wrap-transition artifact flag: |r| beyond the deposit's own longest bone segment
# (the k_forensics_20260921 receipt's mesh_scale_probe femur bbox, 0.172 m) cannot be
# a physical line-of-action distance; flagged and named, never smoothed.
ARTIFACT_THRESHOLD_M = 0.172

CLASS = ["R_BFL", "R_GMax", "R_SM", "R_ST"]
SECONDARY = ["R_AL", "R_AM", "R_GRA", "R_PECT"]
INVENTORY = ["R_ILI", "R_GMed", "R_GMin", "R_PIRI"]
QUARANTINED = ["R_RF", "R_SAR", "R_AB"]
SCAN_LIST = CLASS + SECONDARY + INVENTORY

MODEL_KEY_BY_RNAME = {  # k-fill force-set keys
    "R_BFL": "R_BFL", "R_GMax": "R_GMax", "R_SM": "R_SM", "R_ST": "R_ST",
    "R_AL": "R_AL", "R_AM": "R_AM", "R_GRA": "R_GRA", "R_PECT": "R_PECT",
    "R_ILI": "R_ILI", "R_GMed": "R_GMed", "R_GMin": "R_GMin", "R_PIRI": "R_PIRI",
    "R_RF": "R_RF", "R_SAR": "R_SAR", "R_AB": "R_AB",
}


def sha256_of(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_inputs():
    got = {}
    for key, (path, want) in EXPECTED_SHA.items():
        h = sha256_of(path)
        if h != want:
            raise SystemExit("REFUSED: input %s drifted (got %s want %s)" % (key, h, want))
        got[key] = h
    return got


# ---------------------------------------------------------------------------
# hip-axis geometry (advisory cross-checks; the fd arm stays authoritative)
# ---------------------------------------------------------------------------

def _hip_joint(model):
    return model["joints"]["hip_r"]


def hip_axis_world(model, fk, coordinate):
    """World (axis, origin) of a hip_r TransformAxis: the axis lives in the joint's
    parent offset frame (the mobility frame before rotation)."""
    joint = _hip_joint(model)
    for ax in joint["axes"]:
        if ax["coordinates"][:1] == [coordinate]:
            a = ax["axis"] / float(np.linalg.norm(ax["axis"]))
            poff = dp._joint_frame_offset(joint, "parent", model)
            parent_body = dp._frame_body(joint["sockets"]["parent"], model)
            X = dp.xform_compose(fk[parent_body], poff)
            return X[0] @ a, X[1]
    raise RuntimeError("TransformAxis for %s not found" % coordinate)


def advisory_geo_arm(model, muscle_name, fk, coordinate):
    """Signed perpendicular-distance arm of the hip-spanning line of action, for the
    pre-registered fd-vs-geo cross-check. None when no pelvis-thigh segment exists
    (R_BFL spans pelvis->shank in ONE segment) or the segment is wrap-resolved
    (the slide-term caveat; none of the scanned class paths carries a wrap)."""
    m = model["muscles"][muscle_name]
    purge_wrap_cache(model, muscle_name)
    pts, contacts, _ = dp.resolve_path(model, muscle_name, fk)
    if any(c["engaged"] for c in contacts):
        return None, "wrapped segment - advisory line-of-action not formed"
    joint = _hip_joint(model)
    pair = {dp._frame_body(joint["sockets"]["parent"], model),
            dp._frame_body(joint["sockets"]["child"], model)}
    bodies = [p["body"] for p in m["points"]]
    for i in range(len(bodies) - 1):
        if set((bodies[i], bodies[i + 1])) == pair:
            P, Q = pts[i], pts[i + 1]
            d = Q - P
            dhat = d / float(np.linalg.norm(d))
            axis, origin = hip_axis_world(model, fk, coordinate)
            return float(-dhat @ np.cross(axis, Q - origin)), None
    return None, "no pelvis-thigh joint-spanning segment (single pelvis-to-shank span)"


def purge_wrap_cache(model, muscle_name):
    """Drop the machinery's cached world placement of this muscle's wrap objects.

    derive_pulley_arms._prepare_wrap_world caches world_center/world_R/world_axis
    on first use.  That cache is correct for every pulley-lane scan (knee/ankle/MTP:
    the wrap bodies are rigid at the scanned coordinate) and WRONG for a hip scan of
    any muscle whose wrap body moves with hip_flexion_r (R_ILI's rFemoralneck rides
    thigh_r).  This lane therefore refreshes the placement per call - a consumer-side
    purge, no machinery edit (F5).  No-op for wrap-free paths (the whole class).
    """
    for wref in model["muscles"][muscle_name]["wraps"]:
        w = model["wraps"][wref["wrap_object"]]
        for key in ("world_center", "world_R", "world_axis"):
            w.pop(key, None)


def fd_arm(model, muscle_name, coordinate, state, fk_cache=None):
    """r = -dL/dq, central differences at `state` (missing coordinates at the
    model-file defaults), perturbing `coordinate`."""
    q0 = float(state.get(coordinate, model["coordinates"][coordinate]["default"]))
    st = dict(state)

    def L_at(qv):
        st2 = dict(st)
        st2[coordinate] = qv
        fk = dp.forward_kinematics(model, st2)
        purge_wrap_cache(model, muscle_name)
        return dp.path_length(model, muscle_name, st2, fk=fk)

    Lp = L_at(q0 + FD_STEP)
    Lm = L_at(q0 - FD_STEP)
    return -(Lp - Lm) / (2.0 * FD_STEP)


# ---------------------------------------------------------------------------
# scan
# ---------------------------------------------------------------------------

def scan_muscle(model, muscle, qs):
    """2001-sample -dL/dq scan of hip_flexion_r. A sample that raises inside the
    machinery (endpoint-inside at extreme ROM, wrap pathology) is recorded as
    invalid with its q and the scan stops there - measured, declared, never
    interpolated."""
    n = len(qs)
    arms = np.full(n, np.nan)
    stop = None
    for k, qv in enumerate(qs):
        state = {"hip_flexion_r": float(qv)}
        try:
            purge_wrap_cache(model, muscle)
            Lp = dp.path_length(model, muscle, {**state, "hip_flexion_r": float(qv) + FD_STEP})
            purge_wrap_cache(model, muscle)
            Lm = dp.path_length(model, muscle, {**state, "hip_flexion_r": float(qv) - FD_STEP})
            arms[k] = -(Lp - Lm) / (2.0 * FD_STEP)
        except Exception as exc:  # noqa: BLE001 - recorded, not swallowed
            stop = {"at_index": k, "q_rad": float(qv),
                    "q_deg": round(math.degrees(float(qv)), 4),
                    "reason": "%s: %s" % (type(exc).__name__, exc)}
            break
    valid = int(np.sum(~np.isnan(arms)))
    return arms, valid, stop


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main(argv):
    out_path = Path(argv[1]) if len(argv) > 1 else OUT_JSON
    shas = verify_inputs()
    kfill = json.loads(K_FILL_BOOK.read_text(encoding="utf-8"))
    record_geo = json.loads(RECORD_GEO.read_text(encoding="utf-8"))
    derived_numbers = json.loads(DERIVED_NUMBERS.read_text(encoding="utf-8"))
    standing_pose = json.loads(STANDING_POSE.read_text(encoding="utf-8"))

    forces = {}
    quarantined_gaps = {}
    for name in SCAN_LIST + QUARANTINED:
        key = MODEL_KEY_BY_RNAME[name]
        entry = kfill["derived_force_set"]["muscles"][key]
        if entry["force_N"] is None:
            quarantined_gaps[name] = {
                "status": entry["status"], "force_N": None,
                "why": "the k-fill substitution policy: quarantined rows stay named gaps; "
                       "no force admitted, no arms consumed by any capability sum"}
        else:
            if entry["status"] != "paired_exact_admitted":
                raise SystemExit("REFUSED: %s status %r is not paired_exact_admitted"
                                 % (name, entry["status"]))
            forces[name] = float(entry["force_N"])

    model = dp.parse_model()

    # geometry audit (parse-only facts + the F1 finding)
    wrap_audit = {}
    referenced = set()
    for name in SCAN_LIST + QUARANTINED:
        m = model["muscles"][name]
        for w in m["wraps"]:
            referenced.add(w["wrap_object"])
    def jsonable(v):
        if isinstance(v, np.ndarray):
            return [float(x) for x in v]
        if isinstance(v, dict):
            return {k: jsonable(x) for k, x in v.items()}
        return v

    for wname in sorted(referenced):
        w = dict(model["wraps"][wname])
        w.pop("rotation", None)
        w.pop("world_center", None)
        w.pop("world_R", None)
        w.pop("world_axis", None)
        wrap_audit[wname] = jsonable(w)
    path_audit = {}
    for name in SCAN_LIST + QUARANTINED:
        m = model["muscles"][name]
        path_audit[name] = {
            "points": [{"body": p["body"], "location_m": [float(v) for v in p["location"]]}
                       for p in m["points"]],
            "wraps_referenced": [w["wrap_object"] for w in m["wraps"]],
        }
    f1_class_wraps = {n: path_audit[n]["wraps_referenced"] for n in CLASS}
    f1_no_geometry = all(len(v) == 0 for v in f1_class_wraps.values())

    # windows (consumed from pinned bytes, not hardcoded)
    hip_ok = derived_numbers["oku_before_alteration"]["angles"]["hip"]
    walk_lo = float(hip_ok["min_rad"])
    walk_hi = float(hip_ok["max_rad"])
    node_table = derived_numbers["oku_before_alteration"]["node_table_rad"]["hip"]
    mid_stance_rad = float(node_table[5])  # x = 0.50 of the cycle
    bonds = standing_pose["pose_bonds"]
    hip_flex_at_pose = {
        "hipL_bond_joint_01_02": float(bonds["bond.joint_01_02.flexion"]["theta"]),
        "hipR_bond_joint_01_03": float(bonds["bond.joint_01_03.flexion"]["theta"]),
    }

    qs = np.linspace(HIP_RANGE_RAD[0], HIP_RANGE_RAD[1], N_SCAN)
    grid = {"lo_rad": float(qs[0]), "hi_rad": float(qs[-1]), "samples": N_SCAN,
            "step_rad": float(qs[1] - qs[0])}

    def window_indices(lo, hi):
        return np.where((qs >= lo - 1e-12) & (qs <= hi + 1e-12))[0]

    win_walk = window_indices(walk_lo, walk_hi)
    win_rear = window_indices(HIP_RANGE_RAD[0], REARUP_HI_RAD)
    mid_idx = int(np.argmin(np.abs(qs - mid_stance_rad)))

    directions = {}
    for name in SCAN_LIST:
        arms, valid, stop = scan_muscle(model, name, qs)
        fk0 = dp.forward_kinematics(model, {})
        geo0, geo_reason = advisory_geo_arm(model, name, fk0, "hip_flexion_r")
        fd0 = fd_arm(model, name, "hip_flexion_r", {})
        add0 = fd_arm(model, name, "hip_adduction_r", {})
        finite = arms[~np.isnan(arms)]
        art_idx = np.where(~np.isnan(arms) & (np.abs(arms) > ARTIFACT_THRESHOLD_M))[0]
        directions[name] = {
            "artifact_flag": {
                "threshold_m": ARTIFACT_THRESHOLD_M,
                "basis": "the deposit's longest bone segment (k_forensics_20260921 "
                         "mesh_scale_probe femur bbox 0.172 m); a |moment arm| beyond it "
                         "cannot be physical - flagged and named, never smoothed",
                "count": int(len(art_idx)),
                "samples": [{"index": int(i), "q_deg": round(math.degrees(float(qs[int(i)])), 4),
                             "arm_m": float(arms[int(i)])} for i in art_idx],
            },
            "muscle": name,
            "coordinate": "hip_flexion_r",
            "scan_range_rad": [HIP_RANGE_RAD[0], HIP_RANGE_RAD[1]],
            "samples": N_SCAN,
            "valid_samples": valid,
            "scan_stop": stop,
            "arm_samples_m": [float(v) for v in arms],
            "r_min_m": float(np.min(finite)),
            "r_max_m": float(np.max(finite)),
            "r_min_at_deg": round(math.degrees(float(qs[int(np.nanargmin(arms))])), 4),
            "r_max_at_deg": round(math.degrees(float(qs[int(np.nanargmax(arms))])), 4),
            "negative_samples_extension": int(np.sum(finite < 0.0)),
            "positive_samples_flexion": int(np.sum(finite > 0.0)),
            "advisory_geo_arm_at_default_m": geo0,
            "advisory_geo_reason": geo_reason,
            "fd_arm_at_default_m": float(fd0),
            "fd_vs_geo_at_default_maxabsdiff_m": (abs(float(fd0) - geo0)
                                                  if fd0 is not None and geo0 is not None else None),
            "advisory_adduction_axis_fd_arm_at_default_m": float(add0),
        }

    # P0 internal anatomical sign check at the model default pose
    p0 = {n: directions[n]["fd_arm_at_default_m"] for n in SCAN_LIST}
    p0_verdict = {
        "R_ILI_positive_flexor": bool(p0["R_ILI"] > 0.0),
        "class_negative_extensor": bool(all(p0[n] < 0.0 for n in CLASS)),
        "held": bool(p0["R_ILI"] > 0.0 and all(p0[n] < 0.0 for n in CLASS)),
    }

    # capability books (D3/D4: class fixed, cap law fixed, sign gate per muscle per q)
    def capability(window, names, mask_artifacts=False):
        idx = np.array(window, dtype=int)
        cap = None
        arg = None
        per_q_signouts = {n: 0 for n in names}
        curve = []
        for k in idx:
            tau = 0.0
            parts = {}
            for n in names:
                r = directions[n]["arm_samples_m"][int(k)]
                if mask_artifacts and (directions[n]["artifact_flag"]["count"] > 0):
                    for a in directions[n]["artifact_flag"]["samples"]:
                        if a["index"] == int(k):
                            r = float("nan")
                            break
                if math.isnan(r):
                    parts[n] = None
                    continue
                if r < 0.0:      # extensor sign at this q
                    c = forces[n] * (-r)
                    parts[n] = c
                    tau += c
                else:
                    parts[n] = 0.0
                    per_q_signouts[n] += 1
            curve.append((int(k), tau))
            if cap is None or tau > cap:
                cap, arg = tau, int(k)
        per = []
        for n in names:
            r = directions[n]["arm_samples_m"][arg]
            if mask_artifacts:
                for a in directions[n]["artifact_flag"]["samples"]:
                    if a["index"] == arg:
                        r = float("nan")
                        break
            c = forces[n] * (-r) if (not math.isnan(r) and r < 0.0) else 0.0
            per.append({"muscle": n, "arm_mm_at_argmax": round(float(r) * 1e3, 6),
                        "force_N": forces[n], "contribution_N_m": round(float(c), 9),
                        "sign_gated_out": bool(c == 0.0)})
        return {"cap_N_m": round(float(cap), 9),
                "argmax_q_deg": round(math.degrees(float(qs[arg])), 4),
                "argmax_index": arg,
                "window_grid_indices": [int(window[0]), int(window[-1])],
                "per_muscle_at_argmax": per,
                "sign_gated_out_sample_counts": per_q_signouts,
                "artifacts_masked": bool(mask_artifacts),
                "envelope_samples_N_m": [
                    {"q_deg": round(math.degrees(float(qs[k])), 4), "tau_N_m": round(float(t), 9)}
                    for k, t in curve[::5]]}

    book = {
        "schema": "chimera.hip_arms.v1",
        "lane": "hip-arms-20260920",
        "inputs": {
            "sha256": shas,
            "base_commit": "a13a4d87898dc70b4b0344303d5ee823caae49a2",
            "machinery": "pulley_rederivation_20260920/derive_pulley_arms.py imported UNMODIFIED",
        },
        "method": {
            "fd_step_rad": FD_STEP,
            "scan_samples": N_SCAN,
            "grid_deg": grid,
            "scan_protocol": "hip_flexion_r over the deposit's own declared range, all other "
                             "coordinates at model-file defaults (the pulley lane's protocol); "
                             "r = -dL/dq central differences; r<0 = extensor, r>0 = flexor",
            "sign_gate": "per-muscle per-q (the ankle book's sign law): a class muscle "
                         "contributes F*|r| only where its derived arm is NEGATIVE about "
                         "hip_flexion_r (extension)",
            "windows": {
                "walk": {"lo_rad": walk_lo, "hi_rad": walk_hi,
                         "source": "derived_numbers.snapshot.json oku_before_alteration.angles.hip "
                                   "min_rad/max_rad (sha-pinned)"},
                "rearup": {"lo_rad": HIP_RANGE_RAD[0], "hi_rad": REARUP_HI_RAD,
                           "source": "the extension side of the deposit's own declared "
                                     "hip_flexion_r range; standing-pose-of-record hip "
                                     "flexions (pose.json pose_bonds: %r) sit on the FLEXION "
                                     "side of neutral - the anchor quoted in the prereg was "
                                     "the pose_v2 maximin-rest values (-0.165336845485 / "
                                     "-0.163993995356 rad), a PREREG SLIP recorded in the "
                                     "receipt; the window law itself (extension side of the "
                                     "declared range) is unchanged and consumes no anchor"
                                     % (hip_flex_at_pose,)},
            },
            "mid_stance_evaluation": {"q_rad": mid_stance_rad,
                                      "source": "oku node_table_rad.hip x=0.50 entry",
                                      "grid_index": mid_idx,
                                      "q_used_rad": float(qs[mid_idx])},
        },
        "geometry_audit": {
            "f1_class_wraps": f1_class_wraps,
            "f1_no_geometry_class": bool(f1_no_geometry),
            "paths": path_audit,
            "referenced_wraps_audited": wrap_audit,
        },
        "directions": directions,
        "p0_anatomical_sign_check": {
            "arm_m_at_mid_stance_node": {n: float(p0[n]) for n in SCAN_LIST},
            "verdict": p0_verdict,
        },
        "forces_N": forces,
        "named_gaps": quarantined_gaps,
    }

    hip_book = {
        "class": CLASS,
        "artifact_note": "the class paths are wrap-free (geometry_audit.f1_no_geometry_class); "
                         "asserted artifact-free below, so the primary cap consumes no "
                         "flagged sample",
        "forces_N": {n: forces[n] for n in CLASS},
        "walk_window": capability(win_walk, CLASS),
        "rearup_window": capability(win_rear, CLASS),
        "mid_stance_x050": {
            "q_used_deg": round(math.degrees(float(qs[mid_idx])), 4),
            "per_muscle": [
                {"muscle": n,
                 "derived_arm_mm": round(float(directions[n]["arm_samples_m"][mid_idx]) * 1e3, 6),
                 "force_N": forces[n],
                 "contribution_N_m": round(forces[n] * (-float(directions[n]["arm_samples_m"][mid_idx]))
                                           if directions[n]["arm_samples_m"][mid_idx] < 0 else 0.0, 9)}
                for n in CLASS],
            "sum_N_m": round(sum(forces[n] * (-float(directions[n]["arm_samples_m"][mid_idx]))
                                 for n in CLASS
                                 if directions[n]["arm_samples_m"][mid_idx] < 0), 9),
        },
    }
    book["hip_book_derived"] = hip_book
    class_artifacts = {n: directions[n]["artifact_flag"]["count"] for n in CLASS}
    assert all(v == 0 for v in class_artifacts.values()), \
        "artifact sample inside a wrap-free class curve: %r" % class_artifacts

    # secondary + inventory readings (named, never in the primary class)
    book["secondary_named"] = {
        "class": SECONDARY,
        "note": "the k-fill book's adductor secondary, same standing: named reading, "
                "not in the primary class",
        "walk_window": capability(win_walk, SECONDARY),
        "rearup_window": capability(win_rear, SECONDARY),
    }
    book["inventory_non_class"] = {
        "class": INVENTORY,
        "note": "the remaining admitted hip crossers; named reading only. R_ILI's curve "
                "rides the rFemoralneck wrap (wrap body thigh_r MOVES in a hip scan - the "
                "machinery's per-call cache purge is applied); any residual wrap-transition "
                "sample is flagged in the direction's artifact_flag and its excluded-mask "
                "reading is reported beside the as-measured one",
        "walk_window_as_measured": capability(win_walk, INVENTORY),
        "walk_window_artifacts_excluded": capability(win_walk, INVENTORY, mask_artifacts=True),
        "rearup_window_as_measured": capability(win_rear, INVENTORY),
        "rearup_window_artifacts_excluded": capability(win_rear, INVENTORY, mask_artifacts=True),
    }

    # side-by-side comparison (F2: no constant moved except the arms)
    kfill_ctx = kfill["hip_extension_context"]
    record_arms = {row["muscle"]: float(row["record_hip_arm_m"])
                   for row in kfill_ctx["extensors"]}
    kfill_forces = {row["muscle"]: float(row["force_N"]) for row in kfill_ctx["extensors"]}
    mid_stance = hip_book["mid_stance_x050"]
    comp_rows = []
    for n in CLASS:
        r_der = float(directions[n]["arm_samples_m"][mid_idx]) * 1e3
        r_rec = record_arms[n] * 1e3
        force_full = float(kfill["derived_force_set"]["muscles"][MODEL_KEY_BY_RNAME[n]]["force_N"])
        comp_rows.append({
            "muscle": n,
            "record_arm_mm": round(r_rec, 6),
            "derived_arm_mm_at_mid_stance": round(r_der, 6),
            "ratio_derived_over_record": round(r_der / r_rec, 6),
            "force_N_kfill_context_row_display": kfill_forces[n],
            "force_N_kfill_force_set_full_precision": force_full,
            "force_N_this_lane": forces[n],
            "force_byte_equal_to_force_set": bool(force_full == forces[n]),
            "note": "the k-fill context rows carry 6-dp display roundings of the same "
                    "force set; byte equality is asserted against the force set itself",
        })
    derived_same_pose = mid_stance["sum_N_m"]
    book["comparison"] = {
        "kfill_context_book_consumed": {
            "class": "the record's own hip_extensors functional group at the walking pose",
            "extensors": kfill_ctx["extensors"],
            "hip_extension_context_N_m": kfill_ctx["hip_extension_context_N_m"],
            "adductor_secondary_named_sum_N_m": kfill_ctx["adductor_secondary_named"]["sum_N_m"],
            "arm_caveat": kfill_ctx["arm_caveat"],
        },
        "derived_same_pose_mid_stance_sum_N_m": derived_same_pose,
        "per_muscle_mid_stance": comp_rows,
        "forces_byte_equal_to_kfill_set": all(r["force_byte_equal_to_force_set"] for r in comp_rows),
        "constants_moved": "NONE except the arms (F2): forces byte-equal, demand C* fixed, "
                           "class fixed, cap law fixed",
    }

    # the rear-up C* verdict, re-adjudicated
    prior = kfill["rearup_verdict"]
    primary_cap = hip_book["rearup_window"]["cap_N_m"]
    conservative_caps = {
        "knee_extension": float(kfill["capabilities_deposit_arms"]["knee_extension"]["cap_N_m"]),
        "ankle_plantarflexion": float(kfill["capabilities_deposit_arms"]["ankle_plantarflexion"]["cap_N_m"]),
        "ankle_dorsiflexion": float(kfill["capabilities_deposit_arms"]["ankle_dorsiflexion"]["cap_N_m"]),
        "mtp_flexion": float(kfill["capabilities_deposit_arms"]["mtp_flexion"]["cap_N_m"]),
    }
    conservative_max = max(conservative_caps.values())
    covered_iff_txt = prior["covered_iff"]
    cstar_top = 33.6
    assert "33.6" in covered_iff_txt, "C* top not parseable from the pinned book"
    primary_inside = bool(22.4 < primary_cap <= cstar_top)
    book["rearup_verdict"] = {
        "class": prior["class"],
        "covered_iff": covered_iff_txt,
        "primary_definition": "max over the DERIVED hip book at the REAR-UP window "
                              "(extension side of the deposit's declared hip range), "
                              "sign-gated, k-fill forces",
        "primary_max_capability_N_m": primary_cap,
        "primary_owner": "hip_extension_derived_rearup",
        "primary_inside_C_star_class": primary_inside,
        "conservative_definition": prior["conservative_definition"],
        "conservative_max_capability_N_m": conservative_max,
        "conservative_owner": max(conservative_caps, key=conservative_caps.get),
        "conservative_caps_N_m": conservative_caps,
        "conservative_covered": bool(conservative_max > cstar_top),
        "covered": bool(primary_cap > cstar_top),
        "verdict": "COVERED" if primary_cap > cstar_top else "NOT COVERED",
        "prior_verdict": {"verdict": prior["verdict"],
                          "primary_max_capability_N_m": prior["primary_max_capability_N_m"],
                          "primary_owner": prior["primary_owner"]},
        "verdict_changed": bool((primary_cap > cstar_top) != (prior["primary_max_capability_N_m"] > cstar_top)),
        "walk_window_reading": {
            "cap_N_m": hip_book["walk_window"]["cap_N_m"],
            "argmax_q_deg": hip_book["walk_window"]["argmax_q_deg"],
            "note": "the walk-side capability reading, reported not consumed"},
    }

    out_path.write_text(json.dumps(book, indent=1, sort_keys=True), encoding="utf-8")
    print("wrote", out_path)
    print("sha256", sha256_of(out_path))
    print("F1 no-geometry on the class:", f1_no_geometry)
    print("P0 anatomical sign check:", json.dumps(p0_verdict))
    for n in CLASS:
        d = directions[n]
        print("%-8s r in [%9.4f, %9.4f] mm  neg/ext %4d  pos/flex %4d  valid %d  artifacts %d"
              % (n, d["r_min_m"] * 1e3, d["r_max_m"] * 1e3,
                 d["negative_samples_extension"], d["positive_samples_flexion"],
                 d["valid_samples"], d["artifact_flag"]["count"]))
    for n in SECONDARY + INVENTORY:
        d = directions[n]
        print("%-8s r in [%9.4f, %9.4f] mm  valid %d  artifacts %d"
              % (n, d["r_min_m"] * 1e3, d["r_max_m"] * 1e3,
                 d["valid_samples"], d["artifact_flag"]["count"]))
    print("hip book mid-stance x0.50: derived %.6f N.m vs k-fill record-arm book %.6f N.m"
          % (derived_same_pose, kfill_ctx["hip_extension_context_N_m"]))
    print("hip book walk-window cap %.6f N.m @ %.4f deg"
          % (hip_book["walk_window"]["cap_N_m"], hip_book["walk_window"]["argmax_q_deg"]))
    print("hip book rear-up-window cap %.6f N.m @ %.4f deg"
          % (hip_book["rearup_window"]["cap_N_m"], hip_book["rearup_window"]["argmax_q_deg"]))
    print("REAR-UP VERDICT:", book["rearup_verdict"]["verdict"],
          "(prior:", prior["verdict"], "at %.6f N.m)" % prior["primary_max_capability_N_m"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
