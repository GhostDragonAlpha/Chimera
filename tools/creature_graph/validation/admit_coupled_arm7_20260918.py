"""Admit the seven-coordinate lift implementation records (RULE 0).

Lane lane/seven-coord-complete-20260918 (agent: GLM 5.3). The packet
docs/packets/seven_coordinate_lift_v1.md is already banked as
work.dynamics.seven_coordinate_lift_packet by
admit_solver_packets_20260918.py (its revision 1, status specified). THIS
script is the implementing lane's admitter:

  1. model.dynamics.coupled_arm7 -- the 7-coordinate recipe contract the
     compiler tools/science_funnel/coupled_scene7.py reads. Banked BEFORE any
     implementing code exists (RULE 0 order, same as the qualified
     model.dynamics.coupled_arm was).

Revision-aware and idempotent, one lane-owned object per id, following the
admit_solver_packets_20260918.py pattern: a stored record equal to the
current revision is a byte-preserving no-op; a known PRIOR revision is
superseded; anything else refuses loudly. Formatting is preserved (1-space
indent, CRLF, no BOM).

Revision history of this script (the script grows as the lane lands stages):
  rev A: admits model.dynamics.coupled_arm7 only.

Ownership note: once this lane supersedes work.dynamics.seven_coordinate_lift_packet
with revision 2 (measured results, later revision of this script),
re-running admit_solver_packets_20260918.py will REFUSE on that id ("exists
with foreign content") -- that refusal is correct and loud; the packet's own
supersede clause hands ownership of the record to the implementing lane.

Run from the checkout root with the pinned interpreter:
    python -B tools/creature_graph/validation/admit_coupled_arm7_20260918.py
then rebuild the store:
    python -B tools/creature_graph/build_graph.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROGRAM = ROOT / "tools" / "creature_graph" / "data" / "authored" / "project_program.json"

COUPLED_ARM7_ID = "model.dynamics.coupled_arm7"

COUPLED_ARM7_REVISIONS = [
    # revision 1 (current): the recipe contract is authored; no native scene
    # qualified yet.
    {
        "id": COUPLED_ARM7_ID,
        "kind": "model",
        "name": "Seven-coordinate native arm dynamics recipe",
        "status": "specified",
        "priority": "P1",
        "dependencies": [
            "model.anatomy.macaque_arm",
            "model.environment.earth_patch",
        ],
        "evidence": [],
        "falsifier": {
            "statement": "A native M/gravity/bias/Jacobian deviating from the "
                         "Python Assembly oracle beyond 1e-12 relative, a stop landing "
                         "outside its bound by more than 1e-9, a negative per-drive "
                         "store, a disabled drive that spends energy, a ledger identity "
                         "violation, or a single byte of regression in the qualified "
                         "two-coordinate world falsifies the seven-coordinate recipe.",
            "status": "untested",
        },
        "physical": {
            "statement": "Seven-coordinate native arm dynamics recipe",
            "prediction": "All seven unlocked source coordinates move under "
                          "per-drive capped servo drives with finite per-drive stores; "
                          "generalized quantities match the Python oracle to 1e-12 "
                          "relative at every pose; the qualified two-coordinate scene "
                          "runs bit-exactly unchanged.",
            "contract": {
                "schema": "chimera.coupled_scene7.v1",
                "source_model_id": "model.anatomy.macaque_arm",
                "coordinates": [
                    "shoulder_flexion",
                    "elbow_flexion",
                    "radial_pronation",
                    "wrist_flexion",
                    "wrist_abduction",
                    "shoulder_adduction",
                    "shoulder_rotation",
                ],
                "hand_body": "hand",
                "hand_point_m": [
                    0.001777657291666502,
                    -0.036138621093750024,
                    0.002310406250000002,
                ],
                "attachment_id": "world.earth.patch.coupled_arm_hand",
                "proxy_radius_m": 0.007,
                "tick_hz": 300,
                "substeps": 4,
                "servo_frequency_Hz": 2.0,
                "servo_damping_ratio": 0.8,
                "passive_decay_rate_s": 2.0,
                "battery_initial_J": 2.0,
                "defaults": {
                    "shoulder_flexion_target_deg": 20.0,
                    "elbow_flexion_target_deg": 110.0,
                    "radial_pronation_target_deg": 0.0,
                    "wrist_flexion_target_deg": 0.0,
                    "wrist_abduction_target_deg": 0.0,
                    "shoulder_adduction_target_deg": 0.0,
                    "shoulder_rotation_target_deg": 0.0,
                    "shoulder_flexion_torque_limit_N_m": 0.6,
                    "elbow_flexion_torque_limit_N_m": 0.3,
                    "radial_pronation_torque_limit_N_m": 0.3,
                    "wrist_flexion_torque_limit_N_m": 0.3,
                    "wrist_abduction_torque_limit_N_m": 0.3,
                    "shoulder_adduction_torque_limit_N_m": 0.6,
                    "shoulder_rotation_torque_limit_N_m": 0.6,
                    "shoulder_flexion_drive": True,
                    "elbow_flexion_drive": True,
                    "radial_pronation_drive": True,
                    "wrist_flexion_drive": True,
                    "wrist_abduction_drive": True,
                    "shoulder_adduction_drive": True,
                    "shoulder_rotation_drive": True,
                    "power": True,
                    "load_N": 0.0,
                    "contact_enabled": False,
                    "contact_friction": 0.0,
                },
                "assumptions": [
                    "Root fixed (mounted sternum, the free-root packet's scope, "
                    "not this one); all seven unlocked source coordinates move; the "
                    "source model's locked coordinates stay fixed by authoring.",
                    "Pinned coordinate order is kinematic chain depth order "
                    "(sternum->humerus->ulna->radius->hand) with the qualified pair "
                    "first, so stage comparisons are prefix expansions; the Python "
                    "oracle's own order is sorted() and the fixture pins the "
                    "permutation in one declared list.",
                    "Per-drive ideal capped actuator stores (battery_initial_J per "
                    "drive, the same derived 2.0 J capacity per source): the "
                    "qualified scene's ONE shared battery is a TWO-drive contract and "
                    "is not extended; adding a third drive to a shared store would "
                    "change qualified behavior, which the frozen control forbids.",
                    "Torque-cap rails: 0.6 N m for shoulder-class drives "
                    "(shoulder_flexion, shoulder_adduction, shoulder_rotation) and "
                    "0.3 N m for elbow/wrist-class drives, carried from the qualified "
                    "drive hardware classes; an authored hardware mapping, not a "
                    "measured muscle limit.",
                    "Servo gains extend by the qualified mass-normalized PD at the "
                    "diagonal: kp_d = M[d][d]*(2*pi*f)^2, kd_d = 2*zeta*M[d][d]*(2*pi*f), "
                    "damping_d = M[d][d]*decay, evaluated at model defaults.",
                    "Simultaneous joint stops project in the mass metric with "
                    "nonnegative multipliers; an event-level cascade localizes each "
                    "violated bound by its own bisection, the earliest crossing wins "
                    "and ties within 1e-12*h break to the LOWEST recipe-coordinate "
                    "index (one stop impact per event, recursion bounded); the "
                    "qualified n=2 loop keeps its own last-index tie law byte-for-byte.",
                    "Optional hand contact on the full n-row point Jacobian with "
                    "the qualified single-tangent Coulomb solve lifted "
                    "row-count-only; touching band, gate and floors carried verbatim; "
                    "friction heat enters the GLOBAL energy ledger (there is no "
                    "per-drive energy closure and none is claimed).",
                    "contact_enabled is false by default; toggling it requires an "
                    "explicit reset; enabled scenes start with a strictly positive "
                    "gap at the reset pose; mu is live without reset.",
                    "CPU reference reuses native source binding and Earth field; "
                    "no free root, muscles, grasping, whole animal or GPU residency "
                    "is claimed at seven coordinates.",
                ],
                "contact_plane_height_m": 0.35,
                "contact_plane_id": "world.earth.patch.coupled_arm_contact_plane",
            },
        },
    },
]

LANES = [
    (COUPLED_ARM7_ID, COUPLED_ARM7_REVISIONS),
]


def admit(objects, object_id, revisions):
    current = revisions[-1]
    prior = revisions[:-1]
    existing = [o for o in objects if o.get("id") == object_id]
    if existing:
        if existing[0] == current:
            print(f"{object_id}: already at current revision (no-op)")
            return 0
        if existing[0] in prior:
            objects[objects.index(existing[0])] = current
            print(f"{object_id}: superseded prior revision with current")
            return 2
        print(f"{object_id}: REFUSAL -- exists with foreign content; "
              "graph policy is never silently overwritten", file=sys.stderr)
        return 1
    objects.append(current)
    print(f"{object_id}: admitted to {PROGRAM}")
    return 2


def main() -> int:
    raw = PROGRAM.read_bytes()
    payload = json.loads(raw.decode("utf-8-sig"))
    objects = payload["objects"]
    changed = 0
    for object_id, revisions in LANES:
        result = admit(objects, object_id, revisions)
        if result == 1:
            return 1
        changed = max(changed, result)
    if changed:
        out = json.dumps(payload, indent=1, ensure_ascii=False) + "\n"
        PROGRAM.write_bytes(out.replace("\n", "\r\n").encode("utf-8"))
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
