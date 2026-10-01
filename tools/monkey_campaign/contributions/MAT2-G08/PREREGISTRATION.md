# PREREGISTRATION - MAT2-G08 (Qualify climbing dynamics and numerical budget)

Frozen BEFORE implementation and before any experiment run. Composed against
CARD_STARTER.md v3; house standards IMPLEMENTER_CHECKLIST.md (G1-G9) and
TOOLKIT.md (P1-P9) will be cited at the candidate commit. Package base:
`5f82a3ddb35aac8b59bc4b087a90353e1fb69c1d` (= origin/review/MAT2-G08 as seeded
by the publisher; the integrated line carrying the merged G-chain winners:
G01 PR #296, G04 PR #298, G05 PR #300, F05 PR #302, G07 PR #303, G06 PR #305).
Attempt `1b58946be29847c681b41f9c5a15861b`, agent `wk-g08-arrival-1`
(arrival wk-g08-assembly), criteria_sha256 `f2a89774038270b2665c70ec8ff2a8a`
`521aec21fde5b9bc229e4faea84bdbbcb`, ontology scope_sha256
`cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097`.

done_when (verbatim): "Accepted mechanics pass CPU/GPU and runtime identity
gates relevant to climbing"

Card observation (verbatim): "Do not inherit walking certification for changed
hand/contact dynamics". Profile falsifier (verbatim): "Unresolved owner,
nonphysical attachment, unsupported transfer, concealment behind the trunk or
force/pose inconsistency fails." Profile procedure (verbatim): "Replay
approach, attach, load, hold, transfer and release with attachment and force
telemetry. Use the task-owned subset of layers/behaviors. Inventory absent or
unresolved components explicitly; do not require downstream skills to accept
an upstream interface. Freeze exact applicable probes and views before
execution."

This is the G-chain INTEGRATION card. It claims no new physics and fills no
named absent variable. The accepted mechanics are the sealed upstream
behaviors (G04 grip, G05 observation, G06 supported transfer, G07
release/fall, G01 feasibility boundary, F05 terrain/matter declarations); the
card ASSEMBLES them in one deterministic CPU process, re-passes their identity
gates ON THE ASSEMBLED LINE, and derives the per-operation numerical budget.
Ontology calculations are consumed at their recorded inventory status: C09
(CPU/GPU parity and time stepping) -> the CPU backend is certified HERE
(section 6 identity gates + section 7 budget); the GPU device leg for the
climb contact path is an UNRESOLVED component (section 10; the sealed GPU line
M08-M12 certifies material/actuator/limb/LOD worlds, not the trunk/pad climb
fixture, and this card is CPU-only by runner law). C20 (vertical transfer and
climbing load) -> carried by the assembled G06/G07 segments. C05 (joint
kinematics) -> NO joints exist in this fixture; inventoried ABSENT, never
faked (G04/G06/G07 inheritance). C06 (articulated dynamics and force
accounting) -> carried at the fixture level by the pinned M06 solver ledger
(the full-tick impulse identity); the creature articulated chain stays ABSENT.

## 1. The established interfaces (imported, hash-asserted, never forked)

- THE SOLVER: MAT2-M06 `chimera.local_contact.v1` (`local_contact.py`, raw
  sha256 `1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc`)
  -- imported at run time, sha asserted, never forked. Every impulse on this
  card comes from `lc.solve_tick` (through the pinned upstream runners).
- THE GRIP PHYSICS + FIXTURE: MAT2-G04's sealed `grip_contact.py` (sha256
  `0d6375484c350039468b31a2f7db2895d3365412aee52ce98de72b4173d69245`), PR
  #298. G08 consumes its trunk loader, facet channels, pad placement, press
  operating point, closed forms, named-absent list and windows. No new
  geometry, no new mu source.
- THE OBSERVATION TABLE: MAT2-G05's sealed `contact_support_obs.py` (sha256
  `3dae0a3805cec86bba8dbae9a6fc563f43cddc98fcd01a693f725e4f31c46bd3`), PR
  #300, with the G05 seam law family. G08 does not modify it and does not
  re-declare the W04 TC-2 interface.
