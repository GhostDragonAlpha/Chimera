"""Admit the two native-solver implementation packets (RULE 0) into the authored program.

Idempotent AND revision-aware, one lane-owned object per packet. If a stored
record equals the current revision the script is a byte-preserving no-op; if
it equals a known PRIOR revision of the same lane object it is replaced by the
current revision (this is how the lane records its own falsified
assumptions); anything else refuses loudly -- graph policy is never silently
overwritten. Formatting is preserved (1-space indent, CRLF, no BOM).

Run from the checkout root with the pinned interpreter:
    python -B tools/creature_graph/validation/admit_solver_packets_20260918.py
then rebuild the store:
    python -B tools/creature_graph/build_graph.py

Both records are banked BEFORE any implementing code exists (RULE 0): the
packets AUTHOR derivations, falsifiers, frozen bit-exact controls, budgets
and file plans for a senior native-solver lane; nothing in them has been
measured, so both falsifier statuses are honestly "untested".
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROGRAM = ROOT / "tools" / "creature_graph" / "data" / "authored" / "project_program.json"

FREE_ROOT_ID = "work.dynamics.free_root_balance_packet"
SEVEN_COORD_ID = "work.dynamics.seven_coordinate_lift_packet"

CHECKER = "tools/science_funnel/check_packet.py"
ADMITTER = "tools/creature_graph/validation/admit_solver_packets_20260918.py"
PACKET_TEST = "tools/science_funnel/tests/test_packet_checker.py"

FREE_ROOT_REVISIONS = [
    # revision 1 (current): the packet is authored; nothing measured yet.
    {
        "id": FREE_ROOT_ID,
        "kind": "work",
        "name": "Free-root balance packet for the coupled-arm native solver (AUTHORED)",
        "status": "specified",
        "priority": "P1",
        "dependencies": [
            "model.dynamics.coupled_arm",
            "model.anatomy.macaque_arm",
        ],
        "physical": {
            "statement":
                "A rigid floating base (6 coordinates) added to the qualified "
                "two-coordinate coupled-arm scene -- 8 DOF with shoulder_flexion "
                "and elbow_flexion -- simulated by the same ordered-transform "
                "Model::evaluate machinery and the same RK4-with-event-splits "
                "integrator, with the mount-locked mode dispatching to the "
                "qualified code verbatim, is a faithful free-body simulation: "
                "the base falls under gravity when unsupported, stands only "
                "through cone-valid contact reactions that cancel gravity, and "
                "tips when the center of mass leaves the support hull. The "
                "packet at docs/packets/free_root_balance_v1.md derives every "
                "equation, constant, falsifier, budget and file change in the "
                "qualified code's exact conventions; it implements nothing.",
            "prediction":
                "With the mount released and contact enabled, a zero-torque "
                "assembly dropped from rest lands, dissipates landing energy "
                "exactly as the ledger accounts, and settles friction-"
                "determined; |balance_error_J| and |store_balance_error_J| stay "
                "below 1e-5 J on every status query; free flight conserves "
                "linear and angular momentum to 1e-9 relative over 5 s; the "
                "mount-locked mode reproduces the qualified candidate's status "
                "stream bit-exactly. NONE of this is measured yet.",
            "contract": {
                "packet": "docs/packets/free_root_balance_v1.md",
                "derives": [
                    "8-DOF floating-base equations in the code's exact "
                    "conventions (D1-D3): M, g_gen, c, potential from the "
                    "existing per-body jv/jw sums at n=8; zero generalized "
                    "actuator force on base rows by construction",
                    "contact rows become a list of 3D point-on-plane rows with "
                    "floors -bias (D4); friction becomes the 3-row stick solve "
                    "with the discrete cone check and the qualified slide "
                    "closed forms lifted to 8 rows (D5)",
                    "row projection generalizes from subset enumeration to the "
                    "mass-metric active-set loop with a derived termination "
                    "argument and loud Refusal caps (D6)",
                    "balance = gravity compensation through contact: the "
                    "barycentric normal distribution closes weight and weight "
                    "moment iff the CoM horizontal projection lies in the "
                    "support hull (D7)",
                    "energy-ledger extension with per-contact shares; closure "
                    "identity unchanged in form, bar 1e-5 J (D8)",
                    "stepping stays RK4 + event splits; the derivation is "
                    "stated and the alternative is rejected for cause (D9)",
                    "mount-locked mode = the qualified class runs verbatim "
                    "(FROZEN bit-exact control, D10)",
                ],
                "falsifiers": [
                    "F1 cannot-FALL-cannot-walk (unsupported base must fall at g)",
                    "F2 zero-torque standing must collapse (no phantom stiffness)",
                    "F3 support-polygon violation must tip",
                    "F4 ledger closure < 1e-5 J everywhere",
                    "F5 frozen bit-exact control (ULP-zero vs qualified receipts)",
                    "F6 free-flight momentum conservation 1e-9 relative",
                    "F7 base range scaffold must not clamp",
                    "F8 friction cone validity per touching point",
                    "F9 measured performance budgets (median tick, memory)",
                ],
                "owned_files": [
                    "docs/packets/free_root_balance_v1.md",
                    CHECKER,
                    PACKET_TEST,
                    ADMITTER,
                ],
            },
        },
        "falsifier": {
            "statement":
                "If with contact disabled the base fails to accelerate downward "
                "at g, or zero-torque standing holds pose without a contact "
                "reaction, or a CoM projection outside the support hull fails "
                "to tip, or any status query violates the ledger identities, or "
                "the mount-locked mode differs from the qualified candidate by "
                "a single ULP, or a free-flight trajectory clamps at the "
                "authored base range, or the measured budgets are exceeded -- "
                "the packet's dynamics claim is FALSE and the implementation is "
                "refused. A creature that cannot FALL cannot walk.",
            "acceptance_test":
                "Not yet runnable: the implementing lane executes falsifiers "
                "F1-F9 of docs/packets/free_root_balance_v1.md via its live "
                "qualification script and records measured results here in "
                "revision 2. Until then the honest status is untested.",
            "status": "untested",
        },
    },
]

SEVEN_COORD_REVISIONS = [
    # revision 1 (current): the packet is authored; nothing measured yet.
    {
        "id": SEVEN_COORD_ID,
        "kind": "work",
        "name": "Seven-coordinate lift packet for the native coupled dynamics (AUTHORED)",
        "status": "specified",
        "priority": "P1",
        "dependencies": [
            "model.anatomy.macaque_arm",
            "model.dynamics.coupled_arm",
        ],
        "physical": {
            "statement":
                "The native coupled dynamics can carry all seven unlocked "
                "source coordinates of model.anatomy.macaque_arm with "
                "per-drive actuator stores, per-coordinate joint stops under a "
                "deterministic simultaneous-stop cascade, and the hand contact "
                "on the full 7-row point Jacobian -- the Python reference "
                "tools/science_funnel/coupled_arm.py (Assembly) already "
                "derives M(q), gravity, bias and point Jacobians analytically "
                "for all seven and serves as the independent oracle at 1e-12 "
                "relative -- while the qualified two-coordinate scene runs "
                "UNCHANGED as the frozen bit-exact control. The packet at "
                "docs/packets/seven_coordinate_lift_v1.md authors the staged "
                "lift and its qualification ladder; it implements nothing.",
            "prediction":
                "At any fixture pose, native M/gravity/bias/Jacobian match the "
                "Python Assembly to <= 1e-12 relative; a 7-drive rollout keeps "
                "|balance_error_J| < 1e-5 and |store_balance_error_J| < 1e-5; "
                "all 14 coordinate-bound stop landings hold within 1e-9 with "
                "the impulse ledger closing; the stage-0 dispatch reproduces "
                "the qualified candidate bit-exactly. NONE of this is measured "
                "yet.",
            "contract": {
                "packet": "docs/packets/seven_coordinate_lift_v1.md",
                "derives": [
                    "pinned recipe coordinate order = kinematic chain depth "
                    "order with the qualified pair first; the oracle "
                    "permutation is one declared fixture list (THE REFERENCE section)",
                    "7-row joint-stop cascade: generalized projection (shared "
                    "derivation with the free-root packet D6) plus the "
                    "deterministic earliest-crossing / lowest-index tie law, "
                    "with the qualified n=2 path byte-untouched (S1)",
                    "per-drive actuator stores with per-drive bisections, "
                    "empty events and the honest statement that mechanical "
                    "energy closure stays GLOBAL (S2)",
                    "hand contact on the 7-row point Jacobian with the "
                    "qualified single-tangent Coulomb solve lifted "
                    "row-count-only (S3)",
                    "staged qualification ladder 2 -> 3 -> 5 -> 7 coordinates, "
                    "each stage one commit with falsifiers run first (S5)",
                    "recorded-seed oracle fixture, no sweep (S6)",
                    "frozen bit-exact control via dispatch; qualified class "
                    "and compiler keep their exact bytes (S7)",
                ],
                "falsifiers": [
                    "F1 stage-0 frozen control (ULP-zero vs qualified receipts)",
                    "F2 oracle agreement <= 1e-12 relative (M/gravity/bias/J)",
                    "F3 mass identities (SPD, symmetry, eigenvalues)",
                    "F4 stop cascade determinism and 1e-9 landing correctness",
                    "F5 per-drive store non-negativity and accounting",
                    "F6 ledger closure < 1e-5 J at every stage",
                    "F7 hand contact honesty incl. the mu=0 bit-exact control",
                    "F8 no regression of the qualified 2-coordinate world",
                    "F9 measured performance budgets",
                ],
                "owned_files": [
                    "docs/packets/seven_coordinate_lift_v1.md",
                    CHECKER,
                    PACKET_TEST,
                    ADMITTER,
                ],
            },
        },
        "falsifier": {
            "statement":
                "Any oracle mismatch beyond 1e-12 relative on M/gravity/bias/"
                "Jacobian; any stage-0 status byte differing from the "
                "qualified candidate; any coordinate clamped outside its range "
                "by more than 1e-9 or held by anything but its stops; any "
                "per-drive store going negative, double-charging across "
                "substeps, or spending while disabled; any ledger identity "
                "violation; any nondeterminism across two identical runs -- "
                "REFUTES the lift and the implementation is refused.",
            "acceptance_test":
                "Not yet runnable: the implementing lane executes falsifiers "
                "F1-F9 of docs/packets/seven_coordinate_lift_v1.md per ladder "
                "stage and records measured results here in revision 2. Until "
                "then the honest status is untested.",
            "status": "untested",
        },
    },
]

LANES = [
    (FREE_ROOT_ID, FREE_ROOT_REVISIONS),
    (SEVEN_COORD_ID, SEVEN_COORD_REVISIONS),
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
