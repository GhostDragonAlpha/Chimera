# MAT2-M06 PREREGISTRATION — frozen before implementation and before any measurement

Frozen: 2026-09-28Z, before authoring local_contact.py, author_contact.py,
run_experiments.py, test_local_contact.py or make_report.py, before any
experiment run, and before any capture code exists. Task: MAT2-M06 / planning
id M06 — "Verify local triangle contact and finite sliding" (criteria sha256
bb695fddee166aeb79edf99c62bf6537bb24d52b3d85866f1834f0526feb9efc, attempt
4b3ed2b05f3546b190bd1cc4e9e9075c, arrival
arrival-bfbc8ae99ec54ab5870f6c05d4435671).

done_when (verbatim): "Candidate search feeds actual local surface contact,
friction and declared thin-feature/high-speed treatment. Native tests cover
resting load, oblique contact, sliding and crossing trajectories; compare
against exhaustive contact candidates on small fixtures."

Card falsifier (verbatim): "Hierarchy pruning misses contact, render-only
triangles support weight, or two-sided loads violate the declared balance."

Verification-profile falsifier (verbatim): "Unbound media, clipped load path,
hidden constraint/support, area-independent triangle forces, overlay-driven
motion, or unaccounted energy prevents acceptance."

Port contract (verbatim): "Spatial candidates + surface/material IDs ->
contact points/normals/gaps + reciprocal impulses; topology remains separate."

## Base and reconciliation (read-only, done before this freeze)