- THE SUPPORTED TRANSFER: MAT2-G06's sealed `transfer_sequence.py` (sha256
  `a3f376f9feafc07897ea331219320b6393bfb69916781a6beb80792c7bd068f9`), PR
  #305 -- its schedule, handover law, seam extension and verdict projection
  are imported and executed unmodified.
- THE RELEASE/FALL ACCOUNT: MAT2-G07's sealed `release_fall_account.py`
  (sha256 `78b5cc66f7019fa181765eb0366fe6c98525941840f57723d0ae99cb55b2a8c5`),
  PR #303 -- its hold/release account, free-fall identity, CCD event recording
  and seam delivery are imported and executed unmodified.
- THE SEALED BOUNDARY: MAT2-G01's pinned feasibility receipt (sha256
  `4061d8ec604ddea5dfbdf605f0244874129a69a88d771d4f593c7a927c16be42`) -- its
  case table remains the transfer-admissibility authority.
- THE TERRAIN/MATTER DECLARATIONS: MAT2-F05's sealed `implementation.py`
  (sha256 `d07acb20f4e0a4e813afc8783fff4098eae531f0c808ac6e6e67242a3342d529`)
  and `report.md` (sha256
  `0a640c131f067241d3d20f595bd825e2e4319102cc2d200ac04805f702c6ba6d`), PR
  #302 -- bound as DATA: the declared climbable-trunk matter row
  (`wood_trunk_01` 0.6/0.6), the probe-shell row (0.6/0.4) and the elementwise
  min pair rule (pinned `contact_law.json`) must equal the fixture constants
  the assembled line actually runs with (section 5, matter identity).

The certified measured-value bindings (section 6 identity gates) read the
sealed upstream receipts and traces AT RUN TIME: G06 `experiment_receipt.json`
(sha256 `cf5c9cc5b7d51a23f282313974f853edca83ca30c19edd51a36eb9ddf0d3feff`) +
`experiment_trace.json` (sha256
`eec274ded637a4cb10049bc7d427037e3a1e54e72a3c11b55ddf80ec5d18f2f9`); G07
`experiment_receipt.json` (sha256
`c539617b098190918187d9a7dcbb0a5e33a85998adaa58f6b781703bbdeb88f8`) +
`experiment_trace.json` (sha256
`b8a9e139d85bd7cc116ea3d6ca94f655e41ec7ae67c15f7686e057ca0706eb9b`); G06
`falsifier_receipt.json` (sha256
`97b95e09481e7f02dfd873470b49cb114e2c856aa4fc0cf04bb2d6caeed004bf`); G07
`falsifier_receipt.json` (sha256
`3f23c828de4845d175c5c92ef8d921768596997d80f0b970ec1f147ab77fe1cc`). All
eight resolve from the package base tree (`git cat-file`, read-only).

## 2. What "the assembled line" means on this card (declared model)

ONE deterministic CPU process executes the composed qualification battery:

- SEGMENT T (supported transfer): the sealed G06 battery VERBATIM -- 9
  scenarios x 229 ticks, frozen order (band_lo/band_mid/band_hi/scene x n=2,3,
  then the zero-mu control `band_mid|n=3|mu=0` last), each run through the
  pinned `ts.run_case` on the pinned M06 solver with the frozen G06 schedule,
  handover events, climb channel, P6 verdict projection and seam deliveries.
- SEGMENT R (release/fall): the sealed G07 battery VERBATIM -- 13 scenarios x
  60 ticks (hold 20 + release 40), each run through the pinned G07 account
  machinery (`observe_with_account`) with the G05 seam delivery and the CCD
  event recording.

