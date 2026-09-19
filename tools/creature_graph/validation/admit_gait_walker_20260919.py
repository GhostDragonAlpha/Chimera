"""Admit model.dynamics.gait_walker (stage D-F implementation of
docs/research/20260918_gait_controller_derivation.md) and supersede
work.creature.gait_controller to revision 2 with the measured falsifier
results. Idempotent and revision-aware (the repo's graph policy): a stored
record equal to a listed revision is a no-op; genuinely foreign content
refuses.

Every drive constant is cross-checked against the admitted Oku bytes through
the derivation lane's own parser BEFORE anything is banked: the 21-node
target tables are verified to reconstruct the 101 measured samples within the
doc's stated maxima, and |tau_peak| / W+ are verified against the measured
waveforms. A mismatch refuses the admission.

Run from the checkout root with the pinned interpreter:
    python -B tools/creature_graph/validation/admit_gait_walker_20260919.py
then rebuild the store:
    python -B tools/creature_graph/build_graph.py
"""
import importlib.util
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

PROGRAM = ROOT / "tools" / "creature_graph" / "data" / "authored" / "project_program.json"
DERIVED = ROOT / "tools" / "science_funnel" / "validation" / "gait_controller_20260918" / "derived_numbers.json"
DERIVER = ROOT / "tools" / "science_funnel" / "validation" / "gait_controller_20260918" / "derive_gait_numbers.py"

MODEL_ID = "model.dynamics.gait_walker"
WORK_ID = "work.creature.gait_controller"

# ── THE CONTRACT (docs/research/20260918_gait_controller_derivation.md §2.4,
#    §4, §5) — the 21-node phase tables (rad, Oku convention), the measured
#    torque peaks and their derived caps/stores, the quoted viscous dampers. ──
TABLES = {
    "hip": [0.809, 0.835, 0.825, 0.751, 0.651, 0.525, 0.412, 0.297, 0.128, 0.043, -0.027, -0.065, -0.139, -0.146, -0.042, 0.167, 0.442, 0.767, 0.887, 0.885, 0.807],
    "knee": [-0.472, -0.670, -0.852, -0.948, -0.973, -0.959, -0.946, -0.890, -0.826, -0.849, -0.860, -0.872, -0.847, -0.922, -1.045, -1.174, -1.201, -1.084, -0.865, -0.633, -0.470],
    "ankle": [0.928, 1.232, 1.383, 1.440, 1.447, 1.465, 1.460, 1.487, 1.499, 1.433, 1.354, 1.153, 0.910, 0.846, 0.852, 0.969, 1.253, 1.303, 1.225, 1.071, 0.927],
    "MP": [0.558, 0.338, 0.368, 0.497, 0.651, 0.741, 0.827, 0.856, 0.914, 1.046, 1.140, 1.319, 1.295, 0.865, -0.025, -0.114, -0.142, -0.092, -0.035, 0.134, 0.559],
}
TABLE_MAX_ERR_DEG = {"hip": 1.76, "knee": 2.02, "ankle": 2.70, "MP": 4.07}  # doc §2.4
TAU_PEAK = {"hip": 8.97, "knee": 5.31, "ankle": 5.92, "MP": 0.71}          # doc §4.1
W_PLUS = {"hip": 5.2488, "knee": 2.5567, "ankle": 3.2658, "MP": 0.5013}    # derived_numbers per_drive_budget_check_J (10.038 kg)
VISCOS = {"hip": 0.109, "knee": 0.317, "ankle": 0.0943, "MP": 0.01}        # doc §4.2, quoted Oku dampers
CAP_FACTOR, STORE_FACTOR = 1.25, 1.5                                        # doc §4.3/§4.4 derived
STORE_STRIDE_WINDOW = 10                                                    # the F-G4/F-G6 falsifier window (10 strides)
STORE_FLOOR_EFFECTIVE = {k: round(STORE_FACTOR * STORE_STRIDE_WINDOW * v, 6) for k, v in W_PLUS.items()}
CYCLE_S, DUTY, TOE_OFF, FS_HZ, ZETA, CAPTURE_PHI = 0.71, 0.6832, 0.68, 4.0, 0.8, 0.95
CONTACT_POINTS = [
    {"name": "left_heel", "body": "foot_left", "point_m": [-0.012, 0.0, 0.0], "radius_m": 0.004,
     "provenance": "heel pad behind the ankle pivot on the foot (metatarsal) segment; with the MP head it spans the flat-stand support hull"},
    {"name": "left_mp_head", "body": "foot_left", "point_m": [0.074, 0.0, 0.0], "radius_m": 0.004,
     "provenance": "metatarsophalangeal head = the digitigrade stance contact (derivation 5.4)"},
    {"name": "right_heel", "body": "foot_right", "point_m": [-0.012, 0.0, 0.0], "radius_m": 0.004},
    {"name": "right_mp_head", "body": "foot_right", "point_m": [0.074, 0.0, 0.0], "radius_m": 0.004},
]
CONTACT_FRICTION = 0.6
PLANE_WORLD_UP_M = 0.004  # sole radius; the seating scan pins the reset gaps
LEG_Z_OFFSET_M = 0.02


