# PREREGISTRATION (DRAFT) — K02 reproducible climbing reset scenarios: VALID ATTRIBUTED INITIAL STATES, THE RESET DETERMINISM LAW, FALSIFIERS

Status: DRAFT authored by `wk-k-spec` for the Lieutenant. Per the publication
law this file is committed ALONE FIRST (separate-first) BY THE LIEUTENANT —
AFTER the K01 skill-specification draft it depends on (registry prerequisite:
K01); the committed bytes are the freeze and every emitted receipt must embed
`preregistration_sha256` of exactly those bytes and refuse any mismatch. No
implementation file, harness run, training run, measurement or capture frame of
this card exists at draft time. Write scope of the draft: the NEW lane dir
`E:/ChimeraWork/monkey-coordination/k-spec/` (NO_WORKTREES law honored; no
worktree, no clone; all CPU verification through
`python -B E:/PythonChimera/tools/monkey_campaign/task_package.py seal|run`).

- Card K02 (planning id K02, registry group "Climbing skills (core)"),
  agent-author `wk-k-spec`, lane `E:/ChimeraWork/monkey-coordination/k-spec/`.
- Registry row (verbatim, `MONKEY_COMPLETION_MAP.md`
  sha256 `0e3984578b0cae38ab435daaa77cc10559cceeadbaf9885c3f31b979a362ecae`,
  re-hashed 2026-10-02): "K02 | Build reproducible climbing reset scenarios |
  K01 | C10, C21 | Initial states are valid and attributable; setup/reset never
  becomes a hidden in-episode assist | Use one rigid trunk first".
- Dependency binding: this draft is pinned to the K01 skill-specification draft
  `E:/ChimeraWork/monkey-coordination/k-spec/PREREGISTRATION_K01_SKILL_SPEC.md`
  sha256 `fdc2e79aea9479fd4d6f9d761694ba1edbe6430b1bf1ee9df6fed64ca9ac0935`
  (authored in the same lane, same chain stop; the Lieutenant commits K01
  first). If the committed K01 bytes ever differ from that hash, this draft is
  stale and must be re-pinned BEFORE any dispatch.
- Build line: `E:/PythonChimera` HEAD `7222729eca6e9f97f25061c8b1dc3d229bb703d8`
  (dirty state preserved; nothing in the repo was modified by this lane).

## 0. Standing laws consumed (binding on every reading)

- THE OBJECTIVE-LINE LAW: "A COMPLETED SPECIFICATION IS NOT A TRAINED SKILL";
  "DEMONSTRATED IMPOSSIBILITY CAN CLOSE AN INVESTIGATION, BUT IT CANNOT
  COMPLETE THE PLAYABLE-MONKEY GOAL". Building reset scenarios constructs test
  infrastructure; it trains nothing, qualifies no physics, and completes no
  playable behavior. K02's completion is a reset-scenario CONSTRUCTION with
  receipts — never a climbing skill.
- THE REFUSAL/PREDICTION WORDING LAW (Captain correction #3): a predicted
  refusal observed is a SUPPORTED PREDICTION; each falsifier NAMES the
  observation that would CONTRADICT its prediction.
- THE CORRECTED-CORPUS AND SCOPE-LABEL LAW: only corrected corpus numbers are
  consumed (`climb-derivation/DERIVATION.md` section 7,
  sha256 `da34420558f6632b0544ca94bc3e25ece515027628c7bd8cc54b9fdd30b7ebd9`);
  every friction-bearing threshold below is a CONDITIONAL-CALCULATION carrying
  assumptions A1-A7 (per-reading mass, declared contact count, declared press
  ceiling, pad fixture class, NAMED placeholders mu_s = 0.6 / mu_k = 0.4, law
  forms, screening band [0.3, 1.0]); "Monkey-bark friction (macaque volar skin
  on bark at the 20-60 N operating load) is UNMEASURED" (the standing
  obligation string of the K01-chain opener prereg, `k-tier/PREREGISTRATION_K01.md`
  sha256 `227a06c83180b68846b921e3ea36a0b594b5395d331fd487d9c36cdac764a65e`,
  grounded in the FRICTION_SOURCES L9/P3 CONFIRMED GAP rows and the DERIVATION
  section 8.4 master verdict); THE 0.41 VALUE IS A
  DECLARED SCENARIO PARAMETER, NOT a monkey-bark measurement. THE RESERVED
  DECISION STAYS OPEN (mass lineage, gap 9). THE n=4 SHAPE DECLARATION IS A
  SEPARATE DECISION, NOT MADE HERE.