The assembly identity claim is PROCESS- AND BYTE-LEVEL, not a new schedule:
the same solver, the same pinned modules, one process; the assembled per-tick
rows must REPRODUCE the certified rows (section 6, A1). G08 adds NO schedule,
NO injection-free re-timing, NO new force channel. The segment composition
value is the parts no individual card could claim: the union ledger over all
2841 assembled ticks (22 runs), the cross-segment identity bindings, the
whole-line continuity law, the unsupported-state disclosure over the union,
and the per-operation numerical budget derived across every window.

The certified line visits unsupported states BY DECLARATION (G06 release
phases and its honestly-slipping cases; G07 release phases and its zero-mu
slip control). The W09 disclosure class (a certified line visiting unsupported
ticks) is handled by LEDGER, not by assumption: every assembled tick records
its support verdict, every unsupported tick must carry a DECLARED response
class (section 6, A4), and the walking certification is NOT inherited
(observation verbatim): the hand/contact dynamics here are the fixture pads
of the sealed grasp line, certified on their own receipts.

## 3. Frozen fixture (declared, inside the approved architecture)

Exactly the sealed G04 fixture as consumed by G06/G07: the F03 trunk mesh
(lateral facets), pad tetrae on `channel_facets(geom, n)`, pad matter
`grip_fixture_placeholder_mu` (mu 0.6/0.4, the M06 block declarations),
trunk matter `wood_trunk_01` (0.6/0.6), `SOLID_THICKNESS_M = 0.0`, the G04
press operating point `PRESS_JN_NS = 0.30`, M06 G = 9.81, DT = 0.005 s.
No floor body exists in this fixture (G07 honest limitation inherited): NO
impact landing is modeled or claimed; falls descend alongside the trunk inside
the declared windows. No creature anatomy exists; reach/aperture/tendon/joint
quantities stay ABSENT with their recorded owners.

MATTER IDENTITY (F05 binding, frozen): the assembly asserts at run time
`gc.TRUNK_MU_S == 0.6`, `gc.TRUNK_MU_K == 0.6`, `gc.PAD_MU_S == 0.6`,
`gc.PAD_MU_K == 0.4`, `gc.TRUNK_MATTER == 'wood_trunk_01'`, and that the
pinned F05 report declares the climbable trunk matter row `wood_trunk_01`
0.6/0.6 and probe shells 0.6/0.4 under the elementwise-min pair rule
(`contact_law.json`). A mismatch refuses `matter_identity_drift`.

## 4. Frozen assembly battery (frozen order; M06 G = 9.81, DT = 0.005 s)

22 solver runs, 2841 ticks total, in THIS order:

1. T1..T8: the eight G06 transfer cases in `battery_cases` order
   (`band_lo|n=2`, `band_lo|n=3`, `band_mid|n=2`, `band_mid|n=3`,
   `band_hi|n=2`, `band_hi|n=3`, `scene|n=2`, `scene|n=3`), 229 ticks each.
2. T9: the zero-mu control `band_mid|n=3|mu=0`, 229 ticks.
3. R1..R13: the thirteen G07 release scenarios in the declared G07 battery
   order, 60 ticks each.

No RNG, no wall clock in trace/receipt. Refusals are named codes; vacuous
comparisons are REFUSED (`vacuous_comparison_refused`).

## 5. Preregistered predictions (the assembled line must satisfy ALL)

P1 (matter identity, section 3): the fixture constants equal the pinned F05
declared rows; refusal `matter_identity_drift`.

P2 (transfer envelope): in the assembled T segment, the transfer-phase
support verdict equals the pinned G06 receipt verdict for every one of the 9
cases (three band n=3 cases supported; every n=2/scene case and the zero-mu
control honestly unsupported), and the G01 `(reading, n-1)` composition law
holds on every assembled transfer tick.

P3 (release law): in the assembled R segment, the delivered release flag
flips exactly at tick 21 in all 13 scenarios; every unobstructed release tick
satisfies the free-fall recursion (window 1e-9 m/s) and the closed-form
displacement (window 1e-9 m); the press work in the release phase is exactly
0.0 J; the release-tick pad impulses sit inside the sealed share-scaled bars
(1e-10 N*s per kg).