- Canonical startup assigned slot branch-1, prepared checkout head
  c525b82c7c3ce0128565424764293a3c85811ab3 (origin/branch-1). The sealed line
  (origin/astra/gait-capture tip f67a622ab37bf0f3201613701cf89028d6a8eed4) is a
  fast-forward descendant of c525b82c and carries the merged winners of this
  card's dependencies and peers: MAT2-M01 (PR #223), MAT2-M02 (PR #236, merge
  986f270e), MAT2-M04 (PR #241, merge d83ee979), MAT2-B04 (PR #242) and
  MAT2-B03 (PR #244). MAT2-M03 (pressure membrane) is NOT merged (pending on
  review/MAT2-M03); pressure law is out of M06 scope and is not invented here.
  Per the dispatch ("depend only on what is already merged"), the local attempt
  branch was fast-forwarded to f67a622a (local-only, never pushed).
- Dependency input pins verified in the checkout before this freeze:
  - MAT2-M02/monkey_arm_independent_meshes.json file sha256
    51d8231e0d1eacd7f0d4b558699f011e35ff765f5d0e07ef5889ded27216a834
    (tetra 4 triangles / 4 vertices, plate 2 triangles / 4 vertices,
    identity visual<->physical mesh declarations).
  - MAT2-M02/independent_shape_regions.json file sha256
    0f0b7165883183446b15b7043fd5471f0b12d6d992ffabc27107f4de1238887e
    (canonical object sha256 23995548570aaaac41fccfe9fb0e6cdbee1f7a3f25b151989ce4289be463ceed;
    plate shell_thickness_m 0.002, tetra mass 0.12 kg, plate mass 0.02 kg,
    `contacts` field empty at revision 1).
  - MAT2-M02/monkey_arm_regions.json file sha256
    15ae0e5a3d540d52b9a0e5c9b8af2f8a6bf7f2c9770a5f2cd7c1e9e8758366f1
    (7-region compiled arm; used for surface-ID vocabulary and the
    candidate-vs-exhaustive sweep over real compiled geometry).
  - MAT2-M01/material_state.py (schema authority) file sha256
    b6b009713daa4b315c6b5cb43c7ad4e756123b50edcdd802eeebd55c6afd6c40.
  - MAT2-M04/passive_law.py file sha256
    a89d9000e2856803b3bb808aef6269793b177ba00502617f721a029f9e0f0464.
  These hashes are frozen inputs; a mismatch at run time refuses
  `input_pin_drift` (no silent rebase onto different inputs).
- Reconciled gap this card fills: the compiled material_state documents declare
  an EMPTY `contacts` field and no contact solver exists anywhere on the sealed
  line (rest == current by declaration in M02; M04 evaluates passive material
  response on a pinned gauge with no contact). M06 adds the first local
  triangle-surface contact law: candidate search, local contact geometry,
  friction, declared thin-feature/high-speed treatment, reciprocal impulses.
- Pinned-input property read now (input identity, not a measurement): the
  pinned plate's two triangles have bitwise-equal areas
  (both 0.010000000000000002 m^2, computed from the pinned blob above) and
  identical +z normals. The frozen area-split predictions below rely on this.

## Frozen statement

M06 implements ONLY local surface contact between declared triangle soups
(shells) with rigid per-body translation kinematics (no rotation dynamics, no
deformation, no pressure law, no GPU residency, no render-engine integration).
The contact law consumes candidate pairs from a sweep-and-prune AABB candidate
search over the ACTUAL physical triangle lists (the pinned M02 identity rule:
visual mesh == physical mesh; a "render-only" triangle set is refused), solves
local triangle-triangle closest-feature contact (points, normals, gaps),
applies Coulomb friction (static/kinetic, pair rule = elementwise min), a
declared thin-feature treatment (midsurface gap with per-surface thickness
inflation, thickness pinned from the compiled `shell_thickness_m`), a declared
high-speed treatment (per-tick swept continuous collision detection, so
crossing trajectories cannot tunnel), reciprocal impulses (every impulse is
applied half to each body; pinned bodies emit an anchor reaction into the
ledger), area-scaled per-triangle force distribution (contact patch load
split by triangle area share), and a closed energy/momentum ledger. The result
is a versioned document `chimera.local_contact.v1` (declarations + contact
records) written by an offline, CPU-only, stdlib-only deterministic
executable, per the M01/M02/M04 precedent for "native tests" at this stage.

## Frozen declarations (constants of the law; all declared BEFORE measurement)

- g = 9.81 m/s^2 (down +z is up in fixtures: gravity acts along -z).
- Tick dt = 0.005 s for all dynamic scenarios.
- Shell thickness h = 0.002 m (pinned from MAT2-M02
  independent_shape_regions.json shell_thickness_m); gap between two shell
  triangles = distance(mid_surfaces) - (h_A + h_B)/2; touching when gap <= 0.
- Contact margin/slop s = 1e-5 m; Baumgarte bias coefficient beta = 0.2
  (heritage: G3 deterministic Baumgarte solve, estimator B penetration proxy,
  docs/THE_MASTER_LIST.md H7 stage 3, agent_logs/kimi/contact_ref_01.md).
- Restitution e = 0 (declared inelastic; no bounce).
- Friction: per-surface declarations block (mu_s 0.6, mu_k 0.4), plate
  (mu_s 0.7, mu_k 0.5); pair rule elementwise min -> pair (0.6, 0.4).
  Stick when required tangential impulse <= mu_s * Jn, else slip at mu_k * Jn.
- High-speed/CCD: swept segment-triangle advancement per tick with thickness
  inflation; declared capture bound: per-tick relative motion up to 0.02 m
  (10x thickness) must be caught.
- Candidate search: sweep-and-prune on triangle AABBs (axis chosen by largest
  variance), inflated by max(per-tick motion, thickness) so the same routine
  covers static and swept queries; narrow phase sees ONLY candidate pairs.
- Per-triangle force split: contact impulse distributed over the contacted
  body's triangles by area share a_i / sum(a_contacted); equal areas -> equal
  forces; the pinned plate areas are bitwise equal (verified above).
- Seeds (determinism): one hash-free 64-bit LCG (state = seed*6364136223846793005
  + 1442695040888963407 mod 2^64; uniform doubles from the top 53 bits);
  randomized sweep S1 uses seed_base 20260928 with scene k seeded
  seed_base + k, k = 0..31. No wall-clock, no other randomness anywhere.

## Frozen experiments and predictions (limits fixed before any run)

- X0 candidate-vs-exhaustive, pinned compiled geometry: over the pinned
  independent-shape meshes (tetra+plate in their compiled default pose, 8
  cross-body triangle pairs) and over the 7-region compiled arm (42 shell
  triangles, 21 cross-region pairs at the declared region granularity), the
  candidate set from sweep-and-prune must be a SUPERSET of the exhaustive
  all-pairs narrow-phase contact set (recall 1.0, no missed pairs); every
  produced contact's pair must be in the candidate set (narrow phase fed only
  by the search); pair counts recorded. Fixture-labeled: these are fixtures.
