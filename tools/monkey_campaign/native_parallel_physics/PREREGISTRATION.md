# Native parallel body contributions: bounded software/physics verification

Prepared before implementation on 2026-10-02 UTC. Base repository commit:
7222729eca6e9f97f25061c8b1dc3d229bb703d8. This is operator-authorized isolated
development, not an admitted card, published preregistration, or physics gate.
No live engine/source lane is changed. All executions use sealed CPU packages.

Prediction: the existing native articulated evaluation can compute independent
per-body mass, gravity, bias and potential contributions concurrently after its
parent-ordered kinematics pass, then reproduce the baseline evaluation and coupled
trajectory bytes when one owner sums in the original body order on one pinned
compiler/backend. CoupledDynamics remains the sole state integrator. Default
execution remains serial; concurrency is explicitly requested and capped at four.

The executor must be persistent (not spawn per RK stage), complete all submitted
body tasks before returning, propagate the earliest-index task failure
deterministically, and remain usable after a task failure. An executor failure
must not publish a partial Evaluation. Thread startup failure must join already
created workers before propagating. Recursive use on its own worker must refuse
rather than deadlock. Distinct invocations on one pool serialize safely.

Contradicting observations / failure criteria:

- Any finite tested mass/gravity/bias/potential/frame/point-force output differs
  bitwise between baseline, refactored serial and requested 2/4-worker execution
  under the same compiler and floating-point flags.
- Reordering completion changes outputs, leaves unjoined work after failure,
  exceeds four worker threads, or exposes a partial result as successful.
- A legacy/native analytic regression ceases to pass, or coupled trajectory and
  energy-accounting output differs between serial and parallel evaluation.
- A synthetic mechanics control violates its analytically derived mass, gravity,
  virtual-work or kinetic-energy identity within a fixed 1e-10 scaled tolerance.
  This tolerance is a software numerical check, not a biological uncertainty band.

Inputs: reuse pinned repository source/anatomical reference fixtures when
available. Any small hand-authored pendulum/multibody fixture is declared synthetic
in its filename/report and is not evidence for macaque mass, strength or climbing.
Read-only external dependencies must be copied only as a small declared package
closure, hashed and retained in an input manifest before running.

Evidence: compare separate baseline/candidate binaries (baseline headers copied
before edits); keep compile command/version, source hashes, test reports, failures
and bounded runner receipts. Measure elapsed execution only as a diagnostic: no
speedup prediction and no speed acceptance threshold. Small articulated models
may be slower in parallel because scheduling overhead dominates.

Scope exclusions: no GPU claim, no simultaneous RK stages (each depends on the
previous stage), no full-game build/deployment, no physical hand/ground contact
qualification, no global rollback redesign, no implicit-coupling convergence
claim. This advances a native contribution seam used by existing physics.