P4 (line identity): the assembled per-scenario physics rows are BYTE-IDENTICAL
to the certified rows (canonical-JSON hash equality per scenario) against the
pinned G06 trace (T1..T9) and the pinned G07 trace (R1..R13); structural
facts (verdict booleans, event ticks, seam accepted/refused counts, collision
event count and ticks) EQUAL the certified receipt values exactly.

P5 (whole-line continuity): every assembled tick of every run satisfies the
pose-continuity identity inherited from the sealed upstream laws (the G07
window 1e-9 m on unobstructed ticks; the recorded G06 flight closed forms in
window); a violated tick refuses `assembly_continuity_violation`. There is no
hidden reset anywhere on the assembled line.

P6 (unsupported-state ledger): the assembled union ledger records supported
vs unsupported per tick per run; the ledger totals EQUAL the totals recomputed
from the pinned certified traces; every unsupported tick carries exactly one
DECLARED response class: `declared_release` (press off, free-fall/slip
recursion armed), `declared_solver_slip` (the sealed G01 OUTSIDE-CONDITIONAL
slip executed by the solver with its recursion), or `declared_flight_hover`
(the recorded climb channel with the full-tick ledger armed). An unsupported
tick with no declared class refuses `unsupported_state_unexplained`.

P7 (event localization): the declared event set -- G06 handover tick 31,
handover-back tick 193, release start tick 220 (per T run); G07 release start
tick 21 (per R run); the two certified CCD collision events (scene|n=1 tick
60; band_mid|n=3|mu=0 tick 56) -- localizes in the assembled trace at exactly
the certified ticks; a mismatch refuses `event_localization_mismatch`.

P8 (reference-math): the record-g vs standard-g composition no-flip check
(the G06 X2 form) holds across the assembled transfer table; the declared
force conversion jn/DT = 60.0 N holds at every established press operating
point on the assembled line (window 1e-6 N, the G06 recorded bar).

P9 (seam union): every assembled tick is delivered through its segment's
declared seam; the union census (accepted/refused, refusal codes) EQUALS the
certified census recomputed from the pinned traces/receipts (G06: 2061
accepted, 0 refusals, G05 composition 270 accepted / 1791 refused all
`timing_unbound`; G07: 780 accepted, 0 refusals); the x_* namespace stays
refused live (`named_absent_occupied`); no privileged name is delivered.

P10 (numerical budget): for EVERY operation class in section 7 the measured
worst residual over the WHOLE assembled battery sits inside its frozen
window; the receipt reports measured value + window + margin. A measured
operation with no frozen window refuses `budget_window_absent`.

P11 (determinism): two independent full assembly runs produce BYTE-IDENTICAL
traces; receipt deltas scoped to the declared augmentation keys ([] plus the
run-id-free measured blocks).

## 6. Named checks (test_g08_checks.py; executed, none skipped)

- A1 line_identity: P4 (byte-identical rows + exact structural facts vs the
  pinned certified receipts/traces).
- A2 transfer_envelope: P2 (assembled G06 verdicts + G01 composition).
- A3 release_and_fall: P3 (assembled G07 release account).
- A4 unsupported_ledger: P6 (the union ledger; declared response classes;
  W09-disclosure handling by measurement).
- A5 continuity: P5 (whole-line continuity; the anti-teleport law).
- A6 event_localization: P7.
- A7 reference_math: P8.
- A8 seam_union: P9.
- A9 numerical_budget: P10 (the budget table, measured).
- A10 determinism: P11.
- P-class: seam law, named-variable law (the ten G04-inherited absent
  variables carried ABSENT verbatim), input pins at run time (refusals:
  `input_pin_missing`, `input_pin_drift`, `interface_pin_missing`,
  `interface_pin_drift`, `dep_pin_missing`, `dep_pin_drift`),
  prereg-identity (criteria_sha256 identical across dispatch, registry, this
  preregistration and checks).

