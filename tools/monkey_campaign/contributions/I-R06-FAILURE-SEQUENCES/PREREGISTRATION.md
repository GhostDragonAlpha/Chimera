# PREREGISTRATION — I-R06-FAILURE-SEQUENCES

- Card: I-R06-FAILURE-SEQUENCES (planning id R06)
- Attempt: c57fd6bb125142ee9d593f800eb32dd4
- Branch: branch-7 · Base revision: `9afbddcd90164b5544a16fd0bc72278d985eb6e3`
- Frozen BEFORE any implementation edit (Rule 0). Objective: a deterministic
  failure-sequence regression runner against the EXISTING input / focus /
  session APIs.

## THE THEORY (Rule 0 — all three parts)

**STATEMENT** (someone could disagree with it): The pinned product components
— `SessionFlow` filtering `FocusPolicy` filtering `InputMapper` — uphold, when
composed ACROSS component boundaries, three invariants that each component's
own unit tests do not jointly exercise:

  (a) RELEASE-NO-LATCH: after a key release (or any blur/disconnect-driven
      `release_all`) at instant E, the command sink never again receives a
      positive-speed record later than E + RELEASE_DECAY_MS (100 ms, imported,
      not redeclared); the post-release stream lands on an EXACT-0.0 record
      and then goes silent; every delivered record stays inside the frozen
      band [0, V_MAX_IN_BAND_M_S].
  (b) PAUSE-SILENCE: once the flow leaves `playing` (pause / restart hold /
      exit), zero further CommandRecords reach the sink, no matter how many
      decision ticks are delivered, and the quiesce leaves the mapper
      held-empty.
  (c) TEARDOWN-EXACTLY-ONCE: across repeated close, pause/resume/restart
      cycles and exit from every non-exited state, `World.shutdown_engine()`
      (terminate→wait→kill) runs EXACTLY once per session and `World.boot()`
      EXACTLY once per restart — never double-teardown, never skipped.

Someone could disagree: composition is exactly where unit-tested components
fail (each passes alone; the seam double-fires or swallows).

**PREDICTION** (not yet measured): driving the REAL pinned bytes through the
eight cross-component sequences listed below yields ZERO violations of
(a)/(b)/(c); and the same runner driven against deliberately-broken stand-ins
yields >= 1 violation per control. Full suite < 120 s (prediction: < 5 s),
bit-deterministic across repeated runs (injected integer-ms clock only).

**FALSIFIER** (named before the run; any ONE kills the build):
  - FS-1 (rewrite falsifier, from the card): the runner tests a rewritten
    stand-in instead of existing product code. Kill condition: any component
    module the runner binds to does not hash-match the extraction ledger, or
    the runner substitutes its own mapper/flow/policy logic anywhere in the
    sequence paths under test.
  - FS-2 (certification falsifier, from the card): simulated events credited
    as real device-loss certification. Kill condition: any claim in this
    card's artifacts that the mocked adapter runs certify real Windows/device
    loss behavior.
  - FS-3 (rubber-stamp falsifier): the runner PASSES a deliberately-broken
    component. Kill condition: `LatchingMapper` (ignores speed-key release) or
    `QuiesceIgnoringMapper` (ignores `release_all`) completes its sequence
    with zero violations. If the detectors cannot see latched input, the
    runner proves nothing and must not ship.

## THE SEQUENCES (cross-component; no duplication of existing unit assertions)

Existing unit coverage (NOT duplicated): `focus_policy_tests.py`,
`input_mapper_tests.py`, `session_flow_tests.py` test each component alone.
This card's value is the composed seams: flow×focus×mapper×sink×world doubles.

| id | name | components crossed | invariant |
|----|------|--------------------|-----------|
| SEQ-01 | release-stops-emission | flow→mapper→gate→sink | (a) |
| SEQ-02 | pause-silences-locomotion | flow→mapper (quiesce)→sink | (b)+(a) |
| SEQ-03 | resume-fresh-grid-no-phantom | flow→mapper (resume tail) | (b)+(a) |
| SEQ-04 | restart-through-pause boots-exactly-once | flow→world.boot→mapper | (c)+(a) |
| SEQ-05 | blur-mid-emission decays-to-silence | focus→mapper→gate→sink, flow gating | (a) |
| SEQ-06 | disconnect-reconnect no-zombie | focus(disconnect)→mapper, flow gating | (a)+(b) |
| SEQ-07 | mid-play restart key is a named no-op | flow(table)→world (no boot)→mapper | (c) |
| SEQ-08 | exit-from-attract teardown-exactly-once | flow→world.shutdown, terminal | (c) |

Controls (test-only, clearly labeled stand-ins, NEVER the system under test):
  - CTRL-01 `LatchingMapper`: speed-key release is swallowed; sequence of
    SEQ-01 replayed -> detector must flag zombie records.
  - CTRL-02 `QuiesceIgnoringMapper`: `release_all` swallowed; sequence of
    SEQ-02 replayed -> detector must flag post-pause emission.

## BOUNDARY STATEMENT (frozen up front)

All adapters/sinks in this card are MOCKED boundaries (recording sinks,
recording boot/teardown doubles, injected integer-ms clock). NO real Windows
process, device, window or engine is touched. NOTHING here certifies real
device-loss behavior; the sequences are regression fences over the pinned
headless logic only.

## NUMBERS (all imported from the pinned modules, zero redeclared)

RELEASE_DECAY_MS=100, INTERVAL_MS=50, VALID_MS=100, EXPIRY_TICKS=30,
V_MAX_IN_BAND_M_S=0.763625, OMEGA_MAX_RAD_S=1.6 — bound at runtime from the
hash-verified modules; the runner fails closed if binding fails.

## BUDGET

stdlib only; Python 3.11+; per-invocation < 120 s; total new output < 16 MiB;
code only inside WS; no network, installs, GUI, native builds, GPU, training,
process control, unbounded fuzzing.