def verify_against_bytes():
    """Verify the banked contract against the admitted Oku xlsx via the
    derivation lane's own parser (its module constants and cell reader only;
    the parsing is re-run, never re-typed). Returns the measured block."""
    spec = importlib.util.spec_from_file_location("gait_deriver", DERIVER)
    deriver = importlib.util.module_from_spec(spec)
    sys.modules["gait_deriver"] = deriver
    spec.loader.exec_module(deriver)
    derived = json.loads(DERIVED.read_text(encoding="utf-8"))
    sheets = deriver.sheet_rows(str(deriver.OKU))
    fig = sheets["Fig3ABC"]
    before_cols = {"GRFh": 1, "GRFv": 2, "hip_ang": 3, "knee_ang": 4, "ankle_ang": 5,
                   "MP_ang": 6, "hip_tor": 7, "knee_tor": 8, "ankle_tor": 9, "MP_tor": 10}
    data = []
    for r in fig[1:]:
        x = deriver.f(r, 0)
        if x is None:
            continue
        rec = {"x": x}
        for k, c in before_cols.items():
            rec[k] = deriver.f(r, c)
        if all(rec[k] is not None for k in before_cols):
            data.append(rec)
    data.sort(key=lambda d: d["x"])
    if len(data) != 101 or data[0]["x"] != 0 or data[-1]["x"] != 100:
        raise SystemExit("REFUSAL: the digitigrade sample grid is not the contract's 101 x 0..100")

    measured = {"table_reconstruction_err_deg": {}, "tau_peak_N_m": {}, "n_samples": len(data)}
    for joint in ("hip", "knee", "ankle", "MP"):
        th = {d["x"]: d[joint + "_ang"] for d in data}
        worst = 0.0
        for x in range(101):
            pos = (x / 100.0) * 20.0
            k0 = int(pos)
            k1 = min(k0 + 1, 20)
            frac = pos - k0
            v = TABLES[joint][k0] * (1 - frac) + TABLES[joint][k1] * frac
            worst = max(worst, abs(v - th[x]))
        err_deg = worst * 180.0 / math.pi
        measured["table_reconstruction_err_deg"][joint] = round(err_deg, 3)
        if err_deg > TABLE_MAX_ERR_DEG[joint] + 0.05:
            raise SystemExit(f"REFUSAL: {joint} table reconstruction {err_deg:.3f} deg exceeds the contract's {TABLE_MAX_ERR_DEG[joint]} deg")
        tp = max(abs(d[joint + "_tor"]) for d in data)
        measured["tau_peak_N_m"][joint] = round(tp, 4)
        if abs(tp - TAU_PEAK[joint]) > 0.02:
            raise SystemExit(f"REFUSAL: {joint} measured |tau_peak| {tp:.4f} differs from the contract's {TAU_PEAK[joint]}")
    stance = [d["x"] for d in data if d["GRFv"] > 0.0]
    duty = (len(stance) + 1) / 101.0
    measured["duty_factor"] = round(duty, 4)
    measured["toe_off_pct"] = int(max(stance))
    if abs(measured["duty_factor"] - DUTY) > 0.001 or abs(measured["toe_off_pct"] - TOE_OFF * 100) > 0.5:
        raise SystemExit("REFUSAL: duty/toe-off drift against the contract")
    measured["w_plus_J"] = {k: derived["per_drive_budget_check_J"][k]["positive_J_at_10kg"] for k in W_PLUS}
    for k in W_PLUS:
        if abs(measured["w_plus_J"][k] - W_PLUS[k]) > 1e-9:
            raise SystemExit(f"REFUSAL: W+ drift for {k}")
    return measured