- THE FIXTURE-LINE PRECEDENT: initial states come from DECLARED FIXTURES with
  recorded identities — the K01/K02/G04 fixture line (the declared F03 S1
  press operating point, the G04 declared pad fixture class, the G06 fixture
  transfer pattern), never from hidden assists. "The A09 anatomical endpoint
  ids are NOT used as fixture ids (their owners stay unresolved in records)"
  (G04 report,
  sha256 `dfca5b5556efe018ca09be4577bf6fbb5df38bb5c9ebc33d15bd18646ba349c8`).
- ANTI-ASSIST MASTER LAW (the registry limit, verbatim): "setup/reset never
  becomes a hidden in-episode assist". DERIVATION section 5 K02 row freezes the
  form: "reset states expressed as declared fixture grasps with recorded facet
  ids; anti-assist law = the reset may not set any state the solver would
  refuse (the G04/G06 ledger identities as reset invariants)".

## 1. The initial-state catalog (fixture-only; one rigid trunk first)

Every reset state in the catalog is a DECLARED FIXTURE GRASP at the ONE rigid
climbable trunk (trunk_01; declared 0.074 m diameter x 1.158 m height, lateral
sites — DERIVATION section 5 K02 row). No anatomical reset exists in this
catalog (see section 4).

Catalog = the sealed G05/G06 scenario cases, each with its declared fixture
identity:

- RS-01..RS-08 (transfer scenarios, G06 fixture pattern —
  `evidence-store/MAT2-G06/report/REPORT.md`
  sha256 `2e4343191591322dca4667e428c09d1dc8dcae39c8a90a53cb5298d90ab2f206`;
  receipt
  `evidence-store/MAT2-G06/numerical/experiment_receipt.json`
  sha256 `cf5c9cc5b7d51a23f282313974f853edca83ca30c19edd51a36eb9ddf0d3feff`):
  the 8 transfer cases — band_lo/band_mid/band_hi x n=2/n=3 plus scene x
  n=2/n=3 — at the declared G06 schedule (approach 1, attach 4, load 8, hold
  11, handover 31, transfer 31, re-attach 193, attach2 193, load2 197, release
  220; total 229 ticks; climb-template envelope span 219 ticks from attach).
  Three of these are SUPPORTED closing cases (band n=3:
  0.13243500000000002 / 0.15082875 / 0.16922250000000003 N*s vs capacity
  0.18 N*s); five are HONEST NON-CLOSING failure arms (band_hi|n=2
  0.33844500000000005; band_lo|n=2 0.26487000000000005; band_mid|n=2
  0.3016575; scene|n=2 0.49236380190000006; scene|n=3 0.24618190095000003
  N*s). Failure arms are CATALOG ENTRIES, not defects: resets construct the
  states; the physics decides.
- RS-09 (adhesion control): the zero-mu control (band_mid|n=3|mu=0) — cannot
  hold, must slide; sealed sibling class slides 0.05150250000055512 m under
  full press.
- RS-10..RS-22 (support/hold cases, G05 battery —
  `evidence-store/MAT2-G05/report/REPORT.md`
  sha256 `1e5fcc7f81b5bd7b0ae3b460c72d5ed190510f66db4793c6b2e99756da8c8524`;
  receipt
  `evidence-store/MAT2-G05/numerical/experiment_receipt.json`
  sha256 `468185796db949ffd97b7e390de4adbc80aef74d1021445a8cfa28a74ef3dfbe`):
  the 13 sealed support cases (band_lo/band_mid/band_hi x n=1/2/3 plus scene x
  n=1/2/3 plus the zero-mu control), each starting from static press at the
  declared operating point with the sealed G01 stick/slip boundary as the
  expected verdict table (scene n=3 static threshold 0.5468840727038888
  standard-g / 0.5470708910000001 record-g; scene n=2 0.8203261090558333;
  band n=2 0.44129925000000003 / 0.5025908125 / 0.563882375; band n=3
  0.2941995 / 0.33506054166666666 / 0.37592158333333336 standard-g).

Per-state declared fixture identity (ALL states, no exceptions):

- trunk_01 lateral site; source facet (triangle 0) for hold rows, target facet
  (triangle 1) for hold2 rows; the run-time coplanarity probe reproduces the
  declared geometry (plane offset 0.0 m; refusal `target_facet_drift` armed);
