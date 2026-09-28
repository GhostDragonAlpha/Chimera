# MAT2-M04 report — passive resistance and directional material response

Attempt 262e9d2a30ae4c4b82d84de7de9661a1, arrival
arrival-9c8ab01ecb754d6792806d29ae3fc332, criteria sha256
e9faa5bcb3926b2cdcd68f110c2c9480bb7b7d18e40a2623beb5ff5ce978a665. Isolated
attempt checkout of E:\PythonChimera, canonical startup slot branch-3,
prepared base c525b82c7c3ce0128565424764293a3c85811ab3; per the dispatch
("depend only on what is already merged") the local attempt branch was
fast-forwarded to the sealed line tip 986f270ef24cda0008c52bd40d4b6d08565c06
92 (= registry MAT2-M02 winner merge, PR #236, which contains the merged
MAT2-M01 schema and MAT2-M02 compiler). No pushes, no PRs, no writes outside
the attempt workspace.

Preregistration (PREREGISTRATION.md) was committed (e1b940cd) BEFORE the
implementation existed and before any measurement. The capture predictions
(PREDICTIONS.md in the capture workspace, with pre-render amendments A1-A3)
were frozen before any capture code produced a frame.

## done_when clause map (all clauses executed on the exact candidate revision)

| clause | execution | result |
|---|---|---|
| only the rigid, compliant and fiber-reinforced responses needed by the monkey | exactly three profiles: arm's seven bone regions -> rigid (no soft tissue exists in the compiled arm; none invented); tetra -> compliant_maxwell (+ fiber variants for the directional gate); plate keeps pinned geometry, its areas feed the area-scaling oracle only | arm_rigid_laws.json (7 rigid, 0 other), independent_shape_laws.json (G-TETRA gauge); no active/pressure/thermal/plastic response implemented (inventoried) |
| declare constitutive equations, parameters, source or synthetic status | declaration table frozen in the preregistration and embedded per profile in the law documents (Hooke + Maxwell series + E(theta)=E_trans+(E_fiber-E_trans)cos^2; E=5e5 Pa, E_fiber=2e6, E_trans=5e5, k=2.5e4 N/m, c=6250 N·s/m, tau=0.25 s; all synthetic_authored) | validator requires constitutive_equation + parameters + source_status per profile (P1) |
| rest state | zero load -> extension 0, force 0, stored 0, dissipated 0, history unchanged; declared in every profile row | P9 green (bitwise) |
| damping | linear Maxwell series dashpot, c=6250 N·s/m, tau=0.25 s, declared ONLY on compliant_maxwell; null (never silently zero) on rigid/fiber | P1 damping assertions green |
| valid strain range | [-0.30, +0.30] declared; gate refuses `outside_valid_strain_range` BEFORE any state update; all test loads inside (max eps 0.10 in E1, 0.1632 in protocol V) | P9 green |
| independent load-extension, relaxation and rotated-fiber experiments meet preregistered limits | E1 (five cases x four loads, closed-form oracle), E2 (position ramp + hold, exact exponential integrator vs closed form), E3 (fiber 0/45/90 deg) — three separate runs, separate oracles | all frozen numbers reproduced; see below |

## Frozen numbers reproduced (exact candidate revision)

- E1: x = F/k with k = 2.5e4 / 1.0e5 / 6.25e4 / 2.5e4 N/m (compliant,
  fiber0/45/90); rigid exactly 0 with bitwise force transmission; linearity
  x(2F) = 2x(F) bitwise; ordering 0 < fiber0 < fiber45 < fiber90 =
  compliant (<=1e-12) at every load; over-band load 1.0e4 N refused.
- E2: F(ramp end, t=0.2 s) = 34.416939742673655 N; F(hold end, t=1.2 s) =
  0.6303682399821345 N = F_ramp·e^-4; W = 0.038957650643315876 J;
  U(ramp) = 0.023690514825016586 J; U(end) = 7.947282359563479e-06 J;
  Q = 0.038949703360956316 J; ledger residual 6.9e-18 J (bound 1e-9·W);
  independent closed-form integral oracle Q_ramp + Q_hold agrees.
- E3: x(0°)=0.0005, x(45°)=0.0008, x(90°)=0.002 m; strict ordering; ratio
  x90/x0 = 4.0 exactly (= E_fiber/E_trans); E(45°) = 1.25e6 Pa exactly;
  mirror symmetry and load/fiber frame equivariance bitwise.
- P7 area scaling: pinned plate triangles 0.01+0.01 m^2 -> 25 N + 25 N
  bitwise; doubled-area twin 100/3 + 50/3 N; zero/negative area refused
  `zero_area_interface`.
- P8 density independence: every E1 number bitwise invariant; the evaluator
  AST contains no density/mass identifiers.
- P10 determinism: run_experiments.py twice -> byte-identical
  experiment_trace.json + experiment_receipt.json (no wall-clock, no RNG).

## Checks run (exact commands, candidate revision)

From the attempt checkout root with /c/Python314/python:

1. `python -B tools/monkey_campaign/contributions/MAT2-M04/run_experiments.py`
   -> E1/E2/E3 + interface oracle + protocol V all green; emits
   experiment_trace.json + experiment_receipt.json.
2. `python -B tools/monkey_campaign/contributions/MAT2-M04/test_passive_response.py`
   -> "checks: 157/157 passed ... ALL FROZEN PROBES GREEN (P1-P12, F1-F3)".
   P12 re-runs the UNMODIFIED M01 and M02 frozen suites in this checkout
   (both green: M01 "35 named checks, 0 failed"; M02 142/142).
3. `python -B tools/monkey_campaign/contributions/MAT2-M04/author_laws.py`
   -> emits the three law/direction documents + passive_law_display.json;
   the directions document validates through the UNMODIFIED M01 validator
   (direction_count 3, law_count 0).