- S1 randomized recall sweep (small fixtures, seeded): 32 seeded scenes, each
  3 bodies x 2-4 triangles (12 triangles max, 66 pairs) under random rigid
  offsets in a 0.5 m box with rotations up to 30 deg, half the scenes with
  relative motion up to 0.02 m/tick: recall vs exhaustive all-pairs sweep = 1.0
  on EVERY scene (zero missed contacts; a single miss fails the run).
- X1 resting load (native test 1): declared block (2 triangles, mass
  0.12 kg = pinned mass_tetra value) settles onto the pinned-geometry plate
  (2 triangles, pinned support). Frozen limits after settle:
  per-tick normal impulse Jn = m*g*dt = 0.005886000000000001 N·s within
  1e-12 relative; total support force = m*g = 1.1772 N within 1e-9 relative;
  the two plate triangle forces are equal within 1e-12 (pinned bitwise-equal
  areas), each 0.5886 N within 1e-9 relative; steady penetration <= 1e-4 m;
  anchor (pinned-support) reaction closes the momentum ledger: sum of all body
  momentum changes + anchor impulses = 0 within 1e-12 per component per tick.
- X2 oblique contact (native test 2): block impacts the plate at 30 deg
  incidence, speed 0.5 m/s (v_n 0.25, v_t 0.4330127018922193 m/s). Frozen:
  contact normal within 1e-9 of the plate +z normal; post-impact normal
  velocity |v_n'| <= 1e-12 (e = 0); slip regime (required stop impulse
  m*0.433 > mu_s*Jn = 0.6*0.25*m), post-impact v_t = 0.3330127018922194 m/s
  within 1e-9; impulse direction inside the friction cone (|Jt| <= mu*Jn
  with the declared pair mu used, within 1e-12).
- X3 sliding, finite (native test 3): block with v0 = 0.5 m/s purely tangential
  on the plate under gravity with pair mu_k = 0.4. Frozen: measured stop
  distance d within v0*dt = 2.5e-3 m of the analytic oracle
  d = v0^2/(2*mu_k*g) = 0.031855249745158 m; block stops (|v| <= 1e-12) and
  stays stopped for >= 50 further ticks (no creep, Jn steady at m*g*dt);
  friction work W_f = mu_k*m*g*integral(v dt) equals the initial kinetic
  energy 0.015 J within 1e-9 J; sliding displacement per tick finite and
  bounded by v0*dt; total ledger residual <= 1e-9 * scale (declared contact
  correction work recorded as its own term, never hidden).
- X4 crossing trajectories (native test 4, thin-feature/high-speed): two
  2-triangle shells (thickness 0.002 m each) approach head-on along z at
  2 m/s each (closing 4 m/s; per-tick approach 0.02 m = 10x thickness; equal
  masses 0.02 kg = pinned mass_plate value). Frozen: the CCD path detects the
  crossing at or before mid-surface overlap in EVERY of 5 offset variants;
  post-resolution non-penetration (gap >= -1e-5 m) at every later tick;
  post-impact both velocities zero within 1e-12 (e = 0, equal masses) and
  total momentum conserved within 1e-12 per component; a declared
  negative-control mode (CCD disabled) must MEASURABLY tunnel (used only as
  the tamper/control arm, recorded, never passed as the law).