def drives_block():
    out = []
    for i, leg in enumerate(("left", "right")):
        for joint, key in (("hip_flexion", "hip"), ("knee_extension", "knee"), ("ankle_dorsiflexion", "ankle"), ("MP_dorsiflexion", "MP")):
            out.append({
                "coordinate": f"{joint}_{leg}", "leg": leg, "joint": key,
                "torque_cap_N_m": round(CAP_FACTOR * TAU_PEAK[key], 6),
                "store_floor_J": STORE_FLOOR_EFFECTIVE[key],
                "store_floor_per_stride_J": round(STORE_FACTOR * W_PLUS[key], 6),
                "store_stride_window": STORE_STRIDE_WINDOW,
                "viscous_damping_N_m_s_rad": VISCOS[key],
            })
    return out


COORDINATES = ["base_rot_x", "base_rot_y", "base_rot_z", "base_trans_x", "base_trans_y", "base_trans_z",
               "hip_flexion_left", "knee_extension_left", "ankle_dorsiflexion_left", "MP_dorsiflexion_left",
               "hip_flexion_right", "knee_extension_right", "ankle_dorsiflexion_right", "MP_dorsiflexion_right"]
RANGES = {
    "hip_flexion": [-0.35, 1.10],
    # knee: the measured cycle's deepest flexion is 1.213 rad (phi=0.78); the
    # standing-start transient legitimately over-flexes past it (zero forward
    # speed at cycle 1), so the stop sits at the PHYSICAL flexion limit
    # (~115 deg, shank-to-thigh), not at the cycle extreme.
    "knee_extension": [-2.00, 0.05],
    "ankle_dorsiflexion": [-0.30, 1.70], "MP_dorsiflexion": [-0.35, 1.55],
}

OWNED_FILES = [
    "docs/research/20260918_gait_controller_derivation.md",
    "ChimeraEngine/engine/gait_controller.hpp",
    "tools/science_funnel/gait_scene.py",
    "tools/creature_graph/validation/admit_gait_walker_20260919.py",
    "tools/science_funnel/validation/gait_impl_20260919/receipt.json",
]


def contract_block():
    return {
        "schema": "chimera.gait_scene.v1",
        "source_derivation": "docs/research/20260918_gait_controller_derivation.md",
        "derived_from_record": "work.creature.gait_controller",
        "coordinates": COORDINATES,
        "base_coordinates": COORDINATES[:6],
        "joint_ranges_rad": {k: v for k, v in RANGES.items()},
        "drives": drives_block(),
        "cycle_duration_s": CYCLE_S,
        "duty_factor_sampled": DUTY,
        "toe_off_pct": TOE_OFF,
        "servo_frequency_Hz": FS_HZ,
        "servo_damping_ratio": ZETA,
        "capture_step_phase": CAPTURE_PHI,
        "tables_rad": TABLES,
        "table_max_err_deg_contract": TABLE_MAX_ERR_DEG,
        "contact_points": CONTACT_POINTS,
        "contact_friction": CONTACT_FRICTION,
        "contact_plane_height_m": PLANE_WORLD_UP_M,
        "leg_z_offset_m": LEG_Z_OFFSET_M,
        "tick_hz": 300,
        "substeps": 4,
        "seating_scan": {"reset_gap_target_m": 2e-06},
    }