## 7. The numerical budget (C09 deliverable; frozen windows, MEASURED values)

The budget table lists every operation class with its frozen window (verbatim
from the pinned sealed modules) and the measured worst residual over the whole
assembled battery:

| operation | frozen window | source module |
|---|---|---|
| press establishment jn == P | 1e-9 N*s | G04 WIN_JN |
| stick arrest vt | 1e-12 m/s | G04 WIN_VT |
| slip/free-fall velocity recursion | 1e-9 m/s | G04 WIN_RECURSION_V |
| displacement recursion (post tick 1) | 1e-9 m | G04 WIN_DISP |
| full-tick ledger identity | 1e-12 N*s | G04/G06 WIN_LEDGER |
| post-release jn/jt zero bar | 1e-12 N*s | G04 WIN_RELEASE |
| release-tick per-kg bar | 1e-10 N*s/kg | G04/G06 WIN_RELEASE_SCALE |
| handover jt == share*g*DT | 1e-9 N*s | G06 WIN_JT |
| per-tick flight closed form | 1e-12 m | G06 WIN_FLIGHT |
| impulse-work identity (energy) | 1e-12 J | G07 WIN_ENERGY |
| friction loss split | 1e-12 J | G07 WIN_LOSS |
| stored-energy account | 1e-9 J | G07 WIN_DRIFT |
| impulse replay closure | 1e-12 m/s | G07 WIN_REPLAY_V |
| pose continuity (anti-teleport) | 1e-9 m | G07 WIN_CONT |
| seam timing t_seconds | 1e-12 s | G05/G06 timing window |

The derived budget statement: the receipt names the TIGHTEST-margin operation
(measured) and reports every margin; no window is widened. These are the
budgets per operation "where applicable" (C09 contract); the assembled line
certifies the CPU backend against them.

## 8. Falsifier arms (F-class; every arm clean control FIRST, named premature
guard `g08_fb<n>_premature`, receipt row with the clean-control block; a
non-biting arm fails the build). Tamper machinery stays in the PINNED upstream
injection points (`ts.run_case` injections; the G07 account hooks); the
assembly executable is what the discriminators run against:

- FB1 teleport_transfer: clean = the assembled T continuity passes; tamper =
  `teleport_at_tick` at the handover tick on `band_mid|n=3`; discriminator =
  the continuity check bites (the teleportation class).
- FB2 support_overclaim: clean = the assembled verdict matches measured modes
  on `band_mid|n=3` (supported) and `scene|n=3` (honestly not); tamper = the
  stick verdict substituted on the `scene|n=3` transfer ticks; discriminator =
  the assertion fails on the tampered ledger (an unsupported transfer recorded
  as supported).
- FB3 flight_hidden_anchor: clean = A-full-tick ledger residuals <= 1e-12
  everywhere; tamper = the unrecorded 0.02 N*s per-tick flyer impulse during
  the flight window; discriminator = `ledger_imbalance:full_tick` fires (the
  concealment class).
- FB4 release_sticky: clean = P3 bars pass; tamper = the last hold friction
  impulse re-applied after press-off; discriminator = the release law fires.
- FB5 force_pose_inconsistency: clean = P8 conversion holds with the recorded
  pose; tamper = the conversion doubled with the pose unchanged;
  discriminator = the conversion check fires.

## 9. Input pins (verified at run time; drift refuses the run)

Repo pins resolve from the package base `5f82a3dd...` via read-only
`git cat-file` (the runner provisions CHIMERA_SOURCE_REPO/CHIMERA_BASE_SHA):