- declared pads (the G04 pad fixture class; G04 section 9 disclaimer carried:
  "the fixture probes the CONTACT MECHANISM with declared pads; the
  creature-side grasp ... is NOT claimed");
- press at the DECLARED fixture operating point jn = 0.3 N*s per tick per
  channel (jn/dt = 60.0 N, the sealed F03 S1 operating point) — a declared
  fixture input, never an actuator qualification (x_press ABSENT, TC-8 0/8);
- declared standoff 2e-05 m (DERIVATION section 5 K02 row);
- fixture reach envelope 0.5 m (template travel 0.38599999999999995 m;
  x_reach ABSENT — fixture kinematics, not anatomy);
- per-reading mass declared per state (band 5.4 / 6.15 / 6.9 kg register
  scalars or scene 10.037998 kg); no state mixes readings.

## 2. Validity law — a reset may not set any state the solver would refuse

A reset state is VALID iff every one of the following holds at the reset
boundary, each machine-checkable from the pinned identities:

- V1 LEDGER IDENTITY: the full-tick ledger identity m*dv == press + weld +
  gravity + contact + anchor holds for every body at the reset tick (worst
  recorded residual class 1e-15..1e-12 N*s; refusal `ledger_imbalance` armed);
  the trunk anchor reaction is recorded and equals minus the summed trunk
  contact impulse; reciprocity residual 0.
- V2 FACET GEOMETRY: the coplanarity/facet probe matches the declared triangles
  (refusal `target_facet_drift`); the state touches the declared facets only.
- V3 DECLARED CONTACT SET: the contact set at reset is exactly the declared
  pad set at the declared channels (n as declared for the state); no
  undeclared contact, no snap, no interpenetration (the F04 frozen-case class
  governs).
- V4 SEAM-DELIVERED SETUP: setup telemetry is delivered ONLY through the
  declared G05/G06 seam keys (the 36 declared keys = 4 timing + 32 slots; dt
  0.005 s; strictly monotone; the x_* namespace refused with
  `named_absent_occupied`; the privileged registry empty). Any setup value
  delivered outside the declared seam is an assist, not a state.
- V5 NO SOLVER-REFUSED STATE: the reset does not set any state the solver
  would refuse — a reset that must fire ledger_imbalance, target_facet_drift,
  undeclared_field, named_absent_occupied, privileged_source, dim_mismatch or
  a nonfinite_value at or after the boundary is INVALID BY CONSTRUCTION and
  the scenario is refused, not repaired silently.

## 3. Attribution law — every initial state attributable

Every reset state carries a machine-checkable provenance record BEFORE any
episode executes:

- A1 fixture ids (trunk_01, lateral site, facet triangles 0/1, pad set,
  channel count n, reading) — anatomical endpoint ids are NEVER used as
  fixture ids;
- A2 the pinned receipt hashes that seal the state's expected physics (the
  G01/G04/G05/G06 receipt identities cited above; the corrected corpus rows of
  DERIVATION sections 7-8);
- A3 the episode seed — exactly one of the K01-declared climbing seeds
  20261002, 20261003, 20261004 — and the reset index;
- A4 the state's CONDITIONAL-CALCULATION labels (assumptions A1-A7) so no
  threshold is ever read as a measured monkey-bark value.

An initial state that cannot name A1-A4 is UNATTRIBUTABLE and unlawful.

## 4. Fixture-only law (conditional scope)

WITHOUT x_reach/x_aperture (both ABSENT; gaps 4-5), NO anatomical reset is
constructible or claimable: "without them resets are fixture-only" (DERIVATION
section 5 K02 row). All resets in this card are FIXTURE resets at declared
pads. Any future anatomical reset class is a NEW declared-fixture decision
requiring x_reach/x_aperture receipts and its own prereg — it is never smuggled
in by reusing fixture bytes. "Use one rigid trunk first" is the registry limit:
no second trunk, no deformable branch, no multi-tree scenario in this card.

## 5. The reset determinism law

- D1 BIT-EXACT RESET: a reset executed in two fresh processes produces the
  identical tick-0 state (the state-chain head identity; the sealed
  byte-identical trace class — G05 X2 "trace byte-identical across two fresh
  runs"; the stick-class fixture records exact-zero cumulative creep, the
  bit-exact cross-job determinism class). Any nonzero tick-0 delta is a
  determinism FALSIFIER hit, not noise to be tolerated.
- D2 SEEDED RESET: every reset-time stochastic draw (if any are ever declared)
  derives from the declared episode seed; undeclared reset-time randomness is
  prohibited.
- D3 RESET BOUNDARY: reset happens ONLY at the declared terminal/reset
  boundary of the scenario schedule (the 229-tick template boundary class).
  There is no mid-episode reset, no mid-episode re-press, no contact
  restoration, no pose-set, no creep erase, no force restore: each of those is
  a hidden in-episode assist and is FALSIFIER F4 below.