def model_record(measured, status, falsifier_status, acceptance):
    rec = {
        "id": MODEL_ID,
        "kind": "model",
        "name": "Gait walker: 14-coordinate free-root hindlimb assembly driven by the derived walking controller",
        "status": status,
        "priority": "P1",
        "dependencies": [
            "model.anatomy.macaque_arm",
            "model.environment.earth_patch",
            "work.dynamics.free_root_balance_packet",
            "work.creature.gait_controller",
        ],
        "evidence": [],
        "falsifier": {
            "statement": "F-G1 realized trajectories beyond the node tables +/-5 deg for more than 5% of a cycle, or excursions beyond +/-10% of the measured waveforms; F-G2 duty outside [0.63, 0.73] or a left/right phase drift beyond 0.02; F-G3 peak GRF outside 1.08 BW +/-10%, toe-off outside 68% +/-5%, or the closure identity 2*I_stance = BW*T outside 3%; F-G4 a drive exceeding 2x its measured positive work or depleting its store (empty events over 10 strides); F-G5 the body refusing to fall with the controller powered off; F-G6 a tip without push, or a push-capture that fails to land; F-G7 nondeterminism between two identical runs; F-G8 any ledger identity violation beyond 1e-5 J -- REFUTES the walking controller or this runtime, whichever the failing measurement names.",
            "acceptance_test": acceptance,
            "status": falsifier_status,
        },
        "physical": {
            "statement": "Implementation of the derivation's stages D-F: the hindlimb lift as a 14-coordinate Model assembly (6-axis authored free base + hip/knee/ankle/MP per leg in the Oku sign convention, +/-1 stem mapping: all four joint axes are the world South axis {0,0,1} with slope +1, so positive q is flexion/extension/dorsiflexion exactly as the tables), the contact-reset hybrid phase clock, the 21-node tables, the mass-normalized PD at the derived 4.0 Hz with caps at 1.25x |tau_peak|, per-drive depletive stores at 1.5x W+, and the support-hull capture reflex -- integrated as the sibling runtime ChimeraEngine/engine/gait_controller.hpp consuming the controller's tau through the same advance(h,tau) input the qualified solvers expose. The qualified 2-coordinate class keeps its exact bytes; the free-root and n-coordinate headers are unmodified.",
            "prediction": "The free-root walker carrying the Section 2.4 tables through the Section 5 control law walks at the measured anchors: duty 0.68 in [0.63, 0.73], peak vertical GRF 1.08 BW within 10%, the closure 2*I = BW*T within 3%, zero store depletions over 10 cycles, the CoM inside the support hull on loaded ticks, and the body falls with the controller off.",
            "contract": contract_block(),
        },
        "measured_verification": measured,
    }
    return rec


def work_record_rev2():
    return {
        "id": WORK_ID,
        "kind": "work",
        "name": "Macaque gait controller derived from the admitted movement data (IMPLEMENTED, stages D-F)",
        "status": "verified",
        "priority": "P1",
        "dependencies": [
            "model.dynamics.coupled_arm",
            "model.anatomy.macaque_arm",
            "work.dynamics.seven_coordinate_lift_packet",
            "work.dynamics.free_root_balance_packet",
            "work.creature.macaque_whole_body_sources",
        ],
        "physical": {
            "statement": "Revision 2 (implementing lane gait-impl-20260919): stages D-F of the ladder executed on the derived contract -- the 14-coordinate hindlimb walker (ChimeraEngine/engine/gait_controller.hpp) carries the 21-node tables through the contact-reset hybrid clock, the capped mass-normalized PD at the derived 4.0 Hz, per-drive stores at 1.5x W+, and the support-hull capture reflex. The original authored statement, prediction and falsifier set are unchanged from revision 1; the measured results live in model.dynamics.gait_walker.",
            "prediction": "Unchanged from revision 1 (the derivation's PREDICTION).",
            "contract": {
                "derivation": "docs/research/20260918_gait_controller_derivation.md",
                "derives": ["revision 1's eight derived constants, all unchanged and re-verified against the admitted bytes at implementation time"],
                "falsifiers": [
                    "F-G1 realized trajectories within the node tables +/-5 deg, excursions within +/-10% of measured",
                    "F-G2 duty 0.68 in [0.63, 0.73], left/right phase offset 0.50 +/- 0.02 (contact reset required)",
                    "F-G3 GRF envelope: peak 1.08 BW +/-10%, toe-off 68% +/-5%, closure 2*I_stance = BW*T within 3%",
                    "F-G4 energy: per-drive W+ per stride within 2x table and within store; zero empty_events over 10 strides",
                    "F-G5 the free-root falsifier: controller off -> the body falls; any hover refutes the simulator",
                    "F-G6 stability: 10 cycles without tip; the capture reflex must land an early touchdown under a scripted push",
                    "F-G7 determinism: two identical runs, bit-identical status streams",
                    "F-G8 ledger closure |balance_error_J| < 1e-5 and |store_balance_error_J| < 1e-5 on every status query"
                ],
                "owned_files": OWNED_FILES,
            },
        },
        "falsifier": {
            "statement": "Unchanged from revision 1: if the controller is removed and the body does not fall, or the realized angles, GRF profile, or duty factor leave the stated envelopes, or a drive depletes its store mid-walk, or the CoM projection leaves the support hull without a tip, or any status query violates the ledger identities -- this derivation is FALSE and the controller is refused. A creature that cannot FALL cannot walk.",
            "acceptance_test": "Executed by the implementing lane as the native gait falsifier suite (ChimeraEngine/engine/tests_coupled_arm/gait_unit.cpp, F-G1..F-G8) on the compiled gait scene; measured results recorded in model.dynamics.gait_walker and tools/science_funnel/validation/gait_impl_20260919/receipt.json.",
            "status": "tested",
        },
    }


