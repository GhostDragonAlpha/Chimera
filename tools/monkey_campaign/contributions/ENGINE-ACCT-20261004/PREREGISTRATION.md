# PREREGISTRATION DRAFT — ENGINE-ACCT-V1: the docketed engine-debt accounting rung on the sealed W03 walk line — the smooth mass-metric drift channel, the RK4 stage-state deltas, the impact-solve decomposition; the P3-SIGNED attribution re-evaluation and the 30.970713623726674 J ledger-localization re-attempt

Status: **DRAFT (chain stop 1).** Authored by wk-engine-accounting
(dispatch `LIEUTENANT_RESUME_v2.json` event 2026-10-09T17:30:00Z; agent_3223d748;
roster "the corrected-scoping engine debt ... prereg chain stop 1").
Lane-host clock at authoring: 2026-10-04 03:3x CDT (the recorded host-clock
anomaly class, same as the W03I lane; the authoring context date 2026-10-02
differs — both stated, no date is evidence). Phase 1 = design + prereg DRAFT
only: ZERO runner jobs, ZERO seals, ZERO Git mutations, ZERO builds by this
lane. This draft awaits the Lieutenant's pin; FINALIZE-AT-FREEZE slots are
named below and stay UNSET until filled once at freeze, before any gated
run. Any required prereg commit goes through the publication owner BEFORE
any gated experiment (a seal is not a substitute). Nothing here is a run
claim.

## 0. Inheritance of record and the corrected scoping this lane executes

THE VERDICT THIS LANE EXTENDS (the docketing event): **W03-SIGNED**, PR #346,
MERGED at `81cdd6e4` = the astra tip (23rd PR); the sgt FINAL APPROVE (the
delta settled in the workers' favor by full-population enumeration over all
622 receipts; the F2 mechanism correction source-verified at the exact
lines); the prereg pin commit `3c66ad5b5825c51c75e9ffbb185169fbac2f6042` on
`origin/review/W03-SIGNED-20261004` (parent = the astra tip
`28a110f2eb3ec6495318bb70738d4408859e4ac3`), pinned blob content sha256
`64298da87f019016ef8aad9ae4ca0bbbc850ec43389a680eefe30a382a260d5d` (this
lane re-hashed the sealed of-record copy: MATCH); seal of record manifest
sha256 `1cc8112ba6b8d54f5061333e71da9309b34054f30898879f956bcd971e09b7d3`
(sealed dir `a62394879`, canonical key = the receipt's
`sealed_manifest_sha256`); battery job `f2dfde7d` (slot 3), receipt sha256
`0a9c325776ecd1557553e409ee962a39519cba97ec29b6b9a8983d3e6c1d2c02`,
runner receipt sha256
`28848f2496c785cb07b87228e024aaa1fd159b87ea3211120949550cd6076e1f`, exit 0,
cleanup_verified true, verdict **FALSIFIED** (G_TEETH false via P10-t1,
structurally unsatisfiable while P3-RESIDUAL stands: pass_clean =
pass_flip = 0). The 8-job census: 5 FAILED preserved + 3 PASSED.

THE SEALED NUMBERS THIS LANE RE-EVALUATES (all from receipt `0a9c3257...`,
key names quoted; re-read this lane):

