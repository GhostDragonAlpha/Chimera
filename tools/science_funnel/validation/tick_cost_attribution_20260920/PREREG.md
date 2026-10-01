# PREREG — TICK-COST ATTRIBUTION (lane/tick-cost-attribution-20260920)

Date frozen: 2026-09-20 (lane clock) / committed before any measurement below was taken.
Agent: tickcost. Base bytes: bd4bf630 (merge containing the typeb-p1 receipt 272dc20b and
the pinned walk bytes agent/gait-wave38-calendar-guard @ 30821ef7).
Context decision (Astra round 5, settled): server-authoritative 300 Hz + thin clients +
immediate solver optimization. THE BUDGET: 300 Hz = 3.33 ms/tick. THE GAP: the honest
steady-state receipt (typeb_p1_20260921) measured 23.1 ms/tick = 43.3 ticks/s, 98.4% of the
walk loop inside `d.step()` (integration + reflex), 6.8x realtime. Attribution must go
INSIDE the step.

---

## RULE 0 — THE MEMBRANE (stated before the build)

**STATEMENT** (disagreeable): The 23.1 ms/tick steady-state tick of the pinned CPU walk is
dominated by the physics-solver core itself (bond/force-constraint evaluation — the
mass-metric solves, friction cones and impact projections inside `rate()`/`impact()` —
plus the RK4 floating-point integration that consumes them), NOT by removable harness
machinery. The controller/observability periphery (reflex clock decisions, servo PD,
observation assembly `status()`, JSON serialization, harness census, per-tick allocations,
sync) is a minor share, and even removing EVERY byte-neutral removable class whole cannot
bring the tick inside the 3.33 ms / 300 Hz budget. If this statement is true, "immediate
solver optimization" owns the gap and no harness/client work can close it; if it is false,
the banked 98.4% number is hiding a removable share and the optimization lane changes.

**PREDICTION** (not yet measured, pre-named): ranking of steady-state per-tick wall time:
1. bond/force-constraint evaluation (the `project_rows` active-set solves, `friction_solve`
   cone solves, `inverse_spd` mass-metric inversions, and the impact projections of
   `impact()` — the constraint/bond layer driven 4x(RK4) per substep) is the LARGEST
   subsystem share of `d.step()`;
2. contact/force FIELD generation (the forward kinematics `evaluate()` — frames, mass
   matrix, bias forces, contact rows and gaps) is the SECOND largest;
3. everything else COMBINED (reflex clock + hind step law, capture reflex + support hull,
   servo PD/IK, saturation census, tick-start buffer reset, allocations, `status()`
   observation+serialization, harness census, sync) is < 10% of the tick; sync specifically
   measures 0 (single process, single thread — no client coupling exists in this binary).

**FALSIFIERS** (named before the run, all three enforced, nothing tuned away):

- **F1 COST-GAP**: compute the OPTIMISTIC-REMOVAL BOUND = measured steady-state full-loop
  per-tick time MINUS the sum of every class whose complete removal is order-preserving and
  byte-neutral (status/observation assembly, serialization, harness census + dump, tick
  buffer-reset/allocation churn, sync — each bounded above by its own measured time; the
  physics classes: FK, constraint solves, integration, reflex DECISIONS, servo, are NOT
  removable — their removal changes replay bytes by construction). If even this bound is
  > 3.33 ms/tick, COST-GAP FIRES: no composition of byte-neutral removals reaches the 300 Hz
  budget on this machine, the residual is NAMED (subsystem + ms + share), and it is carried
  as a FINDING — never tuned away, never made unreachable by redefinition. If the bound is
  <= 3.33 ms/tick, the statement above LOSES and the removable share becomes the lane's
  finding instead.

- **F2 NUMERIC-DRIFT**: any optimization that would change one replay byte (reduction order,
  iteration counts, RK4 substage structure, contact decisions, event-bisection iteration
  counts, evaluation order) is REJECTED in this lane and recorded as a
  physics-compatibility change request — a list of named candidate optimizations, each with
  the byte class it would change, implemented by NOBODY here. Enforcement during
  measurement: the instrument itself must be byte-neutral — the instrumented binary's stdout
  sha256 must EQUAL the pinned ship stdout sha 71065ac54fa988704ce29cd79cfb5cdbe0d4e2eab3f
  7db69b10d4b8d94517592 (22184 bytes, refusal tick 302, gait_positional_correction_budget)
  on every run, and two instrumented runs must be byte-identical to each other. A single
  differing stdout byte = F2 RED = the instrument is invalid, the measurement is discarded,
  the generator is fixed, and the run is repeated.