- D4 RESET IS OUTSIDE THE EPISODE ACCOUNT: reset operations never enter the
  reward, the energy account, the ledger identities of the episode, or any
  success metric; the episode's physics account starts at the reset boundary
  with the declared state and nothing else (C13: no residual support, teleport
  or hidden reset; C22: no snap/teleport, unaccounted impulse, stale grip or
  lost command at transitions).
- D5 REPRODUCIBILITY ACROSS SEEDS: for each catalog state and each declared
  seed, the reset produces the same tick-0 state modulo the declared
  seed-dependent fields; declared-seed-independent quantities (fixture
  geometry, facet ids, press operating point) are identical across seeds.

## 6. Falsifiers (each names the observation that would CONTRADICT it)

- F1 NONDETERMINISTIC RESET: prediction — D1 holds. The contradicting
  observation is NAMED: two fresh processes producing different tick-0
  state-chain heads for the same (state, seed).
- F2 UNATTRIBUTABLE STATE: prediction — every executed episode's initial state
  names A1-A4. The contradicting observation is NAMED: an executed episode
  whose initial state lacks fixture ids, receipt provenance, seed/reset index,
  or scope labels.
- F3 SOLVER-REFUSED RESET STATE: prediction — V5 refusals never fire on a
  lawful catalog state. The contradicting observation is NAMED: a catalog
  reset that fires ledger_imbalance / target_facet_drift / named_absent_
  occupied / privileged_source / undeclared_field / dim_mismatch /
  nonfinite_value at the boundary — i.e., the reset set a state the solver
  refuses.
- F4 ASSIST-SMUGGLING: prediction — no reset machinery touches in-episode
  state. The contradicting observation is NAMED: any in-episode performance
  difference attributable to reset machinery — a mid-episode state write, a
  re-press, an unexplained creep erasure (the stick class records EXACT ZERO
  cumulative creep; "recovery" from nonzero creep without a declared
  dissipative term is the assist signature), or a reset that enters the reward
  or energy account.
- F5 ANATOMICAL-RESET SMUGGLING: prediction — all resets are fixture resets.
  The contradicting observation is NAMED: any reset claiming anatomical
  validity, anatomical endpoint ids, or creature-side grasp validity from
  fixture bytes (x_reach / x_aperture ABSENT).
- F6 RESET-EQUALS-SKILL: prediction — K02 completion is a construction
  receipt. The contradicting observation is NAMED: any claim that reset
  construction constitutes a trained skill, a physics qualification, or
  playable-objective progress ("setup/reset never becomes a hidden in-episode
  assist"; "A COMPLETED SPECIFICATION IS NOT A TRAINED SKILL").

## 7. Verification plan (the evidence this card will emit; CONDITIONAL on K01
commit and section 0.4 of the K01 spec for anything training-adjacent)

- One sealed runner package per verification round through
  `task_package.py seal|run`; the scenario executor constructs each catalog
  state from the declared fixture identity, checks V1-V5 at the boundary, and
  emits per-state receipts: tick-0 state-chain head, boundary probe verdicts,
  refusal census (expected empty), and the declared-seed reset matrix (3 seeds
  x catalog states).
- Fresh-process duplication: every catalog state's reset executes twice in
  separate processes; the two tick-0 identities must match bit-exactly (D1).
- The G05 seam composition check re-runs on the reset battery: delivered key
  universe equals the declared set exactly; zero accepted samples outside the
  declared keys.
- Honest expected outcomes recorded BEFORE the run: the 5 non-closing transfer
  states and the zero-mu control are EXPECTED to fail their physics (observing
  those refusals supports the sealed boundary); the 3 band n=3 transfer states
  are EXPECTED to close at the placeholder mu (thinnest margin
  0.010777499999999968 N*s). A correctly predicted refusal completes a
  DIAGNOSTIC verification only — "DEMONSTRATED IMPOSSIBILITY CAN CLOSE AN
  INVESTIGATION, BUT IT CANNOT COMPLETE THE PLAYABLE-MONKEY GOAL".

## 8. Out of scope (explicitly)

Training (K03, gated on the grasp chain + P04 reservations); per-phase skill
evaluation (K04); anatomical resets (gaps 4-5); any second trunk, branch, or
multi-tree scenario (registry limit "Use one rigid trunk first"); friction
measurement (NB-01/02); the mass-lineage selection (gap 9); the n=4 shape
declaration; any claim that this card trains, qualifies or completes anything.