| pin | repo path at base | sha256 |
|---|---|---|
| local_contact_py | contributions/MAT2-M06/local_contact.py | 1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc |
| m06_test_suite | contributions/MAT2-M06/test_local_contact.py | b832d0dc07c1762a190d4b662ceed2b1b6dd469cbd22343cb39934e90eb08e77 |
| contact_law_json | contributions/MAT2-M06/contact_law.json | 583962c29f18118a478dedb167f2c3667414b86f5cab4ee54763416f1df7e41b |
| m06_experiment_receipt | contributions/MAT2-M06/experiment_receipt.json | 2956dd7aaf3682fc18de9b724ddd8a695011ec74c9a12a5a56744b3d738a9397 |
| trunk_mesh_json | contributions/MAT2-F03/assets/trunk_01_mesh.json | 3b17441764714c5e5e9c7a43c3253b3271a0f508954095e1960a57820cef6ee7 |
| f03_material_state | contributions/MAT2-F03/assets/trunk_01_material_state.json | 91c17a5c59ce79af3dc0e8a6dadb00c92a039075775a0a1de618da12dfca61bd |
| g04_grip_module | contributions/MAT2-G04/grip_contact.py | 0d6375484c350039468b31a2f7db2895d3365412aee52ce98de72b4173d69245 |
| g04_test_suite | contributions/MAT2-G04/test_g04_checks.py | a01b167e4393e2e513ba343f2bc6ba3fdf4d01ee08170f7fe8c3cb1c5c9a0ae1 |
| g05_obs_module | contributions/MAT2-G05/contact_support_obs.py | 3dae0a3805cec86bba8dbae9a6fc563f43cddc98fcd01a693f725e4f31c46bd3 |
| g05_test_suite | contributions/MAT2-G05/test_g05_checks.py | 83ba17604f66fdbe623b71ce481b539862ec39ebf81ee4c8bea2e5af29f9985b |
| g06_transfer_module | contributions/MAT2-G06/transfer_sequence.py | a3f376f9feafc07897ea331219320b6393bfb69916781a6beb80792c7bd068f9 |
| g06_test_suite | contributions/MAT2-G06/test_g06_checks.py | aa03fd9c77663eba41f3fe9f2641245e28318c259a83b6eddcf5d861772f4aed |
| g06_experiment_receipt | contributions/MAT2-G06/experiment_receipt.json | cf5c9cc5b7d51a23f282313974f853edca83ca30c19edd51a36eb9ddf0d3feff |
| g06_experiment_trace | contributions/MAT2-G06/experiment_trace.json | eec274ded637a4cb10049bc7d427037e3a1e54e72a3c11b55ddf80ec5d18f2f9 |
| g06_falsifier_receipt | contributions/MAT2-G06/falsifier_receipt.json | 97b95e09481e7f02dfd873470b49cb114e2c856aa4fc0cf04bb2d6caeed004bf |
| g07_release_module | contributions/MAT2-G07/release_fall_account.py | 78b5cc66f7019fa181765eb0366fe6c98525941840f57723d0ae99cb55b2a8c5 |
| g07_test_suite | contributions/MAT2-G07/test_g07_checks.py | 89ce29d6f9b606f6c81df802818715c52a4b0779e816300671a8b5a8b5728522 |
| g07_experiment_receipt | contributions/MAT2-G07/experiment_receipt.json | c539617b098190918187d9a7dcbb0a5e33a85998adaa58f6b781703bbdeb88f8 |
| g07_experiment_trace | contributions/MAT2-G07/experiment_trace.json | b8a9e139d85bd7cc116ea3d6ca94f655e41ec7ae67c15f7686e057ca0706eb9b |
| g07_falsifier_receipt | contributions/MAT2-G07/falsifier_receipt.json | 3f23c828de4845d175c5c92ef8d921768596997d80f0b970ec1f147ab77fe1cc |
| g01_feasibility_module | contributions/MAT2-G01/run_feasibility.py | 2926527383cfe8ea425bb9251844e28c9a0e0479566f472fb5d2b77ae68b98d3 |
| g01_test_suite | contributions/MAT2-G01/test_g01_checks.py | 4ae01f5f5d07f6bf898f8f04988636797a944a39fb00d21f85974f0a78b229b9 |
| g01_feasibility_receipt | contributions/MAT2-G01/feasibility_receipt.json | 4061d8ec604ddea5dfbdf605f0244874129a69a88d771d4f593c7a927c16be42 |
| f05_implementation | contributions/MAT2-F05/implementation.py | d07acb20f4e0a4e813afc8783fff4098eae531f0c808ac6e6e67242a3342d529 |
| f05_report | contributions/MAT2-F05/report.md | 0a640c131f067241d3d20f595bd825e2e4319102cc2d200ac04805f702c6ba6d |

