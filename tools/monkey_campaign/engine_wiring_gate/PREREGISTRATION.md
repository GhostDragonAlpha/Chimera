# PREREGISTRATION -- engine_wiring_gate (the whole-game gate)

Task: ENGINE-WIRING-COMBINE-CORE, lane wk-engine-wiring. Declared BEFORE any
candidate capture run. This file's sha256 is pinned in INPUTS.json; the
runner refuses drift (`prereg drift`) before anything executes. Per
NO_WORKTREES.md the sealed package manifest + the runner receipts are the
precommitment records; the prereg bytes ride the sealed package that the
runs verify.

## Target under qualification

The REAL per-tick combine-core consumer: `MembraneTick::step()`'s
ordered-pass tail in ChimeraEngine/engine/membrane_tick.cpp, whose FALL pass
routes its ground-force evaluation through the deterministic combine
scheduler (combine_core.hpp -- the engine lift of the approved
wk-runtime-combine core at lane commit ff4db63) over PR #319's
contribution_executor.hpp seam. Baseline under comparison: the SAME tick at
the base commit 522e4ae2f77b3bf0b011c932e0565d8a01f24e9b (blob
ae11ac7696d8324a9e8d15e5bea0a75e678e2763 for membrane_tick.cpp), byte-assert
from the shared repository's Git object database before every run.

## Fixed experimental parameters (no post-hoc changes)

- Scene: the probe's deterministic synthetic membrane, 9x7 grid, 96
  triangles, 63 vertices, authored rest y in [0.0200, 0.0220] m above the
  floor; generation constants are IN THE PROBE SOURCE (hash-pinned here).
  No classification, no seals, no touches.
- Enabled rungs: gravity ON (the fall pass; the wired consumer). Stance,
  gait and the reflex set are ATTEMPTED and their enablement RECORDED; on
  this synthetic scene they refuse (no classification / no sealed torso
  cell), which is itself deterministic and part of the capture.
- dt = 1/60 s; ticks = 180 (3 s: free fall, penalty-spring landing, settle).
- Worker counts: candidate at 1, 2, 4. Baseline runs its only (serial) mode.
- Compilers: two jobs, one backend each -- GNU (MinGW-w64 g++ 15.2.0,
  `-std=c++17 -O2 -fno-fast-math -ffp-contract=off -pthread -Wall -Wextra`)
  and MSVC (Visual Studio 2022 BuildTools cl 19.44,
  `/nologo /std:c++17 /EHsc /O2 /fp:precise /W4 /MD`).
- Chunk law: exactly FOUR canonical chunks at every worker count
  (worker-count-invariant contribution set).

## Predictions (all must hold; any single miss fails the gate)

P1 (worker byte-identity): the candidate's full capture stream -- fall
scalars, per-tick combine receipts (canonical store digest + routed
contribution list + witness count), and the full verts9 stream in C99
hexfloat -- is byte-identical across workers 1, 2 and 4, under EACH
compiler backend, after normalizing the single `GATE workers=` provenance
line.

P2 (serial faithfulness): the candidate's V-stream (every physics float of
every tick) is byte-identical to the unwired baseline's V-stream, at every
worker count, under each backend. The wiring changes WHERE the arithmetic
runs, never a value.

P3 (cross-backend value identity): the parsed hexfloat VALUES of the two
backends' captures are identical (the C99 %a text form may differ in
trailing-zero padding between runtimes; parsed IEEE-754 bits may not).

P4 (witness law): the ground-evaluation witness advances exactly once per
gravity tick (witness=180 after 180 ticks), in every configuration.

P5 (mechanism laws, in-engine): the lifted core refuses a non-owner write
(`combine_non_owner_write`), a double state write
(`combine_double_state_write`), an undeclared contribution output
(`combine_undeclared_contribution_output`), and the engine setter refuses
worker counts above the 4-thread profile; the material payload parity check
passes (the compiled membrane material constants bit-match the
tools/material_iface first-consumer payload).

## Falsifier

The gate FAILS (and the evidence is kept, never hidden) if any of: a
compile failure under either backend; any refusal code or FAIL token in any
capture; any byte difference under P1; any byte difference under P2; any
parsed-value difference under P3; a witness count other than exactly the
tick count under P4; any mechanism check failing under P5; or any pinned
input drift (base blobs, prereg, payload, probe). Failure means the
parallel path is NOT qualified: the live dynamics default remains ONE
worker (the serial law) and no default-enable may be proposed from this
package.

## Scope and standing law

- THE SERIAL LAW (PR #319, standing): keep the live dynamics default at one
  worker; use the batch/parallel path only for measured, independently
  evaluable configurations; measure the real consumer before enabling
  parallel execution by default. This gate IS that measurement; its
  receipts do not by themselves change the default. Any default change is a
  separately authorized, separately reviewed change.
- No rendered frame is involved: the capture is numeric (hexfloat text).
  The capture-gate-template visual pipeline is therefore not implicated.
- Receipts must be anchored through the campaign evidence store before any
  result is referenced. Worker self-reports do not qualify the gate:
  independent Sergeant review (compiler-suite authority) is requested
  through the Lieutenant; merge authority stays with the authorized
  reviewer/integrator.
- No physics claim: the qualified claim is determinism of the wired
  consumer over the pinned scene, nothing else.