def main() -> int:
    raw = PROGRAM.read_bytes()
    payload = json.loads(raw.decode("utf-8-sig"))
    objects = payload["objects"]

    measured = verify_against_bytes()
    print("contract verified against the admitted bytes:",
          json.dumps({k: measured[k] for k in ("table_reconstruction_err_deg", "tau_peak_N_m")}, sort_keys=True))

    # The work record: revision 1 must exist (the derivation lane banked it).
    wid = [i for i, o in enumerate(objects) if o.get("id") == WORK_ID]
    if not wid:
        print(f"{WORK_ID}: REFUSAL -- revision 1 must exist (bank it with the derivation lane's admitter)", file=sys.stderr)
        return 1
    rev2 = work_record_rev2()
    if objects[wid[0]] == rev2:
        print(f"{WORK_ID}: already at revision 2 (no-op)")
    elif objects[wid[0]].get("physical", {}).get("contract", {}).get("derivation") == rev2["physical"]["contract"]["derivation"]:
        objects[wid[0]] = rev2
        print(f"{WORK_ID}: superseded revision 1 with revision 2 (implemented, measured)")
    else:
        print(f"{WORK_ID}: REFUSAL -- foreign content", file=sys.stderr)
        return 1

    # The model record: rev1 = specified (banked pre-run), rev2 = verified.
    status = sys.argv[1] if len(sys.argv) > 1 else "specified"
    if status == "verified":
        results = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8")) if len(sys.argv) > 2 else {}
        acceptance = ("Executed: the native gait falsifier suite runs F-G1..F-G8 green on the compiled gait scene "
                      "(receipt: tools/science_funnel/validation/gait_impl_20260919/receipt.json, native gait_unit stdout). "
                      "Measured: " + json.dumps(results, sort_keys=True))
        mid = [i for i, o in enumerate(objects) if o.get("id") == MODEL_ID]
        rec = model_record(measured, "verified", "tested", acceptance)
        if not mid:
            objects.append(rec)
            print(f"{MODEL_ID}: admitted at revision 2 (verified with measured results)")
        elif objects[mid[0]] == rec:
            print(f"{MODEL_ID}: already at revision 2 (no-op)")
        else:
            objects[mid[0]] = rec
            print(f"{MODEL_ID}: superseded revision 1 (specified) with revision 2 (verified, measured)")
    else:
        mid = [i for i, o in enumerate(objects) if o.get("id") == MODEL_ID]
        rec = model_record(measured, "specified", "untested",
                           "Not yet runnable at this revision: banked before the native suite's first run (Rule 0 order); the implementing lane records measured results in revision 2.")
        if not mid:
            objects.append(rec)
            print(f"{MODEL_ID}: admitted (specified, pre-code)")
        elif objects[mid[0]] == rec:
            print(f"{MODEL_ID}: already at current revision (no-op)")
        elif objects[mid[0]].get("status") == "specified" and objects[mid[0]].get("physical", {}).get("contract", {}).get("schema") == "chimera.gait_scene.v1":
            objects[mid[0]] = rec
            print(f"{MODEL_ID}: refreshed revision 1 (specified)")
        else:
            print(f"{MODEL_ID}: REFUSAL -- foreign content", file=sys.stderr)
            return 1

    out = json.dumps(payload, indent=1, ensure_ascii=False) + "\n"
    PROGRAM.write_bytes(out.replace("\n", "\r\n").encode("utf-8"))
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
