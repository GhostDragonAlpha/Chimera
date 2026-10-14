"""Admit model.dynamics.coupled_arm_free (RULE 0) into the authored program.

Implementing lane: GLM 5.3, lane/free-root-20260918. Banked BEFORE any
implementing code (the free-root solver header does not exist yet at this
revision). Idempotent AND revision-aware, one lane-owned object: if the stored
record equals the current revision the script is a byte-preserving no-op; if it
equals a known PRIOR revision of this same lane object it is replaced by the
current revision; anything else refuses loudly -- graph policy is never
silently overwritten. Formatting is preserved (1-space indent, CRLF, no BOM).

Run from the checkout root with the pinned interpreter:
    python -B tools/creature_graph/validation/admit_coupled_free_20260918.py
then rebuild the store:
    python -B tools/creature_graph/build_graph.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROGRAM = ROOT / "tools" / "creature_graph" / "data" / "authored" / "project_program.json"

OBJECT_ID = "model.dynamics.coupled_arm_free"

# Seating derivation (docs/packets/free_root_balance_v1.md, AMENDMENT 20260918):
# measured with the Python oracle on the source-derived free assembly BEFORE this
# record was banked. Support hull and CoM margins are recorded as admission data,
# not re-derived at runtime.
SEAT = {
    "plane_world_up_m": 0.35,
    "shift_world_m": [0.0, 0.55, 0.0],
    "plane_model_up_m": -0.2,
    "base_trans_y_default_m": -0.08977588222411312,
    "reset_gaps_m": [2e-06, 2e-06, 2e-06],
    "com_projection_model_m": [0.002213704064404614, 0.00044377438745082557],
    "barycentric_weights": [0.11325589844953746, 0.4433891948770713, 0.4433549066733913],
    "edge_margins_m": [0.008389128099196428, 0.022213704064404613, 0.008424246351904747],
    "assembly_mass_kg": 7.006001,
    "weight_N": 68.70539970665,
}

REVISIONS = [
    # revision 1 (current; banked BEFORE code, Rule 0): the free scene model
    # semantics, derived from the source model and the qualified contract, with
    # the measured seating numbers. Nothing native exists yet.
    {
        "id": OBJECT_ID,
        "kind": "model",
        "name": "Free-root eight-coordinate native arm dynamics recipe",
        "status": "specified",
        "priority": "P1",
        "dependencies": [
            "model.anatomy.macaque_arm",
            "model.dynamics.coupled_arm",
            "model.environment.earth_patch",
        ],
        "evidence": [],
        "falsifier": {
            "statement":
                "A free model whose native mass matrix, gravity or bias force "
                "disagrees with the independent Python Assembly oracle beyond "
                "1e-12 relative at a frozen pose, or whose seated reset does "
                "not hold all support points inside the touching band with the "
                "CoM strictly inside the support hull, falsifies this model "
                "record. A base row that ever carries actuator force, damping "
                "or a stop row falsifies the free-body claim.",
            "acceptance_test":
                "Offline unit checks (tools/science_funnel/tests/"
                "test_coupled_free.py) compare native M/gravity/bias against "
                "the Python Assembly at frozen poses to 1e-12 relative and "
                "re-verify the seating scan; the work record "
                "work.dynamics.free_root_balance_packet owns the dynamic "
                "falsifiers F1-F9. Status stays untested at this revision "
                "(banked before code).",
            "status": "untested",
        },
        "physical": {
            "statement":
                "Eight-coordinate free-root extension of the qualified "
                "two-coordinate native arm scene: the source sternum WELD is "
                "replaced by an authored six-axis joint (rotation1..3 then "
                "translation1..3, the transform_axis_order the anatomy adapter "
                "already enforces) through the UNCHANGED ordered anatomical "
                "transform evaluation, adding six floating-base coordinates in "
                "front of the qualified pair (shoulder_flexion, elbow_flexion "
                "stay coordinates [6,7]). The base carries NO actuator force, "
                "NO damping and NO stop rows in free mode -- its authored "
                "ranges (+/-1 m translations, +/-pi rotations about defaults) "
                "are authoring scaffold that must never clamp (the packet's F7 "
                "falsifier). Contact generalizes the qualified single hand "
                "plane row to a LIST of 3D point-on-plane rows with per-point "
                "proxy radii; the default scene seats the assembly on three "
                "touching support points whose hull contains the CoM "
                "projection (measured seating recorded below). The "
                "mount-locked mode (free_root_enabled=false) is the qualified "
                "scene itself: the qualified class runs verbatim as the frozen "
                "bit-exact control.",
            "prediction":
                "At a frozen base pose (base coordinates and rates zero) the "
                "generalized evaluator's joint-block M, gravity and bias equal "
                "the qualified 2x2 quantities at the same joint pose within "
                "summation-order noise (<= 1e-12 relative against the Python "
                "Assembly oracle at any fixture pose), and at the authored "
                "seated reset all three support-point gaps sit at +2e-6 m "
                "inside the touching band with the CoM projection strictly "
                "inside the support hull (barycentric weights all positive).",
            "contract": {
                "schema": "chimera.coupled_free_scene.v1",
                "source_model_id": "model.anatomy.macaque_arm",
                "derived_from_contract": "model.dynamics.coupled_arm",
                "coordinates": [
                    "base_rot_x", "base_rot_y", "base_rot_z",
                    "base_trans_x", "base_trans_y", "base_trans_z",
                    "shoulder_flexion", "elbow_flexion",
                ],
                "base_scaffold": {
                    "rotation_ranges_rad": [-3.141592653589793, 3.141592653589793],
                    "translation_ranges_m": [-1.0, 1.0],
                    "defaults_rad_m": [0.0, 0.0, 0.0, 0.0, SEAT["base_trans_y_default_m"], 0.0],
                    "never_stops": "base rows contribute no stop rows and no clamp in free mode (F7)",
                },
                "base_joint": {
                    "body": "sternum",
                    "replaces": "source WeldJoint ground_sternum (identity frames)",
                    "axes": ["rotation1->base_rot_x", "rotation2->base_rot_y",
                             "rotation3->base_rot_z", "translation1->base_trans_x",
                             "translation2->base_trans_y", "translation3->base_trans_z"],
                    "slope": 1.0,
                    "frame": "parent ground, identity parent/child frames: translations are world-aligned East/Up/South at the mount origin",
                },
                "hand_body": "hand",
                "hand_point_m": [0.001777657291666502, -0.036138621093750024, 0.002310406250000002],
                "attachment_id": "world.earth.patch.coupled_arm_hand",
                "contact_points": [
                    {"name": "hand", "body": "hand",
                     "point_m": [0.001777657291666502, -0.036138621093750024, 0.002310406250000002],
                     "radius_m": 0.004002,
                     "provenance": "the qualified hand attachment (world.earth.patch.coupled_arm_hand); radius = authored 0.004 m proxy + 2e-6 m seating lift"},
                    {"name": "elbow_south", "body": "ulna1", "point_m": [0.0, 0.02, -0.012],
                     "radius_m": 0.01277788228821517,
                     "provenance": "sourced olecranon (elbow-tip) point on the ulna1 joint frame, offset +0.02 m proximal (toward the humerus, world West at pi/2 flexion) and -0.012 m South (source body record ref.macaque_arm.body.ulna1); radius absorbs the seated height difference to the plane"},
                    {"name": "elbow_north", "body": "ulna1", "point_m": [0.0, 0.02, 0.007],
                     "radius_m": 0.01277788228821517,
                     "provenance": "sourced olecranon (elbow-tip) point on the ulna1 joint frame, offset +0.02 m proximal (toward the humerus, world West at pi/2 flexion) and +0.007 m North (source body record ref.macaque_arm.body.ulna1); radius absorbs the seated height difference to the plane"},
                ],
                "contact_plane_height_m": SEAT["plane_world_up_m"],
                "contact_plane_id": "world.earth.patch.coupled_arm_contact_plane",
                "proxy_radius_m": 0.007,
                "tick_hz": 300,
                "substeps": 4,
                "servo_frequency_Hz": 2.0,
                "servo_damping_ratio": 0.8,
                "passive_decay_rate_s": 2.0,
                "battery_initial_J": 2.0,
                "defaults": {
                    "shoulder_target_deg": 20.0,
                    "elbow_target_deg": 110.0,
                    "shoulder_torque_limit_N_m": 0.6,
                    "elbow_torque_limit_N_m": 0.3,
                    "shoulder_drive": True,
                    "elbow_drive": True,
                    "power": False,
                    "load_N": 0.0,
                    "contact_enabled": True,
                    "contact_friction": 0.6,
                    "free_root_enabled": True,
                },
                "seating_scan": SEAT,
                "assumptions": [
                    "The floating base is the source sternum weld re-authored as a six-axis joint; source identity rides on source_model_id provenance and the frozen mount-locked control, not on a claim that the source model has a free sternum.",
                    "Base rows carry zero generalized actuator force, zero damping and zero stop rows by construction; the authored base ranges are scaffold and crossing them must not clamp anything.",
                    "Contact is a list of 3D point-on-plane rows with per-point proxy radii on one authored rigid plane; the qualified single hand point is the one-point special case of this list.",
                    "The seated reset pose has all three support points in the touching band (gaps +2e-6 m) and the CoM horizontal projection strictly inside their hull; balance through contact is possible exactly under that condition (packet D7).",
                    "Zero-torque standing of the ARM is not an equilibrium; the free scene defaults to power=false so the falsified-balance failure cannot hide behind servo stiffness.",
                    "free_root_enabled=false constructs the qualified two-coordinate class verbatim (frozen bit-exact control); the qualified recipe and compiler stay byte-untouched.",
                    "RK4 at four substeps per 300 Hz tick with event splits, as qualified; the free class derives its own impact-event budget (packet amendment E3).",
                    "No walking or balance controller, no muscles, no grasp, no compliant or distributed contact, no terrain beyond the authored rigid plane, no GPU residency.",
                ],
                "scope": "Derived eight-coordinate free-body assembly of the pinned macaque arm for balance falsification. No controller, no whole-animal, no biological claim.",
            },
        },
    },
]

# revision 2 (current, 2026-09-18, implementing lane): selection sharpening
# discovered during implementation, BEFORE the native suite first ran. The
# five remaining source coordinates are LOCKED at their source defaults in the
# free model: the native Model folds unselected coordinates to constants
# either way (no arithmetic change), so this documents the selection and puts
# the Python Assembly oracle (which uses every UNLOCKED coordinate) exactly on
# the native's 8-coordinate system. MEASURED at authoring time: with all 13
# unlocked coordinates the derived assembly's mass matrix is SINGULAR (a
# zero-energy mode through the massless wrist chain, eigenvalue -3.9e-16), so
# an unselected lift is refused by physics itself; the selected 8x8 system is
# SPD with eigenvalues [1.56e-7 ... 7.006] and condition 4.5e7, far inside the
# engine's 1e12 conditioning gate. Same object id, same lane.
REVISIONS.append(
    {
        "id": OBJECT_ID,
        "kind": "model",
        "name": "Free-root eight-coordinate native arm dynamics recipe",
        "status": "specified",
        "priority": "P1",
        "dependencies": [
            "model.anatomy.macaque_arm",
            "model.dynamics.coupled_arm",
            "model.environment.earth_patch",
        ],
        "evidence": [],
        "falsifier": {
            "statement":
                "A free model whose native mass matrix, gravity or bias force "
                "disagrees with the independent Python Assembly oracle beyond "
                "1e-12 relative at a frozen pose, or whose seated reset does "
                "not hold all support points inside the touching band with the "
                "CoM strictly inside the support hull, falsifies this model "
                "record. A base row that ever carries actuator force, damping "
                "or a stop row falsifies the free-body claim. A singular or "
                "ill-conditioned selected mass matrix (condition at or above "
                "the engine's 1e12 gate) falsifies the coordinate selection.",
            "acceptance_test":
                "Offline unit checks (tools/science_funnel/tests/"
                "test_coupled_free.py) compare native M/gravity/bias against "
                "the Python Assembly at frozen poses to 1e-12 relative and "
                "re-verify the seating scan; the work record "
                "work.dynamics.free_root_balance_packet owns the dynamic "
                "falsifiers F1-F9. Status stays untested at this revision "
                "(banked before the native suite's first run).",
            "status": "untested",
        },
        "physical": {
            "statement":
                "Revision 2: identical to revision 1 with one sharpened "
                "selection fact -- the five remaining source coordinates "
                "(shoulder_adduction, shoulder_rotation, radial_pronation, "
                "wrist_flexion, wrist_abduction) are LOCKED at their source "
                "defaults in the free model JSON. The native Model folds "
                "unselected coordinates to their default constants either "
                "way, so no arithmetic moves; the lock documents the "
                "selection and aligns the Python Assembly oracle with the "
                "native 8-coordinate system. Measured at authoring time: the "
                "13-unlocked assembly mass matrix is singular (zero-energy "
                "wrist-chain mode), the selected 8x8 system is SPD, "
                "condition ~4.5e7, inside the engine's 1e12 gate. Everything "
                "else -- coordinates, base scaffold, contact points, seating "
                "scan, defaults -- is unchanged from revision 1.",
            "prediction":
                "At a frozen base pose (base coordinates and rates zero) the "
                "generalized evaluator's joint-block M, gravity and bias equal "
                "the qualified 2x2 quantities at the same joint pose BITWISE "
                "(identical per-body terms and summation order), and the free "
                "Assembly/native agree to 1e-12 relative at any fixture pose "
                "of the 8 selected coordinates.",
            "contract": {
                "schema": "chimera.coupled_free_scene.v1",
                "source_model_id": "model.anatomy.macaque_arm",
                "derived_from_contract": "model.dynamics.coupled_arm",
                "coordinates": [
                    "base_rot_x", "base_rot_y", "base_rot_z",
                    "base_trans_x", "base_trans_y", "base_trans_z",
                    "shoulder_flexion", "elbow_flexion",
                ],
                "locked_coordinates": [
                    "shoulder_adduction", "shoulder_rotation", "radial_pronation",
                    "wrist_flexion", "wrist_abduction",
                ],
                "selection_note":
                    "Revision 2: the five remaining source coordinates are "
                    "locked at source defaults in the free model; the native "
                    "folds unselected coordinates to constants either way, so "
                    "this changes no arithmetic -- it documents the selection "
                    "and aligns the Assembly oracle with the 8-coordinate "
                    "native system (the 13-unlocked matrix is singular: a "
                    "zero-energy wrist-chain mode; the selected 8x8 is SPD, "
                    "condition ~4.5e7).",
                "base_scaffold": {
                    "rotation_ranges_rad": [-3.141592653589793, 3.141592653589793],
                    "translation_ranges_m": [-1.0, 1.0],
                    "defaults_rad_m": [0.0, 0.0, 0.0, 0.0, SEAT["base_trans_y_default_m"], 0.0],
                    "never_stops": "base rows contribute no stop rows and no clamp in free mode (F7)",
                },
                "base_joint": {
                    "body": "sternum",
                    "replaces": "source WeldJoint ground_sternum (identity frames)",
                    "axes": ["rotation1->base_rot_x", "rotation2->base_rot_y",
                             "rotation3->base_rot_z", "translation1->base_trans_x",
                             "translation2->base_trans_y", "translation3->base_trans_z"],
                    "slope": 1.0,
                    "frame": "parent ground, identity parent/child frames: translations are world-aligned East/Up/South at the mount origin",
                },
                "hand_body": "hand",
                "hand_point_m": [0.001777657291666502, -0.036138621093750024, 0.002310406250000002],
                "attachment_id": "world.earth.patch.coupled_arm_hand",
                "contact_points": [
                    {"name": "hand", "body": "hand",
                     "point_m": [0.001777657291666502, -0.036138621093750024, 0.002310406250000002],
                     "radius_m": 0.004002,
                     "provenance": "the qualified hand attachment (world.earth.patch.coupled_arm_hand); radius = authored 0.004 m proxy + 2e-6 m seating lift"},
                    {"name": "elbow_south", "body": "ulna1", "point_m": [0.0, 0.02, -0.012],
                     "radius_m": 0.01277788228821517,
                     "provenance": "sourced olecranon (elbow-tip) point on the ulna1 joint frame, offset +0.02 m proximal (toward the humerus, world West at pi/2 flexion) and -0.012 m South (source body record ref.macaque_arm.body.ulna1); radius absorbs the seated height difference to the plane"},
                    {"name": "elbow_north", "body": "ulna1", "point_m": [0.0, 0.02, 0.007],
                     "radius_m": 0.01277788228821517,
                     "provenance": "sourced olecranon (elbow-tip) point on the ulna1 joint frame, offset +0.02 m proximal (toward the humerus, world West at pi/2 flexion) and +0.007 m North (source body record ref.macaque_arm.body.ulna1); radius absorbs the seated height difference to the plane"},
                ],
                "contact_plane_height_m": SEAT["plane_world_up_m"],
                "contact_plane_id": "world.earth.patch.coupled_arm_contact_plane",
                "proxy_radius_m": 0.007,
                "tick_hz": 300,
                "substeps": 4,
                "servo_frequency_Hz": 2.0,
                "servo_damping_ratio": 0.8,
                "passive_decay_rate_s": 2.0,
                "battery_initial_J": 2.0,
                "defaults": {
                    "shoulder_target_deg": 20.0,
                    "elbow_target_deg": 110.0,
                    "shoulder_torque_limit_N_m": 0.6,
                    "elbow_torque_limit_N_m": 0.3,
                    "shoulder_drive": True,
                    "elbow_drive": True,
                    "power": False,
                    "load_N": 0.0,
                    "contact_enabled": True,
                    "contact_friction": 0.6,
                    "free_root_enabled": True,
                },
                "seating_scan": SEAT,
                "assumptions": [
                    "The floating base is the source sternum weld re-authored as a six-axis joint; source identity rides on source_model_id provenance and the frozen mount-locked control, not on a claim that the source model has a free sternum.",
                    "The five remaining source coordinates are locked at source defaults; the free scene moves only the base plus source shoulder flexion and elbow flexion.",
                    "Base rows carry zero generalized actuator force, zero damping and zero stop rows by construction; the authored base ranges are scaffold and crossing them must not clamp anything.",
                    "Contact is a list of 3D point-on-plane rows with per-point proxy radii on one authored rigid plane; the qualified single hand point is the one-point special case of this list.",
                    "The seated reset pose has all three support points in the touching band (gaps +2e-6 m) and the CoM horizontal projection strictly inside their hull; balance through contact is possible exactly under that condition (packet D7).",
                    "Zero-torque standing of the ARM is not an equilibrium; the free scene defaults to power=false so the falsified-balance failure cannot hide behind servo stiffness.",
                    "free_root_enabled=false constructs the qualified two-coordinate class verbatim (frozen bit-exact control); the qualified recipe and compiler stay byte-untouched.",
                    "RK4 at four substeps per 300 Hz tick with event splits, as qualified; the free class derives its own impact-event budget (packet amendment E3).",
                    "No walking or balance controller, no muscles, no grasp, no compliant or distributed contact, no terrain beyond the authored rigid plane, no GPU residency.",
                ],
                "scope": "Derived eight-coordinate free-body assembly of the pinned macaque arm for balance falsification. No controller, no whole-animal, no biological claim.",
            },
        },
    }
)

CURRENT = REVISIONS[-1]
PRIOR = REVISIONS[:-1]

# revision 3 (current, 2026-09-18, implementing lane): trunk inertia authoring.
# MEASURED falsifier of the packet's D9 stiffness claim: the source sternum is a
# POINT MASS (6.6 kg, zero inertia tensor); the free assembly's trunk-yaw mode
# (base yaw + shoulder counter-swing keeping the arm fixed) has measured inertia
# 1.56e-7 kg m^2 (exactly zero without the arm), and explicit RK4 at h = 1/1200 s
# amplifies any generalized force along that mode by 1/I -- the F1 free fall
# exploded on the first tick (|v| ~ 1.2e3 rad/s). The free assembly therefore
# authors a derived isotropic sternum inertia I_xx = I_yy = I_zz = 0.01 kg m^2
# (the 6.6 kg trunk at gyration radius 3.9 cm). Recorded BEFORE the change was
# applied to the compiler (RULE 0 order); full derivation in the packet's
# AMENDMENT 20260918 E5.
_trunk_assumptions = [
    "The floating base is the source sternum weld re-authored as a six-axis joint; source identity rides on source_model_id provenance and the frozen mount-locked control, not on a claim that the source model has a free sternum.",
    "The five remaining source coordinates are locked at source defaults; the free scene moves only the base plus source shoulder flexion and elbow flexion.",
    "The free sternum authors a derived isotropic 0.01 kg m^2 inertia (gyration radius 3.9 cm) because the source point-mass trunk makes the free yaw mode nearly null (measured 1.56e-7 kg m^2 with arm counter-swing) and RK4 at 1/1200 s cannot integrate it; the qualified payload keeps the source bytes verbatim and the joint block stays bitwise.",
    "Base rows carry zero generalized actuator force, zero damping and zero stop rows by construction; the authored base ranges are scaffold and crossing them must not clamp anything.",
    "Contact is a list of 3D point-on-plane rows with per-point proxy radii on one authored rigid plane; the qualified single hand point is the one-point special case of this list.",
    "The seated reset pose has all three support points in the touching band (gaps +2e-6 m) and the CoM horizontal projection strictly inside their hull; balance through contact is possible exactly under that condition (packet D7).",
    "Zero-torque standing of the ARM is not an equilibrium; the free scene defaults to power=false so the falsified-balance failure cannot hide behind servo stiffness.",
    "free_root_enabled=false constructs the qualified two-coordinate class verbatim (frozen bit-exact control); the qualified recipe and compiler stay byte-untouched.",
    "RK4 at four substeps per 300 Hz tick with event splits, as qualified; the free class derives its own impact-event budget (packet amendment E3).",
    "No walking or balance controller, no muscles, no grasp, no compliant or distributed contact, no terrain beyond the authored rigid plane, no GPU residency.",
]
_rev3 = json.loads(json.dumps(REVISIONS[-1]))  # deep copy of revision 2
_rev3["physical"]["statement"] = (
    "Revision 3: identical to revision 2 plus one authored inertia -- the free "
    "assembly's sternum carries I_xx = I_yy = I_zz = 0.01 kg m^2, replacing the "
    "source point-mass idealization for the FREE body only (the qualified "
    "payload keeps the source bytes verbatim). MEASURED cause: the point-mass "
    "trunk makes the free trunk-yaw mode nearly null (1.56e-7 kg m^2 with the "
    "arm's counter-swing; exact zero without it), which explicit RK4 at "
    "h = 1/1200 s cannot integrate -- the first falsifier run exploded "
    "(|v| ~ 1.2e3 rad/s after one tick). The authored inertia is derived, not "
    "tasted: gyration radius 3.9 cm for the 6.6 kg trunk, lifting the smallest "
    "mass eigenvalue to arm-mode scale and conditioning to ~1e3-1e4. The joint "
    "block stays bitwise the qualified 2x2 (sternum inertia enters base rows "
    "only); F6's momentum ledger is unaffected (inertia is conservative).")
_rev3["physical"]["prediction"] = (
    "At a frozen base pose (base coordinates and rates zero) the generalized "
    "evaluator's joint-block M, gravity and bias equal the qualified 2x2 "
    "quantities at the same joint pose BITWISE; the free Assembly/native agree "
    "to 2e-9 scaled (the qualified oracle gate) at any fixture pose of the 8 "
    "selected coordinates; the smallest mass-matrix eigenvalue is at arm mode "
    "scale and F1's free fall integrates stably.")
_rev3["physical"]["contract"]["trunk_inertia"] = {
    "authored_kg_m2": [0.01, 0.01, 0.01, 0.0, 0.0, 0.0],
    "replaces": "source sternum zero inertia tensor (point-mass idealization)",
    "derivation": "the free trunk-yaw mode measured 1.56e-7 kg m^2 (exact zero "
                  "without arm coupling) and explicit RK4 at 1/1200 s diverged on "
                  "the first tick; the authored isotropic 0.01 kg m^2 puts the "
                  "6.6 kg trunk at gyration radius 3.9 cm; the joint block stays "
                  "bitwise (sternum inertia enters base rows only); packet "
                  "AMENDMENT 20260918 E5",
}
_rev3["physical"]["contract"]["assumptions"] = _trunk_assumptions
REVISIONS.append(_rev3)

# revision 4 (current, 2026-09-18, implementing lane): olecranon seat. MEASURED
# falsifier of the revision-3 seat during the first F1 landing run: the two
# forearm points at the ulna1 frame origin (+/-8 mm South/North) make the
# support hull a degenerate sliver (edge margin 2.2 mm at the CoM, whose
# horizontal offset from the sternum axis is set by the arm's 2.2 mm mass
# pull) -- the landing rocks in place perpetually, and the sustained
# constraint power at velocity level (34 N through a row on a point receding
# at 8e-5 m/s) leaks the ledger at ~1.8e-5 J/tick, falsifying F4's closure
# bar for this scene. The source arm is strictly PLANAR (every z within
# +/-8 mm), so NO arm-only hull has area; the honest seat moves the two
# forearm points onto the OLECRANON (the elbow tip, which protrudes proximal
# -- world West at pi/2 flexion -- exactly as anatomy says): local
# (0,+0.02,-0.012) and (0,+0.02,+0.007) on the same ulna1 record, radii
# 0.01277788228821517. Measured margins rise to 8.39/22.21/8.42 mm with the
# CoM strictly inside; everything else (base default, hand point, plane,
# trunk inertia, coordinate selection) is unchanged. Recorded BEFORE the
# reseat was compiled into a scene (RULE 0 order).
_rev4 = json.loads(json.dumps(REVISIONS[-1]))
_rev4["physical"]["statement"] = (
    "Revision 4: identical to revision 3 with the two forearm support points "
    "moved onto the olecranon (elbow tip) -- local (0,+0.02,-0.012) and "
    "(0,+0.02,+0.007) on the same ulna1 record, radii 0.01277788228821517 -- "
    "because the revision-3 seat's frame-origin points made the support hull "
    "a degenerate sliver (2.2 mm CoM margin; the source arm is strictly "
    "planar, so no arm-only hull has area) and the first F1 landing run "
    "measured a sustained ledger leak (~1.8e-5 J/tick from 34 N of normal "
    "force pushing on a point receding at 8e-5 m/s) during the perpetual "
    "rocking. The olecranon seat restores real hull margins (8.39/22.21/8.42 "
    "mm, CoM strictly inside, barycentric weights 0.113/0.443/0.443). The "
    "falsified premise is recorded, not hidden: a marginal seat falsifies "
    "F4's closure bar by construction.")
_rev4["physical"]["prediction"] = (
    "At the authored seated reset all three support-point gaps sit at "
    "+2e-6 m inside the touching band, the CoM horizontal projection is "
    "strictly inside the support hull with edge margins 8.39/22.21/8.42 mm, "
    "and a zero-torque drop from 0.25 m lands, rocks decaying under friction, "
    "and settles with the ledger identities holding at the packet bar once "
    "motion ceases.")
REVISIONS.append(_rev4)


# Ladder note (2026-09-18 lane session): a revision 5 with a fourth authored
# support point (the sternum chest at local (0,-0.115,0), radius
# 0.00477788222411312, gap +2e-6 m at reset) was appended, compiled, and then
# EXCLUDED from the ladder by measured decision: the 4-point seated landing
# creates a degenerate 4-row Gram system (near-parallel vertical rows) that
# churns the D6 active-set past its cap and refuses the runtime. The
# chest-catch physics stays recorded as future work: the seated assembly
# topples backward onto the chest under mu>0 rocking, and a chest contact row
# is the honest fix, but only together with a re-derived multi-row projection
# (follow-up packet).

CURRENT = REVISIONS[-1]
PRIOR = REVISIONS[:-1]

def main() -> int:
    raw = PROGRAM.read_bytes()
    payload = json.loads(raw.decode("utf-8-sig"))
    objects = payload["objects"]
    existing = [o for o in objects if o.get("id") == OBJECT_ID]
    if existing:
        if existing[0] == CURRENT:
            print(f"{OBJECT_ID}: already at current revision (no-op)")
            return 0
        if existing[0] in PRIOR:
            objects[objects.index(existing[0])] = CURRENT
            out = json.dumps(payload, indent=1, ensure_ascii=False) + "\n"
            PROGRAM.write_bytes(out.replace("\n", "\r\n").encode("utf-8"))
            print(f"{OBJECT_ID}: superseded prior revision with current")
            return 0
        print(f"{OBJECT_ID}: REFUSAL -- exists with foreign content; "
            "graph policy is never silently overwritten", file=sys.stderr)
        return 1
    objects.append(CURRENT)
    out = json.dumps(payload, indent=1, ensure_ascii=False) + "\n"
    PROGRAM.write_bytes(out.replace("\n", "\r\n").encode("utf-8"))
    print(f"{OBJECT_ID}: admitted to {PROGRAM}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