Host pins (verified at run time, hashes frozen here):

| pin | host path | sha256 |
|---|---|---|
| g01_receipt_store | E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-G01/numerical/feasibility_receipt.json | 4061d8ec604ddea5dfbdf605f0244874129a69a88d771d4f593c7a927c16be42 |
| grasp_benchmark_md | E:/ChimeraWork/research-data/20260929/benchmark-grasp/GRASP_BENCHMARK.md | d936cebe38b1416dfc417db727ea81396eb8eb9217efed3f05b344db17f71610 |
| friction_sources_md | E:/ChimeraWork/monkey-coordination/g04-friction/FRICTION_SOURCES.md | 336118e929bd0b4fb067db5a448dc2e348fed073007787635549a4cf1cf5868b |
| g04_report_store | E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-G04/report/REPORT.md | dfca5b5556efe018ca09be4577bf6fbb5df38bb5c9ebc33d15bd18646ba349c8 |
| g05_report_store | E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-G05/report/REPORT.md | 1e5fcc7f81b5bd7b0ae3b460c72d5ed190510f66db4793c6b2e99756da8c8524 |
| g06_report_store | E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-G06/report/REPORT.md | 2e4343191591322dca4667e428c09d1dc8dcae39c8a90a53cb5298d90ab2f206 |

The visual-gate modules are pinned as G06 pinned them:
`tools/monkey_campaign/visual_capture.py`
(5ee55d5ab52beb05ffc33e9b66858f94b706cb22c290786db4a79ab344a4ff05) and
`tools/monkey_campaign/visual_gate.py`
(13cf07f47fc73f0c7fa9b5208752f6afadbdcfc66cf30b83457d756d2bc6c8c3) from the
base tree; `tools/monkey_campaign/integrity.py`
(c3ff77401c1abb5ca657afeee59fb95bac739ebef2cfd688f174b4f97caf82b2) is a
WORKTREE pin (declared provenance: shared repository working tree, 2026-10-01,
the G05/G06 heritage convention).

WHOLESALE regression-closure extraction (byte-exact at base, the g06_deps
form): contributions/MAT2-M01, MAT2-M02, MAT2-M04, MAT2-M06, MAT2-G04,
MAT2-G05, MAT2-G06, MAT2-G07, MAT2-G01. (MAT2-F05 is data-bound, not
wholesale: its harness materializes host stores outside package scope.)

## 10. CPU/GPU and runtime identity inventory (C09/C05/C06; honest scoping)

| gate/component | backend | status on this card |
|---|---|---|
| deterministic re-execution identity (byte-identical assembled line vs certified line) | CPU | CERTIFIED HERE (A1) |
| full-tick impulse ledger + reciprocity + visible anchor | CPU | CERTIFIED HERE (inherited, re-run assembled) |
| energy/work account + friction split + replay | CPU | CERTIFIED HERE (assembled R segment) |
| event localization (handover/reattach/release/CCD) | CPU | CERTIFIED HERE (A6) |
| reference-math composition (record-g vs standard-g; jn/DT conversion) | CPU | CERTIFIED HERE (A7) |
| mutation controls (FB1-FB5) | CPU | CERTIFIED HERE (section 8) |
| upstream suite regression (M06, G04, G05, G06, G07, G01) | CPU | CERTIFIED HERE (section 11) |
| GPU device-leg parity for the climb contact path | GPU | UNRESOLVED -- no certified owner on the sealed line (M08-M12 certify material/actuator/limb/LOD worlds, not the trunk/pad fixture); CPU-only package per runner law; the GPU queue owns this future work. INVENTORIED, never claimed. |
| engine device-leg anchors (W03 freefall/stand/C1/C2) | GPU | OUT OF SCOPE -- their own lane; CPU evidence is structurally not device proof (W03 law). |
| joint kinematics (C05) | -- | ABSENT -- no joints exist in this fixture; inventoried, never faked. |
| creature articulated chain (C06 M(q)qddot) | -- | ABSENT -- fixture pads + trunk only; the solver ledger carries the fixture-level force accounting. |