## Falsifier proof (card falsifier, each arm bitten on a TAMPERED COPY)

Tamper copies are written to the attempt scratch
(scratch-falsifiers/), mutated by exact source replacement, probed, logged
(scratch-falsifiers/FALSIFIER_LOG.json) and the copies discarded:

- F1 density substitutes for stiffness: density-coupled k moves the 50 N
  extension from 0.002 m to 2e-05 m at factor 100 — the frozen closed-form
  oracle catches it; identical to the real module at factor 1; the real
  module has no density path (green under P3+P8).
- F2 rotated fiber has no effect: an isotropic shortcut collapses
  x(0)=x(45)=x(90)=0.0005 m (ratio 1.0, not 4.0) — P5's strict ordering
  fails loudly; input-side zero and non-unit fiber axes refuse
  `invalid_fiber_axis`.
- F3 passive material creates unexplained energy: a sign-flipped ledger
  refuses the green E2 trace (`unexplained_energy`); the real module accepts
  the green trace and refuses negative dissipation, ledger residual, and
  negative stored energy with named codes.

Verification-profile falsifier arms: unbound media (trace sha binding),
clipped load path (measured margins >= 3.05% every side, evidence/
margins.json), hidden constraint/support (pinned support plates rendered and
labeled in whole/side views), area-independent triangle forces (P7),
overlay-driven motion (fixed bookmark cameras; geometry moves only per the
sha-bound solver trace; predicates refuse otherwise), unaccounted energy
(P6/F3 ledger).

## Motion-profile capture (visual evidence, material profile)

Built per the M01/M02 discipline in
E:\ChimeraWork\monkey-coordination\kanban-attempts\MAT2-M04\
262e9d2a30ae4c4b82d84de7de9661a1\capture-evidence-20260928\ (PREDICTIONS.md
frozen before capture code; full record in its EVIDENCE.md):

- Real 3D orthographic renders of the pinned tetra displaced ONLY by the
  protocol-V solver trace (force ramp 100 N/s, ticks 0..12, dt 0.1 s); 6
  manifest views (3 profile view ids x diagnostic/clean), 78 lossless FFV1
  frames 1280x720, 78 s at 1 fps (each row window replays all 13 solver
  states); ffprobe-verified 78 frames / 78.0 s.
- Solver-driven motion predicates refuse before assembly (monotone, rigid
  control bitwise static, ordering at loaded ticks, force record).
- Cameras: whole 3/4 view at 3.0 m (Amendment-A2 span formula, fit factor
  1.065, >= 3.05% margin/side, Amendment-A3 one-step recentering);
  orthogonal front [0,0,-1] + side [1,0,0]; oblique 25 deg close-up of the
  loaded interface (span 0.05 m) whose target AND labels come from ONE
  function (loaded_endpoint); the loaded vertex travels about 209 px across
  the close-up row — the visible solver-driven motion.
- task_id "M04" (SHORT form) in manifest and context;
  visual_capture.validate_manifest with the registry profile read read-only
  from card MAT2-M04: structurally_valid=True, fired=[], capture_kind video,
  view_count 6, visual_acceptance=false (acceptance belongs to the
  independent visual reviewer).
- Key hashes: video 506e58e2db26be3ce4382c81ee47f78c3c8b44121061df5a7f3b350
  397b7f710; rendered trace d08d049a1e9218e0a3bdf54c012dff73fa68620eb8077773
  edddb8502ecc4d79; solver trace copy faf952243e87d9b881985a23aee39bf37d41f8
  fbe8a1b415f0119be10de6546f; subject
  ae396848907319c758491c17d1a4a52769e0e9ffd625cc954db6e39d8ef7a18c.

## Reconciliation notes

- Filled M02's inventoried absences exactly: material directions (now three
  declared fiber axes, emitted through the UNMODIFIED M01 direction schema)
  and the first passive response evaluator (M02 had rest == current by
  declaration).
- M01's `laws` vocabulary is closed at 'pressure_deformation' (reserved by
  M03, implemented in parallel). Passive laws therefore live in the M04-owned
  `chimera.passive_law.v1` document pinning the M02 inputs by canonical
  sha256; the mapping into material_state.v1 law rows is recorded as future
  serial-integration work, not claimed done.
- Heritage cited from real pins: B1 scratch law (d = F/(2·pi·R·H_soft),
  loads declared never inferred), B2 bonds-are-materials (capacity =
  strength x area; P7's area scaling), B3 tensile web, B4 tension-only drape
  (sha256 of each preregistration file recorded in PREREGISTRATION.md);
  graph contracts concept.elasticity, req.material_catalog (tendon
  fiber_solid, bone composite_solid), type.B15.

## Honest limitations

- Offline CPU-only material experiment executable over pinned M02 documents;
  not the native engine, no GPU, no runtime integration, no training.
- Constitutive parameters are synthetic authored models (no source modulus
  is admitted for monkey tissue in the graph); only geometry, masses and
  mesh data are pinned heritage.
- Uniaxial gauge kinematics (affine stretch about a pinned face) is a
  declared experiment rig, not a general 3D constitutive solver; the five
  capture columns are the same specimen under declared display offsets.
- No viscous damping on the fiber profile (declared elastic anisotropy);
  no plasticity, fracture, thermal, or active response (out of card scope).
- visual_acceptance is false by design in the validator receipt; independent
  visual acceptance is outstanding.

## File identities (sha256, computed at commit time; recorded in the handoff)

Commit chain on local branch-3 (attempt branch): e1b940cd (preregistration
freeze) -> 7402c364 (implementation + frozen capture predictions checkpoint)
-> final candidate head (see handoff message). Capture artifacts live in the
attempt workspace, not in the contribution.