- **P3-SIGNED, outcome RESIDUAL**: 240/240 window transitions violate the
  frozen `window_Ns = 1e-09` (per-tick absolute; "corrected-identity
  convention; not widened (Lt slot answer)"); `worst_resid_Ns =
  0.48973347721985194` at `worst_coord = 4` (base_trans_y);
  `worst_resid3_Ns = 0.19512176238675244` (east);
  `worst_resid_world_Ns = 1.1667760259401594`;
  `median_resid3_Ns = 0.04692466030871379`; AND the instrument's own
  internal identity is EXACT: `cg3_vs_fxsum_max_dev_Ns =
  5.551115123125783e-17` — the recording closes; the applied impulse
  accounting does not. `v1_containment_failures_same_rows = 112`.
- **P4 ledger**: m1 `bal_at_300 = 30.970713623726674` == the sealed raw,
  `exact_within_1e-9 = true`; m2 `not_localized = true`, `localized_to =
  []`; the frozen convention `max_t |B(t)-B(60) - (C(t)-C(60))| <= 1e-6 J`
  over [60,300]; the nine declared candidates' worst deviations (J):
  actuator_work 49.74405097489279, cw_contact 31.07475018469639, cw_stop
  31.07453444877076, external_work 31.074534540056852, poscorr_du_booked
  31.107107822428727, impact_heat_total 29.800854344825556, brake_heat
  21.53910185300819, friction_heat 21.159024072130272, damping_heat
  13.312730402435673.
- **P10**: `pass_count_clean = 0`, `pass_count_flip = 0`, `floor_Ns =
  1e-09`, `median_resid3_clean_Ns = 0.05500843558173279`,
  `median_resid3_flip_Ns = 0.08381533021798007`, `t2_median_rises = true`,
  `t1_degrades = false`, `vacuous_evaluator = true` (AS FROZEN — the t1
  form presupposed clean passes, which are ZERO while P3-RESIDUAL stands;
  per the A.7 F1 convention note the 0.0550 clean median is the WORLD-form,
  the P3 east median is 0.04692). The mutant arm's anchor set was EXACT.
  G_TEETH = false BY THE FROZEN TEXT; no t1 reformulation happened locally.

THE CORRECTED, SOURCE-VERIFIED SCOPING (the ONLY scoping this lane
executes — `E:/ChimeraWork/monkey-coordination/w03-instrumentation/
EVIDENCE.md` Appendix A.7 F2, adopted at the sgt FINAL APPROVE of #346):

- **RETRACTED, NEVER RESTORED, NEVER USED HERE**: the claim that "the
  recorded per-row projection multipliers do not reconstruct the applied
  projection impulse". `project_rows` builds the returned impulse
  `p[i] += max(0,lambda[k])*rows[act[k]][i]` (line 704) and on success
  outputs the SAME clamped lambdas as `multipliers` (line 712); per-call
  reconstruction is EXACT BY CONSTRUCTION, and both call sites apply
  exactly `p` (rate() line 1756-1757 `correction=multiply(inv,p)`;
  impact() line 1814-1816 `s.impulse[i]+=p[i]`). Any sentence in that
  class in any artifact from this lane is a defect.
- **THE SCOPING**: the unrecorded terms are
  (i) **THE SMOOTH MASS-METRIC DRIFT** — the (dM/dq)qdot*v term, the
  along-the-tick variation of p = M(q)v from the coordinate path, of which
  only the DISCRETE positional-correction jump's dM term is recorded
  (W03I channel `pcorr_dp`); and
  (ii) **THE RK4 STAGE-STATE MISMATCH** — the stage internals declared
  unrecorded in the W03I schema S7 ("DECLARED ABSENT: the RK4 stage
  internals inside `free_step` remain unrecorded"). The W03I-recorded
  stage impulses are computed at the four per-substep stage states while
  the identity is evaluated on tick-boundary states.
- The P3-RESIDUAL and P4-NOT_LOCALIZED are ENGINE DEBT by the sealed
  record; the docketed rung is the engine-side impulse accounting
  extension; THIS lane is that rung's prereg (chain stop 1).

Engine-source facts re-read and line-cited THIS LANE (read-only; pinned
`gait_controller.hpp` content sha256
`f0ffea12795bd47f7c48f5ed9b8aa98869725467d94a1081b1d942f6fba129bd`,
re-hashed MATCH; its companion `coupled_articulation.hpp`, content sha256
`5bd73c2d43b85b229040da1ac779ef3733dc7d4dbe04cbeb1447c03767dc9fb5`,
hash-recorded this lane):

- `gait_controller.hpp` L616 `evaluate(const State& s)` ->
  `model_->evaluate(s.q,s.v,gravity_)`; L615 `State s_` sits in the
  private section (public: at L1957) — the dump process still cannot reach
  any of this through the public interface; the engine-recording patch
  pattern (W03I, hooks H1-H15) remains REQUIRED.
- **THE M(q) CONSTRUCTION CODE PATH (named, this lane's channel source)**:
  `chimera::multibody::Model::evaluate(q,v,gravity)`,
  `coupled_articulation.hpp` L82-91. Per body, per axis (L86): the axis
  transform `one.t`, the PER-COORDINATE PARTIAL transform
  `one.d[a.slot]=dr*a.slope`, and the TIME-DERIVATIVE transform
  `one.dt=dr*rate` (+ `one.ddt=skew(a.axis)*dr*(rate*rate)`), propagated
  through the frame composition `product()` (L45: `c.dt=a.dt*b.t+a.t*b.dt;
  c.ddt=...; c.d[i]=a.d[i]*b.t+a.t*b.d[i]`). The per-coordinate Jacobian
  columns `jv/jw` come from `f.d` (L88); the mass matrix accumulates
  (L89): `e.mass[n*i+j]+=b.mass*dot(jv[i],jv[j])+dot(jw[i],vector(iw,
  jw[j]))`; the bias accumulates from the ddt body accelerations (L89):
  `e.bias[i]+=b.mass*dot(jv[i],acc)+dot(jw[i],moment)`. THE ENGINE'S OWN
  MACHINERY ALREADY COMPUTES the path time-derivative transforms (dt,
  ddt) and the per-coordinate partials (d) at EVERY evaluate() call; the
  smooth drift dM/dt along the coordinate path is constructible from this
  same machinery as a recording-only shadow accumulation.
- `rate()` L1712-1760: `evaluate(s)` + `inverse_spd(e.mass)` (L1713); rhs
  = `gravity-bias+external` (+`tau-damping*v` on drive coords) (L1716-
  1719); the per-contact `friction_solve` impulses applied INSIDE rate()
  (L1744-1747); the `project_rows` impulse applied (L1755-1758). The
  returned Rate carries `q=s.v, v=free` (the PROJECTED stage acceleration).
- `free_step()` L1761-1783: the four RK4 stage states
  `start`, `shifted(a,h/2)`, `shifted(b,h/2)`, `shifted(c,h)` (L1762,
  L1766); the state update RK4-weighted (L1768); the generalized reaction
  impulse `di=h*(a.reaction+2*b+2*c+d)/6` (L1769-1770); the E8 discrete
  constraint power `di*(start.v+end.v)/2` (L1771); per-point
  `contact_generalized` RK4 accumulation of the per-stage `point_force[k]`
  rows (L1774); the friction FORCE impulse accumulated SCALAR-ONLY
  (`friction_force_impulse[k]+=h*(lambda stages)/6`, L1778) — the
  per-stage direction products are what W03I H7/H9 record and what S11
  now binds to stage states; damping RK4 (L1779).
- `impact()` L1784-1872: the friction-catch branch (L1792-1811,
  `friction_solve` at the impact state, `s.v[i]+=change[i]`,
  `s.impulse[i]+=force[i]` L1803, per-branch heat shares L1805-1809); the
  projection branch (L1812-1824, `project_rows` on `s.v`, `s.impulse[i]+=
  p[i]` L1816, per-row multiplier shares L1819-1822); the POSITIONAL
  CORRECTION (L1837-1871): `s.q[i]+=corr[i]` (L1855), `du=evaluate(s).
  potential-u_before` (L1856), booked `s.impact-=du` (L1857) — the mass-
  metric least-norm CONFIGURATION jump; W03I H12 records its momentum term
  `pcorr_dp` = e3^T(M_after - M_before)v — the ONLY mass-variation term
  recorded today, and it is DISCRETE.
- L1961 `require(recipe_.at("substeps")==4,"gait_substeps")`; the tick
  loop L2646-2697 (4 substeps; the 40-step store bisection scaling tau;
  `impulse_torque[c]+=tau[c]/4` L2691); `status()` L2700-2914 (the
  serialized v1 channels incl. per-point `impact_impulse_N_s`/
  `normal_impulse_N_s` L2740).
- The engine's OWN FP-honesty anchors for window derivation:
  `inverse_spd` requires mass symmetry at 1e-12 relative
  (`coupled_articulation.hpp` L39) — the same class the drift-channel
  consistency window candidates below.

## 1. The question, the qualifications, and the not-claims

THE QUESTION (either answer is a result): with the smooth mass-metric
drift channel, the per-stage state/impulse deltas, and the impact-solve
decomposition recorded additively on the SAME sealed physics bytes, does
per-tick generalized-momentum attribution CLOSE (does the sealed
240/240-tick P3-RESIDUAL, worst 0.48973347721985194 N*s at coordinate 4,
shrink to the FP floor on the extended named channel set)? And does the
`30.970713623726674` J imbalance NOW localize into the named channels? A
closure upgrades the walk physics toward its final accounting; a residual
NAMES the next term. Neither answer repairs anything in place.

QUALIFIES (at the HEADLESS CLASS only): the sealed W03-class articulated
walk scene's per-tick momentum change attributed to a NAMED, SIGNED,
EXTENDED channel set; the energy-ledger imbalance localized per tick/
substep/stage/channel; the extended evaluators proven non-vacuous by
CONSTRUCTED mutants (a sign-flip case; a term-drop case).

NEVER CLAIMS (the not-claims, at maximum; the W03I class carried whole):
instrumentation physics — NOT player control, NOT the product runtime, NOT
a launchable build (PLAYABLE_BUILD.json nulls stand), NOT real-time play
(TC-11), NOT a trained policy, NOT anatomical-hand or grasp/climb transfer
(fore-LIMB pads, never "hands"), NOT uneven-ground traversal (F06
negatives stand), NOT the bench measurements. No change to any sealed
W10/W03/WALK-PH/W03-SIGNED row: PR #346's FALSIFIED verdict and the
PR #328 FALSIFIED_OR_PARTIAL record stand until the chain supersedes them
with new sealed evidence — never "repaired" in place. The withdrawn
universal "nothing-hidden-moves-the-body" is NOT restored under any
outcome; a P3-ACCT closure supports only the narrow claim that the NAMED
extended channel set accounts the per-tick momentum change on the clean
arm at the headless class. No engine-ledger FIX is delivered here: a
repair is a NEW prereg through the publication owner. And the retracted
multipliers claim (section 0) is never restated in any form.

## 2. Design of record and the declared instrument extension

Design: the SAME sealed physics bytes on every clean arm — scene
`chimera.earth_scene.v1` sha256
`f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342` (this
lane re-hashed the pinned copy: MATCH), 14 bodies / 18 coordinates / 12
capped drives / 8 contact points / 10.037998000000004 kg — with an
EXTENDED declared instrument arm (`ENGINE-ACCT`), the W03I instrument
lineage (hooks H1-H15 of `INSTRUMENT_SIGNED_PATCH.py`, sha256
`e4a8d3b51a94c0057b33b8ce4ef5f06df127a4e219b8f326f367c5402788980e`,
re-hashed MATCH; derived header sha256
`2c72df55c1f615c5abc8b7948ba7de8f62d765d482fc25f5a6fbc9ecc54f9054`; dump
sha256 `9e32d94ed78f848fc063a519b050d84689e84c00af05b85c54c85f6bd037cea8`)
plus a NEW declared engine-recording patch layer
(`INSTRUMENT_ACCOUNTING_PATCH.py`, phase-2 artifact). Source lineage:
extracted read-only from the shared object database at revision
`17ba94b948ca217c1bbf8f7dee5b51b995b387bb` (blobs per the W03I prereg of
record, section 1); NO worktree, NO clone, NO Git mutation — NO_WORKTREES.md
(sha256 `7d3fe1029f727b95ff2c832b06a89b3bac40f59e14993440255636218645f433`,
re-computed and MATCH this lane) obeyed.

The patch law (carried, whole): every added line anchored, enumerated in
the shipped manifest with its read-only justification, ADDITIVE-ONLY,
PURE-RECORDING (reads existing values into new recording accumulators; NO
assignment to any physics-reachable state; NO reordering of any original
expression; NO solver constant introduced, read, or moved), gated behind
the SAME `GAITPHYS_SIGNED=1` master gate so unset envs keep the original
code path (the P1 anchor law, extended to the new layer). Telemetry FILES
only; no new stdout/stderr byte in any mode (the stderr anchor stays
byte-exact incl. the GAIT_EVENT_TRACE [poscorr] lines class); the emission
path never allocates conditionally on physics values (determinism).

### The declared v3 telemetry schema (the S-series extension of the sealed W03I v2)

The sealed v2 channels S1-S9 stand UNCHANGED in name and law; this prereg
LIFTS the S7 declared absence by ADDING:

S10 THE SMOOTH MASS-METRIC DRIFT CHANNEL: per tick, per coordinate i,
`drift_imp[i] = sum_substeps h*(sum_stages w_s*(dMdt_v)_i(stage state))/6`
[units N*s = kg*m/s; the same RK4 weighting law as every recorded impulse
channel], where `(dMdt_v)(q,v) = (dM/dq . qdot) v` is formed from THE
ENGINE'S OWN M(q) CONSTRUCTION MACHINERY — the named code path:
`chimera::multibody::Model::evaluate` (`coupled_articulation.hpp` L82-91),
specifically the per-axis per-coordinate partial transforms `one.d` and
time-derivative transforms `one.dt` (L86) propagated by `product()` (L45),
over the per-body Jacobian columns `jv/jw` (L88) and the mass accumulation
(L89). Declared construction (the exact formula set ships line-by-line in
the phase-2 patch manifest, in one of two declared forms, chosen BEFORE
any gated run and never swapped after):
  (C1) the mixed-partial propagation: the recording layer extends the
  `product()` propagation ONE level to carry the mixed transforms
  d(f.dt)/dq_c, giving exact djv_i/dt and djw_i/dt along the path, hence
  the exact `dM/dt[i][j]`; or
  (C2) the composite per-body derivative: `dM/dt` assembled per body from
  the engine's own f, f.d, f.dt machinery by differentiating the L89
  accumulation term-by-term along the path.
Either form is a RECORDING-ONLY SHADOW of the engine's own construction:
no physics-reachable state is touched; the shadow uses only values the
engine already computes (q, v, the frames and their d/dt/ddt transforms).
MANDATORY INTERNAL CONSISTENCY CHECK (recorded per evaluated state,
emitted; gated at the S10 window below): the construction must satisfy
`v.bias == 0.5 * v.(dMdt_v)` at every recorded state — the classical
skew-symmetry consequence tying the engine's OWN bias channel (built from
the ddt body accelerations, L89) to the drift channel (built from the
extended transforms): two INDEPENDENT formula paths over the same engine
machinery. A failure of this check is a CONSTRUCTION DEFECT — instrument
defect class, the run stops — NEVER physics, NEVER a window to tune.
(Rationale of record, falsifiable: the continuous statement
`d(Mv)/dt = (gravity - bias + F_applied) + dMdt_v` makes the drift exactly
the momentum term the recorded channels omit; the identity above is the
pointwise consistency property the construction must reproduce to be
admitted as that term's measure.)

S11 THE RK4 STAGE-STATE / IMPULSE DELTAS (the S7 declared-absent class,
now recorded): per tick, per substep, per RK4 stage k in {a,b,c,d} (the
states `start`, `shifted(a,h/2)`, `shifted(b,h/2)`, `shifted(c,h)`,
`free_step()` L1762/L1766): the stage momentum
`p_stage[k][i] = (M(q_stage) v_stage)_i` (a PURE READ — rate() already
calls evaluate() at each stage state, L1713; the hook captures
`e.mass * s.v`), the stage generalized reaction `reaction[i]` (L1721/
L1757), the stage per-point impulse rows `point_force[k][i]` and lambdas
(L1745-1747), the stage mode/slip, and the stage rhs decomposition
components (the H6 channels at stage granularity). Volume bounded: 4
substeps x 4 stages x (18 + 18 + 8x18 + counts) doubles/tick, declared;
emission is unconditionally sized under the master gate.

S12 THE IMPACT-SOLVE IMPULSE DECOMPOSITION (extends S2/S3; the W03I-named
channel): per impact event, BOTH branches recorded separately, never
merged: (a) the friction-catch branch's `friction_solve` force vector,
lambdas, mode, and heat shares (L1800-1810); (b) the projection branch's
FULL decomposition — per row r: the multiplier `lambda_r`, the row class
(contact point k / joint stop coordinate c), and the per-row generalized
contribution `lambda_r * row_r[i]` as a RECORDED VECTOR — with the
reconstruction identity `sum_r lambda_r*row_r == p` recorded and asserted
at instrument-defect class on every event (exact BY CONSTRUCTION at
source lines 704/712; the check proves the RECORDING, never physics, and
is the anti-retraction tripwire: any violation falsifies this prereg's own
recording, not the engine); (c) the stop-row multipliers from both
branches; (d) per-branch loss/heat shares beside the recorded `s.impact`
bookings.

Emission law (carried): telemetry FILES only; env-gated; with every env
unset the ENGINE-ACCT binary must produce byte-identical stdout/stderr/
qstream to the sealed anchors (P1).

## 3. Frozen predictions (acceptance = sealed receipt; evaluated with named variables)

Units law (carried): every evaluator formula in the receipt carries a
UNITS line and a dimensional-analysis check BEFORE any numeric claim.
Canonical naming law (carried): manifest hashes are receipt keys.
Early-refusal law (carried): every windowed evaluator declares its
truncation behavior AT FREEZE; a truncated window can never produce a
full-window PASS; TRUNCATED(prefix) is part of the recorded result.

- P1 ANCHOR IDENTITY (the FULL anchor floor, carried bit-exact; the
  paired-instrumentation scoping carried verbatim): the clean ENGINE-ACCT
  arm (all GAITPHYS envs unset; the extended recording layer compiled in)
  reproduces EXACTLY at recorded precision: scene sha
  `f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342`
  (input identity); stdout sha
  `8c537cdb7cb8c43cf9423cb50056787bcc31ee487d70d3c2a1e73ed5d60b06cc`;
  stderr sha
  `c6f9b6c00a1d549a4bc709724d2f62f8f28b37823696de4689e1950651c37481`
  (recorded-hash comparison; no stderr bytes preserved anywhere); q-dump
  run1 sha
  `b47b709c43a021d24bfee13bb2fe4592167cf205ee0abf9971de462319389c93`;
  run2 == run1 bit-identical; ticks
  302 (0..301) ending in the sealed refusal; base dx `0.9131056683968011`,
  dy `-0.7178374101385098`; worst ledger balance raw `30.970713623726674` J
  at tick 300 (store `30.970713623726652`). FAILURE = the recording layer
  perturbs physics — the lane records the failure and stops (no tuning to
  recover). THE SCOPING (carried, mandated): P1 is TRACE-REPRODUCTION
  EVIDENCE AT RECORDED PRECISION, NOT a proof of zero perturbation; no
  paired instrumented/uninstrumented test is run; the assurance class is
  exactly (i) the pure-read recording law, line-enumerated in the sealed
  manifest, (ii) the P1 identity, (iii) two-pass determinism (P8). No
  stronger non-perturbation language may appear in any receipt or report
  from this lane.

- P2 SCHEMA COMPLETENESS v3: every tick of the clean arm emits the
  complete S1-S12 schema, finite, declared units; structurally-zero
  channels named in the census; AND the internal identity checks — the
  v2 set (per-point rows sum to `contact_generalized`; the receipt's
  sealed class `5.551115123125783e-17`), the S12 reconstruction identity
  `sum_r lambda_r*row_r == p` per impact event, and the S10 consistency
  check `v.bias == 0.5*v.(dMdt_v)` per recorded state — all inside the
  S10/S12 windows. A missing, non-finite, or window-violating internal
  check = INSTRUMENT DEFECT: FAILED INSTRUMENTATION, stop; never
  tolerated, never imputed, never window-widened.

- P3-ACCT PER-TICK ATTRIBUTION (THE RE-EVALUATION TARGET; the honest
  either-way): window [60, 300] (carried; the clean arm provides ticks
  0..301). For every tick t and coordinate i, the extended EXACT discrete
  identity on the recorded channels:
  `p_i(t+1) - p_i(t) - (contact_gen[i] + contact_impact_gen[i] +
  stop_imp[i] + actuator_imp[i] + damping_imp[i] + grav_bias_ext_imp[i] +
  drift_imp[i]) = residual_i(t)` [all terms N*s = kg*m/s; units line
  emitted]. The world-space companion carried (its frozen form is the
  P10 sign-sensitive one). WINDOW: CARRIED FROZEN, NOT WIDENED — `1e-9`
  N*s absolute per coordinate per tick (the corrected-identity
  convention; the sealed `window_note` is the authority).
  THE STAGE-LEVEL COMPANION (EMITTED, and gated at the S11 window): per
  substep, the four stage transitions' `p_stage` deltas against the
  stage-local recorded impulse sums + stage drift — the test that
  separates a bookkeeping-granularity explanation from a deeper
  unrecorded channel.
  OUTCOME A (CLOSURE): all window ticks inside the window — per-tick
  attribution CLOSES on the extended named channel set; the sealed
  P3-RESIDUAL is answered: the residual WAS the smooth mass-metric drift
  (+ the stage-mismatch class, per the S11 companion); the walk physics
  attribution upgrades toward its final accounting — the narrow
  named-set claim only, never the universal.
  OUTCOME B (RESIDUAL): any violating tick is localized by tick,
  coordinate, and residual channel-class; the residual IS the result — a
  further unrecorded or non-additive term exists and is NAMED as the next
  candidate class. A residual persisting at the sealed magnitude WITH the
  drift recorded FALSIFIES the drift hypothesis as the sole explanation —
  recorded as such, never softened.
  EMITTED, NOT GATED: the per-tick residual attribution table (the drift
  share and the stage-mismatch share of each tick's sealed-class
  residual), so the magnitude question is answered by the receipt whatever
  the gate says. No tuning; no window sweep; the gate never moves.

- P4-ACCT LEDGER RE-ATTEMPT (the second re-evaluation target; both-ways
  frozen): m1 IDENTITY-WITH-ANCHOR CARRIED: the cumulative balance at
  tick 300 equals the sealed raw `30.970713623726674` J at recorded
  serialization precision; a mismatch = INSTRUMENT DEFECT (stop), never a
  physics finding. m2 LOCALIZATION (either answer a result): per tick and
  per advance() call, the recorded split
  `|d(KE) + d(PE_grav) - (W_actuator + W_external + W_damping +
  heat_impact(incl. poscorr du) + heat_friction + W_brake +
  W_constraint_contact + W_constraint_stop + drift_power_terms)|` with
  the CARRIED W03I convention
  `max_t |B(t)-B(60) - (C(t)-C(60))| <= 1e-6 J` over [60,300] (NOT
  widened; the sealed ruling stands). The candidate set: the sealed nine
  (actuator, cw_contact, cw_stop, external, poscorr_du, impact_heat,
  brake, friction, damping — their sealed worst deviations quoted in
  section 0) PLUS the NEW declared candidates from the extension: the
  drift-power share `0.5*v.(dMdt_v)` split out of the gbe/bias
  aggregation (per stage, RK4-weighted), and the E8 trapezoid residual of
  the constraint power form (`di*(start.v+end.v)/2`, free_step L1771)
  against the stage-level integral. A channel that closes the ledger
  within the window is NAMED; if none does, the receipt says exactly: the
  imbalance does not localize to the declared channel set; closure is
  engine debt, now sharper. No repair in this lane.

- P5 ZERO-FRICTION CONTROL, P6 DRIVE-CUT CONTROL, P7 CAP-RAISE TAMPER,
  P8 DETERMINISM, P9 STATE-WRITE INJECTION: CARRIED UNCHANGED in their
  sealed W03I frozen forms (P5 the common-window form with the mu0
  refusal at tick 65 class recorded TRUNCATED, never normalized; P6 the
  implemented high-water form with the rise census emitted-not-gated; P7
  cap x1.5 caught by the envelope detector AND the signed actuator
  channel; P8 two full clean passes byte-identical across stdout, stderr
  hash, q-dumps, and the FULL v3 telemetry streams; P9 the declared
  `speeds()[3] += 0.05` write at declared tick 100 diverging exactly at
  the injected tick). By reference: the frozen texts are the W03I prereg
  of record sections P5-P9 (pinned blob
  `64298da8...260d5d`), never re-frozen locally. P8's stream set extends
  to the new S10-S12 files; P9 must diverge exactly at the injected tick
  WITH the new recorders on — the recording layer may not move the probe.

- P10-ACCT THE CONSTRUCTED MUTANTS (the teeth; both satisfiable under
  EITHER P3-ACCT outcome — the W03I t1 lesson, fixed structurally):
  TELEMENTRY-ONLY mutants riding `GAITPHYS_MUTANT` in the EMITTER layer;
  the mutant arms' P1 anchor sets (stdout/stderr/q-dumps) must STILL be
  byte-exact — proving the mutants touched only telemetry bytes.
  (a) SIGN-FLIP (carried, extended, declared branch BEFORE the run):
      `GAITPHYS_MUTANT=signflip_acct` — the emitter flips the sign of the
      emitted east/south tangent components (both attribution classes)
      AND of the emitted `drift_imp` channel, on an otherwise clean run.
      t1-ACCT: IF the clean arm closes (P3-ACCT outcome A): the flipped
      stream's pass-count is strictly smaller, with at least one flip-only
      failing tick whose emitted |drift_imp| or total |tangent impulse|
      exceeds `1e-9` N*s (the carried floor class). IF the clean arm is
      RESIDUAL (outcome B): the flip must produce at least one tick whose
      residual crosses a named magnitude class recorded from the clean
      stream (a flip-only |delta-residual| > 1e-9 N*s at a tick with
      nonzero emitted |drift_imp|), recorded as the t1-ACCT-B census.
      WHICH BRANCH IS DECIDED is declared by the clean arm's own outcome —
      no post-hoc choice between them.
      t2-ACCT (carried form): the flipped stream's median |residual|
      strictly exceeds the clean stream's, per form (generalized and
      world).
  (b) TERM-DROP (NEW): `GAITPHYS_MUTANT=dropdrift` — the emitter ZEROES
      the emitted `drift_imp` channel (and only it) on an otherwise clean
      run. The evaluator MUST detect the drop: the P3-ACCT identity
      re-evaluated on the drop stream degrades STRICTLY relative to clean
      (pass-count strictly smaller under outcome A; median |residual|
      strictly larger under outcome B; the same declared-branch law as
      t1-ACCT). This proves the new channel is LOAD-BEARING in the
      identity — the closure, if A, is not a hidden cancellation — and
      that the evaluator is non-vacuous in the extension.
  A failed tooth = VACUOUS evaluator or a load-bearing-free channel:
  G-TEETH false, no P3-ACCT closure claim may be entered from this lane,
  and the failure is reported unchanged.

## 4. Qualification gates and verdict classes

- G-ANCHOR: P1 (the full floor) + the P10 mutant anchor side-conditions.
- G-INSTRUMENT: P2 (completeness + the S10/S12 internal windows) +
  P4(m1).
- G-ATTRIBUTION: P3-ACCT — Outcome A = CLOSED; Outcome B = RESIDUAL with
  the localization receipt. Both recordable; neither downgraded by the
  other's class.
- G-LEDGER: P4(m2) — LOCALIZED (a named channel closes the window) or
  NOT_LOCALIZED (the honest negative, sharpened); m1 failing is never a
  ledger outcome, it is an instrument refusal.
- G-TEETH: P7 caught + P9 exact-divergence + P10-ACCT (a) and (b).
- G-DETERMINISM: P8 (extended to the v3 streams).
VERDICT CLASSES (this lane's own receipt): ATTRIBUTION_CLOSED /
LOCALIZED_PARTIAL / FALSIFIED, exactly the W03I classes with
G-ATTRIBUTION now on P3-ACCT and G-TEETH on the P10-ACCT pair. The
overall W03-class verdict remains the chain's business: this lane's
receipt FEEDS it; it does not self-advance any gate.

## 5. Anti-tuning law (standing, carried + extended)

No drive cap, friction value, gait table, zero map, mass, inertia, entry
speed, servo gain/frequency, tick rate, substep count, contact point, or
plane height may differ between the sealed scene and any CLEAN arm. The
only declared deltas: the control arms (P5 mu=0, P6 power-cut at 150, P7
cap x1.5), the P9 injected tick, and the P10-ACCT telemetry-only mutants
— each declared BEFORE any run. THE SOLVER CONSTANTS: the recording layer
introduces NO solver constant and moves NONE — the engine's own gates and
laws (`kSlip`, the touch gate `1e-6+1e-3*joint_speed_scale`, the E8 form,
the row budget, `substeps==4` at L1961, the poscorr 0.05 budget at L1854,
the impact `loss>=-1e-11` requires, mu 0.6/0.4 placeholders NB-01/02) are
UNTOUCHED and UNREAD by the recorders except as pure reads of values the
engine already computed. Instrument schema, windows, tolerances, and
mutant semantics are declared in this prereg BEFORE any run and never
swept; a FINALIZE-AT-FREEZE constant is set once at freeze with its
derivation, never after seeing data. Any gate that would pass only under
a clean-arm parameter change (including a tolerance relaxation or a
drift-construction swap after data) is a tune_to_success refusal: the
lane records it and stops. An anchor failure traced to the recording
layer is recorded as FALSIFIED, never patched around.

## 6. FINALIZE-AT-FREEZE slots (named here; UNSET by law until the freeze)

Filled ONCE, with derivations, before any gated run, by the Lieutenant's
ruling recorded in the chain:
1. The S10 internal-consistency window for `v.bias == 0.5*v.(dMdt_v)`
   (candidate class: the engine's own 1e-12-relative mass-symmetry
   require, `coupled_articulation.hpp` L39, with an absolute FP floor).
2. The S12 reconstruction-identity assertion tolerance (candidate: the
   sealed `5.551115123125783e-17` N*s class observed for the v2 identity,
   with an absolute floor).
3. The S11 stage-level companion window (candidate: the carried 1e-9 N*s
   absolute per stage transition, justified against the recorded FP
   scale at stage granularity).
4. The drift-construction form (C1 vs C2) — chosen once, in the phase-2
   patch manifest, before any gated run.
5. The contribution-directory name (proposal: `ENGINE-ACCT-20261004`,
   distinct from `W03-SIGNED-20261004`; the Lieutenant may rename at pin).
CARRIED FROZEN, not slots: the P3-ACCT window (1e-9 N*s, corrected
convention, not widened), the P4 window (1e-6 J/tick class), the P10
floors (1e-9 N*s class), all P5-P9 frozen forms.

## 7. Execution plan (phase 2, NOT STARTED; zero jobs launched at stop 1)

- All execution through
  `E:/PythonChimera/tools/monkey_campaign/task_package.py seal|run` with
  absolute paths; DISPATCHED SLOTS 2/3 per this lane's dispatch; BUSY =
  wait/retry >= 10 s, never a second directory, never another allocation.
- PREREG-FIRST: this draft, once pinned by the Lieutenant, is committed
  through the publication owner (the WALK-PHYS alone-first pattern,
  commit `2b58118c`; the W03I pattern, commit `3c66ad5b`) BEFORE any
  gated experiment; the package seal then pins that commit. A seal is not
  a substitute for the commit.
- PRE-GATED FEASIBILITY PROBE (declared, not a qualification run): build
  the ENGINE-ACCT binary from the pinned chain (orig blob + WALK-PHYS
  patch + W03I signed patch + accounting patch) inside a slot; 1-tick
  smoke with telemetry on. Outcomes: OK / BLOCKED(toolchain) — a BLOCKED
  is reported as the smallest missing prerequisite (the known class:
  vcvars quoting, cl PATH, include closure, 1-tick truncation crash,
  keep-path resolution — the W03I lineage's preserved refusals), never
  worked around outside the runner.
- Battery arms: clean1, clean2 (P1/P8), mode0 (anchor law), the clean v3
  telemetry arm (P2/P3-ACCT/P4-ACCT), mu0 (P5), cut (P6), cap15 (P7),
  inject (P9), signflip_acct + dropdrift (P10-ACCT). All receipts +
  streams declared with --keep; evidence anchored through anchor.py
  before any reference.
- Cost estimate (from the sealed lineage): ~7-14 s CPU per 302-tick arm
  at the measured 23-46 ms/tick; the S10/S11 recorders add evaluate()-
  class cost at stage states only; the whole battery well under 15 min
  CPU across the arms; slots 2/3 with retry-on-BUSY.

## 8. Honest-absent list (declared BEFORE any run)

- The drift construction (C1/C2) is NEW recording-layer code: its
  correctness class is the S10 consistency check + P10-ACCT(b) + P2, NOT
  a source-inherited proof; a construction defect stops the run (FALSIFIED
  or FAILED INSTRUMENTATION per which check fires) — never absorbed into
  a window.
- The engine-ledger REPAIR: ABSENT (a localization result, either way).
- Paired instrumented/uninstrumented perturbation test: ABSENT BY
  DECLARATION (the P1 scoping; carried).
- Launchable build / real-time / product runtime / player control: ABSENT
  (headless class only).
- Measured volar friction: ABSENT (0.6/0.4 remain NAMED PLACEHOLDERS,
  NB-01/02; fixed declared inputs, never tuned here).
- The universal no-hidden-channel claim: WITHDRAWN CLASS (never restored;
  outcome A supports only the narrow named-set closure claim).
- The stage-recording shadow's O(h) quadrature class: DECLARED — the S11
  companion measures it; the tick-level gate is on the FULL identity,
  where quadrature error is part of what the window must be derived
  against at freeze.
- The P6 rise census: EMITTED, NOT GATED (carried).
- Truncated-window full-window claims: IMPOSSIBLE BY LAW (carried).

## 9. Preservation law

The W10 sealed rows, the W03 anchor set, the WALK-PHYS lane, the
W03-SIGNED lane (its EVIDENCE appendices incl. A.7 F1-F3 are part of the
record), every store row, and every other lane's bytes are UNTOUCHED.
This lane's writes: `E:/ChimeraWork/monkey-coordination/engine-accounting/`
only (phase 1) + a NEW package contribution directory (phase 2) emitting
NEW artifacts. No Git mutation from this lane; the prereg commit goes
through the publication owner; no merge authority is claimed anywhere.
Every load-bearing artifact this lane reads or writes is hash-recorded in
this lane's `EVIDENCE.md` (hashes recorded at write time; amendments
append-only, never in-place edits).
