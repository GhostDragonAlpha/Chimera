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
    # revision 1 (superseded 2026-09-18 by the implementing lane): packet authored.
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
    # revision 2 (current, 2026-09-18, implementing lane GLM 5.3): IMPLEMENTATION
    # ADMISSION, recorded BEFORE any implementing code (RULE 0 order). Stage 0 was
    # measured first: the untouched qualified suite on this lane's worktree
    # reproduces both frozen bit-exact anchors (press gap 4.147475858029548e-07 m,
    # peak reaction 2.5894018617259906 N, drop heat 0.06656390658451124 J;
    # 158229 dynamics checks, pass). Four implementation errata are admitted
    # through the packet's own revision path and recorded in the packet's
    # AMENDMENT 20260918 section: E1 one-token validation diff to
    # coupled_articulation.hpp (coupled_coordinate_capacity 7 -> 8; integer
    # validation, not arithmetic; frozen control unaffected by construction),
    # E2 scene-server wiring lands in graph_earth.hpp + main.cpp (the actual
    # scene-server files; the packet had named engine.cpp), E3 the free class
    # derives its own impact-event budget depth < 10 + 6N (Refusal
    # coupled_free_impact_event_budget) because one substep can host 3N+2
    # sequential landings, E4 the scene opt-in ships as the sibling compiler
    # tools/science_funnel/coupled_free_scene.py (NEW) because the qualified
    # receipts pin coupled_scene.py's sha256. The support seating is derived and
    # recorded in the amendment (hand point + two sourced ulna1 points;
    # base_trans_y default -0.08977588222411312; CoM strictly inside the hull).
    {
        "id": FREE_ROOT_ID,
        "kind": "work",
        "name": "Free-root balance packet for the coupled-arm native solver (IMPLEMENTATION ADMITTED)",
        # Ladder note: the store status enum has no 'implementation' rung; the
        # honest pre-measurement rung is 'specified'. The implementation
        # admission itself is carried by this revision's name, statement and
        # contract (banked BEFORE code), and the falsifier status stays
        # 'untested' until revision 3 records measured results.
        "status": "specified",
        "priority": "P1",
        "dependencies": [
            "model.dynamics.coupled_arm",
            "model.anatomy.macaque_arm",
        ],
        "physical": {
            "statement":
                "Revision 2: the implementing lane (GLM 5.3, "
                "lane/free-root-20260918) admits implementation of "
                "docs/packets/free_root_balance_v1.md with errata E1-E4 "
                "recorded in the packet's AMENDMENT 20260918 section and in "
                "this revision BEFORE implementing code. The 8-DOF free-root "
                "dynamics (new header ChimeraEngine/engine/"
                "free_root_dynamics.hpp, Refusal tags coupled_free_*), the "
                "frozen mount-locked dispatch to the untouched qualified class "
                "(D10), the sibling scene compiler and the live falsifier "
                "script are admitted under the packet's D1-D10 derivations, "
                "falsifiers F1-F9 and performance budgets unchanged. Stage 0 "
                "(the frozen control) was measured first and holds bit-exactly "
                "on this lane's worktree.",
            "prediction":
                "Unchanged from revision 1 (the packet's PREDICTION); nothing "
                "free-root has been measured yet. The only measured claim so "
                "far is Stage 0: the qualified suite's frozen anchors "
                "(press gap 4.147475858029548e-07 m, peak reaction "
                "2.5894018617259906 N, drop heat 0.06656390658451124 J) "
                "reproduce bit-exactly with 158229 dynamics checks passing on "
                "the lane worktree before any implementing diff.",
            "contract": {
                "packet": "docs/packets/free_root_balance_v1.md",
                "derives": [
                    "D1-D10 unchanged; falsifiers F1-F9 unchanged; performance "
                    "budgets unchanged",
                    "E1 (packet AMENDMENT 20260918): coupled_articulation.hpp "
                    "takes a one-token VALIDATION diff (capacity 7 -> 8); no "
                    "arithmetic moves, frozen bit-exact control unaffected by "
                    "construction; the packet's own 'packet revision first' "
                    "path, recorded here before code",
                    "E2: scene-server wiring in graph_earth.hpp + main.cpp "
                    "(actual scene-server files), new bundle kind "
                    "coupled_free_dynamics, class construction on "
                    "free_root_enabled",
                    "E3: free-class impact-event budget depth < 10 + 6N with "
                    "Refusal coupled_free_impact_event_budget (loud, derived: "
                    "3N+2 sequential landings per substep, halving nesting <= "
                    "2 consuming <= 6, <= 2 per event split)",
                    "E4: coupled_scene.py stays byte-untouched (sha pinned by "
                    "qualified receipts); the opt-in is the sibling compiler "
                    "coupled_free_scene.py; default compile output remains the "
                    "qualified mounted world",
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
                    "ChimeraEngine/engine/free_root_dynamics.hpp",
                    "tools/science_funnel/coupled_free_scene.py",
                    "tools/science_funnel/tests/qualify_coupled_free_live.py",
                    "tools/science_funnel/tests/test_coupled_free.py",
                    "tools/creature_graph/validation/admit_coupled_free_20260918.py",
                ],
            },
        },
        "falsifier": {
            "statement":
                "Unchanged from revision 1: if with contact disabled the base "
                "fails to accelerate downward at g, or zero-torque standing "
                "holds pose without a contact reaction, or a CoM projection "
                "outside the support hull fails to tip, or any status query "
                "violates the ledger identities, or the mount-locked mode "
                "differs from the qualified candidate by a single ULP, or a "
                "free-flight trajectory clamps at the authored base range, or "
                "the measured budgets are exceeded -- the packet's dynamics "
                "claim is FALSE and the implementation is refused. A creature "
                "that cannot FALL cannot walk.",
            "acceptance_test":
                "Runnable with revision 3 of this record: the implementing "
                "lane executes falsifiers F1-F9 of "
                "docs/packets/free_root_balance_v1.md via "
                "tools/science_funnel/tests/qualify_coupled_free_live.py "
                "against the native runtime on the lane-owned port, plus the "
                "offline unit checks in tools/science_funnel/tests/"
                "test_coupled_free.py and the in-process native free suite; "
                "measured results are recorded in revision 3. Falsifier "
                "status stays honestly untested at this revision: no "
                "free-root falsifier has been run.",
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
    # revision 2 (current; SEVEN_COORD_REV2_MARKER_MERGE_20260919): the
    # seven-coordinate implementing lane verified this packet via
    # admit_coupled_arm7_20260918.py, whose record is copied verbatim
    # here so this script recognizes the merged graph's current truth
    # instead of refusing it as foreign content. Genuinely foreign
    # content still refuses.
    {
        "id": "work.dynamics.seven_coordinate_lift_packet",
        "kind": "work",
        "name": "Seven-coordinate lift packet for the native coupled dynamics (VERIFIED with disclosed limits)",
        "status": "verified",
        "priority": "P1",
        "dependencies": [
            "model.anatomy.macaque_arm",
            "model.dynamics.coupled_arm"
        ],
        "physical": {
            "statement": "The native coupled dynamics can carry all seven unlocked source coordinates of model.anatomy.macaque_arm with per-drive actuator stores, per-coordinate joint stops under a deterministic simultaneous-stop cascade, and the hand contact on the full 7-row point Jacobian -- the Python reference tools/science_funnel/coupled_arm.py (Assembly) already derives M(q), gravity, bias and point Jacobians analytically for all seven and serves as the independent oracle at 1e-12 relative -- while the qualified two-coordinate scene runs UNCHANGED as the frozen bit-exact control. Implemented by lane lane/seven-coord-complete-20260918 per the staged ladder; the friction sustained-slide ledger at n>=5 and the absolute tick budget are honestly disclosed limits (see receipt F6/F7/F9).",
            "prediction": "At any fixture pose, native M/gravity/bias/Jacobian match the Python Assembly to <= 1e-12 relative; a 7-drive rollout keeps |balance_error_J| < 1e-5 and |store_balance_error_J| < 1e-5 outside the disclosed sustained-slide regime; stop landings hold within 1e-9 at the impact tick; the stage-0 dispatch reproduces the qualified candidate bit-exactly. MEASURED: oracle worst 4.44e-16 relative over 300 recorded poses; frozen native suite output byte-identical to the pre-change baseline; 371825 checks green at stage 3.",
            "contract": {
                "packet": "docs/packets/seven_coordinate_lift_v1.md",
                "derives": [
                    "pinned recipe coordinate order = kinematic chain depth order with the qualified pair first; the oracle permutation is one declared fixture list (THE REFERENCE section)",
                    "7-row joint-stop cascade: generalized projection (mass-metric subset enumeration incl. the empty mask) plus the deterministic earliest-crossing / lowest-index tie law, with the qualified n=2 path byte-untouched (S1)",
                    "per-drive actuator stores with per-drive bisections, empty events and the honest statement that mechanical energy closure stays GLOBAL (S2)",
                    "hand contact on the 7-row point Jacobian with the qualified single-tangent Coulomb solve lifted row-count-only, plus the derived stick-dissipation condition (S3; friction sustained-slide ledger at n>=5 disclosed, not qualified)",
                    "staged qualification ladder 3 -> 5 -> 7 executed (S5)",
                    "recorded-seed oracle fixture, no sweep (S6)",
                    "frozen bit-exact control via dispatch; qualified class and compiler keep their exact bytes (S7)"
                ],
                "falsifiers": [
                    "F1 stage-0 frozen control (ULP-zero vs qualified receipts): PASS (native suite output hash-identical to pre-change baseline; multi class at n=2 bit-identical to the qualified class)",
                    "F2 oracle agreement <= 1e-12 relative: PASS (worst 4.44e-16 over 300 poses at n=3/5/7)",
                    "F3 mass identities: PASS (SPD, symmetric, Jacobi eigenvalues match oracle eigvalsh at 1e-16 scale)",
                    "F4 stop cascade determinism and landing correctness: PASS for the 20 pinned reachable landings (<= 1e-9 at the impact tick; deterministic double-runs); 10 bound pairs are honestly DISCLOSED as unreachable stalls (drive spring vs gravity) or Zeno-exhaustion regime",
                    "F5 per-drive stores: PASS (nonnegative, disabled spends exactly 0, empty events once, totals equal sums)",
                    "F6 ledger closure < 1e-5 J: PASS outside the disclosed sustained-slide friction regime",
                    "F7 hand contact honesty: PASS for mu=0 (exact-zero friction fields) and the cone; Coulomb sustained-slide ledger at n>=5 DISCLOSED as not qualified",
                    "F8 no regression: PASS (qualified native suite byte-identical; qualified live script 43/43; scene identity re-pinned with graph_hash-only delta proof)",
                    "F9 measured budgets: ratio to mounted 1.86 <= 3 PASS; oracle suite 0.15 s <= 60 s PASS; absolute 0.5 ms tick and 2x status bars EXCEEDED and DISCLOSED (boundary-event bisections + payload growth)"
                ],
                "owned_files": [
                    "docs/packets/seven_coordinate_lift_v1.md",
                    "tools/science_funnel/check_packet.py",
                    "tools/science_funnel/tests/test_packet_checker.py",
                    "tools/creature_graph/validation/admit_solver_packets_20260918.py",
                    "tools/creature_graph/validation/admit_coupled_arm7_20260918.py",
                    "tools/science_funnel/coupled_scene7.py",
                    "tools/science_funnel/tests/test_coupled_arm7.py",
                    "tools/science_funnel/tests/qualify_coupled_live7.py",
                    "tools/science_funnel/tests/build_oracle7.py",
                    "tools/science_funnel/tests/build_landing_table7.py",
                    "tools/science_funnel/validation/seven_coord_complete_20260918/",
                    "ChimeraEngine/engine/coupled_multidynamics.hpp",
                    "ChimeraEngine/engine/tests_coupled_arm/multidynamics_unit.cpp",
                    "ChimeraEngine/engine/tests_coupled_arm/CMakeLists.txt",
                    "ChimeraEngine/engine/graph_earth.hpp"
                ]
            }
        },
        "falsifier": {
            "statement": "Any oracle mismatch beyond 1e-12 relative on M/gravity/bias/Jacobian; any stage-0 status byte differing from the qualified candidate; any coordinate clamped outside its range by more than 1e-9 or held by anything but its stops; any per-drive store going negative, double-charging across substeps, or spending while disabled; any ledger identity violation; any nondeterminism across two identical runs -- REFUTES the lift and the implementation is refused.",
            "acceptance_test": "Executed 2026-09-18 by lane seven-coord-complete (GLM 5.3). F1 PASS: the complete qualified native suite output is byte-identical (SHA256-equal) to the pre-change baseline and the qualified live command script passes 43/43 on the modified engine. F2 PASS: 300 recorded poses at n=3/5/7, worst relative deviation 4.44e-16 (M, gravity, bias, potential, eigenvalues, hand point, 7-row Jacobian, generalized forces). F3 PASS: SPD + symmetry enforced by inverse_spd; eigenvalues match at 1e-16 scale. F4 PASS-with-disclosure: 20 pinned reachable landings hold within 1e-9 of the bound at the impact tick with the ledger closing and reproduce deterministically; 10 bound pairs are honestly disclosed unreachable (drive spring stalls vs gravity; shoulder_flexion both bounds, shoulder_rotation both bounds and their n=3/5 subsets) -- the Zeno-type impact sequence of a sustained wall-push is a loud budget refusal, not a silent clamp. F5 PASS: per-drive stores never negative, a disabled drive spends exactly 0, exhaustion counted once, totals equal sums. F6 PASS outside the disclosed regime. F7 PASS for mu=0 (exact-zero friction fields every tick) and the cone; Coulomb sustained-slide ledger drift at n>=5 (measured 0.0178/0.0216 J over 6000 ticks) DISCLOSED as not qualified. F8 PASS: qualified native suite byte-identical; qualified python suite green with the scene-identity pin re-pinned per its own protocol (graph_hash-only delta, proven by normalized diff). F9 PASS-with-disclosure: 7-coordinate median tick 1.48 ms = 1.83x mounted (bar 3x, PASS); absolute 0.5 ms bar and 2x status bar EXCEEDED and disclosed. Full detail: tools/science_funnel/validation/seven_coord_complete_20260918/receipt.json",
            "status": "tested"
        }
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