## 11. Regression

The declared upstream suites re-run UNMODIFIED on this exact candidate
revision: M06 `test_local_contact.py`, sealed G04 `test_g04_checks.py`, sealed
G05 `test_g05_checks.py`, sealed G06 `test_g06_checks.py`, sealed G07
`test_g07_checks.py`, G01 `test_g01_checks.py`. Exit 0 required for each;
receipt recorded. F05's suite is NOT in the required set: F05 enters as
hash-bound DATA (section 9); its harness materializes host stores outside the
package scope; the non-execution and its reason are RECORDED in the regression
receipt (honest accounting, not a silent skip).

## 12. Capture plan (grasp/motion profile; registry row read mode=ro)

The capture replays the ASSEMBLED composition story on the closing case
`band_mid|n=3`: frames at declared snapshot ticks spanning BOTH segments'
story beats (T-segment: attach 4, load 8, hold 20, handover 31, climb 60,
mid-flight 120, brake 186, attach2 193, hold2 208; R-segment beat: release 21
of a G07 run rendered as the composed release story), 1 video second per
frame; the tick axis is REAL (state_or_tick_interval declares the actual
snapshot tick; tick_map declares tick->video-second mapping; the replay
re-runs the experiments then the render). Views (task-owned realization,
creature absence inventoried never faked): 'whole-body/trunk relationship' ->
trunk + all pads + support-state labels; 'wrist/digit attachment close-up' ->
the relocating channel's attachment patch (the wrist/digit anatomy absence is
the inventoried debt); 'orthogonal view of each loaded interface' ->
orthogonal cameras on the loaded holder interfaces and the target facade.
Diagnostic layers: attachment patches and endpoint ids, contact normals and
forces, support state, declared pad/trunk frame axes; 'tendon paths' ABSENT
(inventoried; no tendons exist); 'joint/frame axes' realized as declared
pad/trunk frame axes (no joints exist). Clean view REQUIRED: clean pairs share
the exact camera and the exact physical state; identical state hash across
every view row. Full 17-field camera record on every row. Codec: FFV1
`-level 3 -g 1 -fflags +bitexact` mkv; lossy never evidence; ffmpeg version
recorded. Pixel presence measured per frame and re-measured from the DECODED
video; task_id SHORT form (G08) in manifest AND context. visual_acceptance
stays FALSE BY DESIGN: independent visual review remains the
Sergeant/Lieutenant gate (this text-only worker inspects no pictures).

## 13. Refusal registry (the card-owned codes; any dev-run code not listed
here or in DEV_RUN_REFUSALS.md is a record defect)

dep_pin_missing; dep_pin_drift; interface_pin_missing; interface_pin_drift;
input_pin_missing; input_pin_drift; matter_identity_drift;
unsupported_state_unexplained; assembly_continuity_violation;
event_localization_mismatch; identity_binding_mismatch;
budget_window_absent; seam_delivery_shortfall; seam_refused_declared_sample;
vacuous_comparison_refused; suite_failure; prereg_identity_mismatch;
census_mismatch. Inherited sealed codes fire unmodified from the pinned
modules (ledger_imbalance:full_tick, reaction_concealed,
target_facet_drift:*, motion_recursion_broken, timing_unbound,
undeclared_field, timing_drift, named_absent_occupied, privileged_source,
nonfinite_value, dim_mismatch) and are cited via their sealed owners.

## 14. Amendments

(none yet -- amendments after this freeze, both before the experiment runs;
each amendment recorded here with its scope.)