- P7 area scaling: resting block centered on the pinned plate -> per-triangle
  forces equal within 1e-12; authored twin plate with triangle areas 0.01 and
  0.02 m^2 -> force split ratio exactly 2.0 within 1e-12; zero/negative area
  refused `zero_area_interface`.
- P-identity: contacts carry surface_id (region id), triangle indices,
  matter/material ids from the compiled matter_claims; contact rows against
  the pinned independent-shape vocabulary use exactly the ids
  {tetra, plate}; an unknown surface id is refused `unknown_surface_id`.
- P-determinism: run_experiments.py twice -> byte-identical
  experiment_trace.json and experiment_receipt.json (no wall-clock, seeded
  LCG only).
- P-regression: the UNMODIFIED M01, M02 and M04 suites re-run green in this
  checkout on the exact candidate revision.

## Frozen falsifier arms (each bitten on a TAMPERED COPY, discarded after)

- F1 "hierarchy pruning misses contact": a sweep-and-prune copy that drops the
  last candidate per axis must be caught by X0/S1 (recall < 1.0 fires); the
  untampered module stays green.
- F2 "render-only triangles support weight": feeding a visual-only triangle
  subset (one plate triangle dropped from the physical soup) must fail X1's
  weight support (support force < m*g beyond tolerance or the block falls
  through) and the identity guard must refuse a non-identity
  visual-to-physical mapping when one is declared.
- F3 "two-sided loads violate the declared balance": a one-sided impulse copy
  (reciprocal half dropped) must fire the momentum-ledger check in X1/X4.
- F4 "friction removed": mu forced to 0 must fire X3 (block never stops within
  the frozen distance; W_f ~ 0).
- Profile-falsifier arms: unbound media (every capture view binds a sha256 of
  the solver trace), clipped load path (measured camera margins reported per
  view), hidden constraint/support (pinned plate rendered and labeled in the
  whole/side views), area-independent triangle forces (P7), overlay-driven
  motion (fixed-bookmark cameras; geometry moves only per the sha-bound
  solver trace), unaccounted energy (X3 ledger + F3 ledger).

## Frozen verification-profile probes and views (material, motion)

- Views (registry profile, verbatim): "whole experiment at fixed distance",
  "orthogonal side and front", "oblique close-up of the loaded interface";
  each rendered as a diagnostic/clean pair (clean_view_required true).
- Diagnostic layers: ALL FIVE registry layers carried in the diagnostic rows:
  stable membrane/triangle/port IDs; pressure and area-scaled force vectors;
  rest/current geometry and material directions; contact/bond state;
  energy/work and simulation tick (B04's correction round is binding).
- Capture: task_id short form "M06"; solver states rendered from the
  experiment trace only; lossless FFV1 Matroska at 1 fps from hashed PNG
  frames 1280x720; capture_sha256 = the video file's sha256 (single on-disk
  artifact); cameras orthographic with all required fields; validate_manifest
  runs with the profile object read read-only from
  E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3
  kanban.cards[MAT2-M06].spec.ontology_qualification.task.verification_profile.
- Frozen capture scenario (solver-driven motion for the motion profile): the
  X3 sliding run (block decelerating from 0.5 m/s to rest under friction) over
  its full tick range; the loaded interface close-up binds the SAME trace.

## Applicability boundary (honest, frozen)

Offline CPU-only contact experiment executable over pinned M02 surfaces and
authored small fixtures; not the native C++ engine, no GPU residency, no live
renderer, no runtime integration, no training; rigid-translation kinematics
only. "Native tests" at this stage means the campaign's own named executable
checks actually run here (M01/M02/M04 precedent); runtime-facing integration
remains with the downstream native-runtime cards and is NOT claimed.