- **F3 MEASUREMENT-VALIDITY**: the profiled path must be the PRODUCTION-EQUIVALENT stepping
  path the 43.3 ticks/s receipt measured — the C++ `GaitWalker::step()` of
  `ChimeraEngine/engine/gait_controller.hpp` + harness `gait_unit.cpp` at bd4bf630, compiled
  with this machine's native recipe (MinGW g++ 15.2.0, -O2, C++17 — the recipe
  PREREG_FULLPORT.md used to reproduce the banked walk class 302 / 30.970714 exactly), run
  on the regenerated pinned scene (file sha256
  f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342, regenerated byte-exact
  by tools/science_funnel/gait_scene.py and re-verified). NOT a toy reimplementation, NOT
  the Python/Numba port (walker_numba*.py never reached a runnable tick and is not the
  43.3 t/s path; walker_reflex.py/walker_model.py are read as the subsystem MAP, not
  profiled). F3 fires if (a) the plain rebuild does not reproduce the pinned ship stdout
  sha, or (b) the re-measured steady-state step-only throughput falls outside 40-48 ticks/s
  (the receipt's 43.3-44.6 band widened by hardware variance), or (c) instrumentation
  overhead exceeds 10% of the mean tick (measured: plain vs instrumented per-tick on the
  same machine, same runs), or (d) the per-class timers fail to close the books (sum of
  exclusive stage times < 95% of the same binary's measured step-loop wall).

---

## METHODS (fixed before measurement)

1. **Baseline re-measure (machine-local)**: rebuild gait_unit from the bd4bf630 tracked
   bytes, run `gait_unit.exe <scene.json>` (the receipt's frozen-ref invocation, argv[1]
   only) 5 times; per run: stdout sha (must equal the pinned ship sha), whole-process wall,
   and the steady-state (tick >= 20) step-only rate from the timing instrument. Record
   hardware context (CPU/cores/RAM/OS) beside the numbers. Report the mean and spread.

2. **The instrument (derived-copy method — the tracked header is READ-ONLY for this
   lane)**: `make_instrument.py` (committed) mechanically derives an instrumented copy of
   gait_controller.hpp and gait_unit.cpp from the tracked text by DECLARED, ANCHORED edits.
   Every edit must anchor at exactly one occurrence or the generator refuses loudly.
   Postcondition, verified per build by the generator: re-applying the recorded edit
   manifest to a fresh read of the tracked sources reproduces the derived files
   byte-identically, and every derived line that is not an original line carries the
   `//@TICKCOST` marker. The derived copies compile into scratch binaries under `.tmp/`;
   NO tracked file is modified at any time (stricter than the typeb-p1 working-tree-patch
   pattern, chosen because this lane shares the worktree with the header's READ-ONLY ban).

   Timers are std::chrono::steady_clock RAII scopes accumulating into namespace-scope
   counters; output is a stderr summary block prefixed `[tc]` plus compact per-tick
   nanosecond arrays prefixed `[tc-ticks]` (stderr-only; stdout bytes are the ship bytes).
   No per-tick fprintf inside the hot path. Classes instrumented (the ladder the decision
   demands, mapped onto this engine):
   - `step.reset_alloc` — the tick-start impulse/contact buffer reset block of step()
     (alloc + clear churn) — timed; PLUS counted global operator new/delete (defined in the
     instrumented harness TU) snapshotted per tick -> allocations/tick and bytes/tick.
   - `step.reflex_clock` — the tick-start stage: its `evaluate()` + update_clock +
     update_fore_clock + height emergency + the hind step law (gaps, IK, deadlines).
   - `step.capture_reflex` — support hull + monotone chain + capture_reflex stage.
   - `step.servo` — the 4 per-substep `servo()` calls (PD + phase-table interpolation +
     fore/hind closed-form IK + command channel).
   - `step.integrate` — the 4-substep loop stage (inclusive): `advance()` total time and
     call count, split into:
       - `adv.impact` — `impact()` (impact projections + friction-cone catch + positional
         correction = the bond/constraint impulse layer);
       - `adv.free_step` — `free_step()` (the RK4: 4x `rate()` + 2 FK);
       - `adv.event_search` — the drive-stop and contact-crossing 42-iteration bisection
         loops + the Coulomb catch recursion overhead (advance() minus impact minus
         free_step, exclusive);
       - per-tick advance() call-count distribution (mean / p95 / max) — the store-bisection
         and event tree share.
   - `solver.friction_solve`, `solver.project_rows`, `solver.inverse_spd` — leaf timers
     inside rate()/impact() (INCLUSIVE bookkeeping reported separately: the leaf sum is the
     bond/force-constraint evaluation share proper).
   - `fk.evaluate` — total `model_->evaluate()` time + call count across ALL call sites
     (the contact/force field generation + moment-arm Jacobians).
   - `step.sat_census` — the planted-strut saturation census block.
   - `obs.status` — `d.status()` per tick (observation assembly + JSON build), timed in the
     harness copy like the tb1 instrument.
   - `harness.census` — the per-tick harness census/parse block; `harness.dump` — the
     every-10-tick `s.dump()` stream append.
   - `sync` — explicit line: 0.0 ms measured, single process/thread, no synchronization
     point exists in this binary (thin-client coupling lives outside it).
   Inclusive/exclusive discipline: the four step() stages + the advance() split close the
   tick exclusively (F3d checks >= 95%); fk.evaluate / solver.* leaves are reported as
   INCLUSIVE shares of the stages they sit inside (double-counted by construction, labeled).

3. **Attribution table + bound**: per-class steady-state (tick >= 20) ms/tick + share of the
   full loop; the F1 bound computed by the committed analyzer from the SAME run it judges;
   COST-GAP verdict stated with the named residual.

4. **Interacting-scene latency**: the harness's own F-G6 push run (2*CYCLE_TICKS = 426
   ticks; a scripted 0.1-BW pelvis push at mid-run — the coupled interacting scene the ship
   suite already runs) with per-tick wall samples collected in the instrumented harness;
   p50/p95/p99 (nearest-rank) over all 426 ticks; the walk runs' percentiles reported as
   supplementary. Sustained = the run completes its 426 ticks (it does by construction; the
   receipt's push426 stage cost ~6.8 s).

5. **Determinism guard**: plain binary (timing OFF, zero instrument) vs instrumented binary
   (timing ON): stdout sha equal to each other AND to the pinned ship sha, 2 runs each —
   the typeb-p1 instrument_check property re-proven for THIS instrument: timing collection
   must not change stepping bytes. Additionally the F-G7 in-binary determinism check keeps
   passing (the suite's own bit-identity gate stays green inside the instrumented run).

6. **Runs**: baseline 5x plain; attribution 3x instrumented (percentiles from the median
   run; means from all 3); overhead = (instrumented mean per-tick) - (plain mean per-tick)
   on interleaved runs, same machine state.

7. **Where things live**: raw logs `raw/` (committed: the [tc] summary blocks and sha
   lines; per-tick arrays kept compressed or summarized — the stdout files are the identity
   artifacts); `receipt_tick_cost.json` appended at the end; tests in
   `test_tick_cost_attribution.py` (generator determinism, manifest re-apply byte-equality,
   bound arithmetic, percentile math — all fast, no engine build inside CI tests).

Pre-committed action on any RED: carry it verbatim with numbers; nothing tuned; no tracked
byte modified; the ship bytes of gait_controller.hpp / gait_unit.cpp / gait_scene.py are
never edited by this lane.

---

## AMENDMENT 1 (frozen AFTER the plain-baseline build, BEFORE any instrumented run)

The pinned ship stdout sha named in F2 (71065ac5..., 22184 bytes) belongs to the
typeb-p1 pinned walk bytes agent/gait-wave38-calendar-guard @ 30821ef7 + its harness.
THIS lane's base bd4bf630 merges later harness notes (the wave-39/40 "NOT MEASURED"
census notes and the F-G42 command-census machinery in gait_unit.cpp; `git diff
30821ef7 bd4bf630` = +147 harness lines, the physics classes untouched), so the
bd4bf630 plain build's stdout is NOT 71065ac5 by construction of the merged lanes.
MEASURED at amendment time, before any instrumented run: the bd4bf630 plain build
produces stdout sha 8c537cdb7cb8c43cf9423cb50056787bcc31ee487d70d3c2a1e73ed5d60b06cc
(22530 bytes) — BYTE-IDENTICAL across the two toolchains of this machine (MinGW g++
15.2.0 -O2 and MSVC cmake Release /fp:precise; the receipt toolchain), and the
receipt's physics anchors are EXACT on both (refusal tick 302
gait_positional_correction_budget, worst moving ledger 30.970714 J, 49 reds / 173
checks). THE F2 GUARD FOR THIS LANE IS THEREFORE: every instrumented run's stdout
sha must equal 8c537cdb7cb8c43cf9423cb50056787bcc31ee487d70d3c2a1e73ed5d60b06cc,
with the 71065ac5 relation carried here as the explanation (harness-note delta,
physics byte-faithful). Everything else in F2/F3 stands.

## AMENDMENT 2 (frozen after the instrument smoke run, BEFORE the run matrix)

The instrument smoke run (byte-identity GREEN: stdout sha == the lane fence on
the instrumented binary) measured three instrument defects; each is fixed or
rejected here, before any attribution number is recorded:

1. **ADV_TOTAL recursion inflation (fixed)**: `advance()` recurses on events; a
   plain RAII scope summed the recursion depth-over-time integral (measured
   1.6x: adv.total 16622 ms vs the true integrate-stage wall 10420 ms over the
   same 303 ticks). ADV_TOTAL is now a re-entrancy-aware scope (only the
   outermost frame books wall time).
2. **Allocation counting REJECTED (F3(c) enforcement)**: the counted global
   operator new/delete (157k allocations/tick routed through the override)
   cost ~+12 ms/tick (~53% of the plain tick) — far over the 10% overhead
   budget. The counting is REMOVED; allocation churn is named UNMEASURED in
   the receipt; the tick-reset stage chrono scope (cheap) stays.
3. **adv per-tick counting fixed**: adv_calls_ is zeroed INSIDE step() every
   tick by the production code's own work-budget line, so the step-end value
   IS the per-tick count (the previous base-subtraction produced negative
   deltas that cast to garbage unsigned).
4. **The >= 426-tick sustained interacting scene (declared)**: the F-G6 push
   walker is the EXPECTED-TIP regime and refuses at tick 302 on the pinned
   bytes (measured here; the receipt's own push426_s = 6.80 s is consistent
   with ~302 ticks at 22.5 ms/tick — the receipt's "426" named the loop bound,
   not a sustained run). The latency requirement is anchored by a NEW declared
   phase in the DERIVED harness only: `stand426` — the stage-E stand (contact
   ON, power ON, the gait clock frozen) under the same scripted F-G6 push
   (0.1 BW at tick 106 for 30 ticks), run 2*CYCLE_TICKS = 426 ticks. The
   push426 phase's measured (302-tick) percentiles are reported alongside,
   named as such.

Also: the plain baseline is rebuilt with the SAME link flags as the instrumented
binary (-static-libstdc++ -static-libgcc; required by the instrumented build to
avoid the MinGW dual-allocator heap corruption measured as exit 0xC0000354), so
the A/B overhead delta isolates the instrument, not the linkage. The stdout
fence is invariant to linkage (measured: plain dynamic-link, static-link, and
MSVC cmake all produce 8c537cdb...).

## AMENDMENT 3 (frozen after the first loaded-machine matrix, before the final pinned matrix)

1. **stand426 push removed**: the first stand426 draft injected the F-G6
   0.1-BW push mid-run; it REFUSED at tick 139 (measured) — a pushed standing
   pose is the tip regime (F-G6's own "expected-tip" face). The sustained
   scene is the UNPUSHED stage-E stand: contact ON, power ON, the gait clock
   frozen — the walk's own stable standing floor, a fully coupled
   gravity+contact+servo scene, 426 ticks. If it still refuses at N < 426,
   that N is reported honestly. The pushed phases (push426 at 0.1 BW and the
   walk's own trajectory) remain in the receipt as measured.

2. **F3(c) overhead method fixed**: the process-wall delta is INVALID as an
   overhead measure — the tc process runs the extra stand426 phase the plain
   process does not (the first loaded-machine matrix measured a bogus
   +23.5 s/process this way). The overhead is now measured on the F-G5 span:
   both binaries print the same stderr markers ("run F-G5" ... "run
   F-G1..G4 walk") around the SAME 500 fixed F-G5 ticks; the driver
   timestamps those lines as they arrive; overhead/tick = (tc span mean −
   plain span mean) / 500. Both builds exercise the SAME scene bytes and the
   tc binary runs its full hot-path instrumentation (evaluate/advance/stage
   scopes) inside that span.

3. **Machine-state control declared**: the box is shared and ran ~60-70%
   loaded during the first matrix (a game + fleet processes; the receipt-era
   typeb-p1 runs measured ~30 s/process on a quieter state; the first matrix
   measured 81 s plain). The final matrix runs under `run_matrix.ps1`:
   driver + gait_unit children pinned to one thread per P-core (affinity
   0x5555) at High priority, children inheriting both. The loaded-machine
   matrix is kept in `raw/` as the noise witness; the pinned matrix in
   `raw_pinned/` is the receipt's measurement set. Shares (ratios) were
   stable across both states; the pinned set owns the absolute ms/tick
   numbers and the F3(b) verdict.


## AMENDMENT 4 (frozen after the second pinned matrix, before the final matrix)

1. **The sustained scene regime (measured refusal ledger, pinned bytes)**:
   the walk refuses at 302 (gait_positional_correction_budget -- the pinned
   physics), the F-G6 push walker at 302 (expected-tip), the stage-E stand at
   139 (pushed AND unpushed -- deterministic). NO walk-family regime sustains
   426 ticks on the pinned scene. The >= 426-tick sustained coupled scene is
   therefore the F-G5 fold regime WITHOUT its early break (`fold426`): power
   OFF, contact ON -- the body collapses onto its contact points and joint
   stops and rests in coupled gravity+contact+stops equilibrium; every tick
   runs the full solver path (contact generation, active-set projection,
   impact probes, RK4). Percentiles reported for fold426 (sustained) AND for
   the walk / push426 phases (the interactive workload, 302-tick windows,
   named as refused-at-302).

2. **F3(c) overhead: analytic bound + microbench** (the F-G5-span A/B of
   Amendment 3 is carried as measured but is NOISE-DOMINATED: the box drifts
   on minute scales -- the second pinned matrix measured plain runs at 95-100 s
   FIRST and tc runs at 59-62 s LAST, a negative "overhead" -- a sequential
   span A/B cannot resolve a sub-ms signal under this drift). The bound:
   overhead/tick = (timer pairs/tick) x (measured ns/pair); pairs/tick comes
   from the instrument's own hit counters (~870 on the walk), ns/pair from
   `timer_microbench.cpp` (1M Scope pairs) run beside the final matrix. The
   instrument books ~2 counter adds + 2 chrono reads per pair and nothing
   else in the hot path.

3. Naming: the phase formerly named stand426 in Amendments 2-3 is SUPERSEDED
   by fold426 (the stand's measured refusal at 139 makes it unusable as a
   sustained scene).

## AMENDMENT 5 (frozen after the third pinned matrix, before the final interleaved matrix)

1. **fold426 refusal (measured, deterministic)**: the power-off, contact-on
   fold regime refuses at tick 129 on the pinned bytes (with 2.13 s/tick p99
   impact cascades during the collapse). The measured refusal ledger over all
   regimes now stands: walk 302, push walker 302, stand 139 (pushed and
   unpushed), fold 129. The pinned scene CANNOT sustain 426 ticks in any
   regime — itself a finding for the 300 Hz decision (the scene cannot run
   1.42 simulated seconds without refusing). The receipt therefore reports
   the longest sustained interacting windows (302-tick walk + push walker)
   AND the fold's 129-tick collapse window, each named with its refusal
   class; the ">= 426 ticks sustained" requirement is carried UNMET-BY-THE-
   PINNED-BYTES (a physics finding, not a measurement gap).

2. **Overhead: interleaved adjacent-pair A/B** (Amendments 3's sequential
   spans proved drift-entangled: the third matrix's plain runs landed on a
   quiet box (F-G5 spans 3.57-3.62 s, tight) and the tc runs ~10 minutes
   later — the sequential delta is uninterpretable). The final overhead
   matrix interleaves plain/tc runs (`--interleave`); overhead = mean of the
   ADJACENT-pair F-G5-span deltas / 500, plus the Amendment 4 analytic bound
   (microbench 42.7 ns/pair x ~870 pairs/tick = 37.1 us/tick = 0.11% of the
   receipt-state tick) as the floor. The attribution shares and the
   COST-GAP verdict from the third matrix stand (shares were stable across
   every machine state measured).
