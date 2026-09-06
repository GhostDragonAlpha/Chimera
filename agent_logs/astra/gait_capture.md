# ASTRA gait-capture handoff

Base: 04d7bd7a8eb10167cbab05e4da469cb222a1c53a. Work branch:
`astra/gait-capture`. Offline derivation bench; engine certification is the
coordinator's separate task. No engine builds, HTTP writes, protected-file
edits, master pushes or force pushes.

## 1. Falsifier table

The full predeclared STATEMENT / PREDICTION / FALSIFIER table and derivations
are in `docs/THE_CAPTURE_LAW.md`. Actual command output is adjacent in
`gait_capture.txt`.

| Item | Result |
|---|---|
| Binding blob calibration | PASS: H=5.615639986, L=3.091284678; COM agrees |
| Analytic flow vs independent RK4 | PASS: 9.193e-14 wu |
| Zero-input standstill, unchanged-foot ablation | PASS controls |
| One-step CP error cancellation | PASS algebra, full-state error remains |
| Placement-only two-step full-state reset | PASS algebra, ~4e-15 error |
| Placement+signed impulse one-step reset | PASS algebra, ~4.4e-16 error |
| Energy and reset ledger | PASS assertions at 1e-9; perturbed E changes |
| Conditional pendulum period loop | PASS: 10 iterations, residual 4.403e-12 s |
| Independent pendulum return | PASS: 4.409e-12 s |
| Reverse-FK known-answer inverse | PASS both side controls |
| JNT3 subset vs full mirror | PASS: 0.0 wu, five poses with both legs active |
| Target-position closure | PASS: 0.0 wu |
| Sole tracking bound | FAIL: max 0.122037881 > 0.028078200; RMS 0.024728394 |
| Inverse pose return | FAIL: 0.296449956 wu; theta mismatch 1.975743440 rad |
| Passive endpoint velocity compatibility | FAIL: 3.407010996 wu/s jump |
| Passive clock + 10% CP reach recovery | FAIL under assumed 2L interval: T<=1.673330718 vs passive T>=1.763839384 |
| Physical clock, signed impulse authority, lateral contact | UNMEASURED; integration CLOSED |

PASS algebra never implies admissible foot placement or impulse. The assumed
2L interval is not a certified outer bound for this peculiar FK/sole geometry.
Local inverse failure is not a proof that no better inverse branch exists.

## 2. Files written

* `docs/THE_CAPTURE_LAW.md` — full derivation, pre-run membranes, measurements,
  contradictions and honesty ledger.
* `tools/gait_capture.py` — numpy/stdlib bench importing the existing mirror.
* `docs/THE_CAPTURE_INTEGRATION.md` — exact candidate target/inverse law,
  L/R mirror convention, transition equations and closed capture gate.
* `agent_logs/astra/gait_capture.txt` — real-blob report output.
* This handoff.

## 3. Falsified / retracted

The conditional clock is 1.831964036 s, not the small-angle candidate
1.763839384 s. Its successful scalar fixed point does not close the moving
hip, stance-to-swing endpoint, startup, rig or contact problem. Those missing
conditions are explicitly printed; the full physical clock remains unidentified.

CP-only first recovery step = 7.216921640 wu, outside the assumed 2L interval.
Full-state one-step reset needs d=5.754466305 wu and J/m=-1.932605984 wu/s:
braking, not a positive-only push-off. Preserving an off-orbit energy while
resetting to the target energy is impossible. Nominal energy is preserved.

The first exact-midstance kickoff needs J/m=1.865289511 and a half-time first
swing. A smaller kickoff J/m=0.555972770 enters the stable manifold and gives
asymptotic approach under periodic supports, not exact entry at first exchange.

The old small-angle integration premise disagrees with the exact shader.
One evaluation gives exact algebraic FK; no substep count repairs the measured
foot errors of this profile. The solver was NOT tuned until a pass appeared.

Additional topology check found 36,630 triangles in the committed blob versus
36,424 in the brief. The original stricter assertion fired. Since the updated
calibration makes COM/H/L binding and the repo wins, the final instrument
prints actual topology and checks validity instead of rejecting good data on
that stale count. Both blobs and the mirror remain unchanged.

## 4. Open items

Actual dynamic COM/mass distribution, swing inertia, signed force/impulse
limits and impact/friction laws; complete attainable foot set; periodic
inverse branch, sole orientation/contact, lateral balance; a driven swing
clock compatible with those constraints; live-engine certification and a
certified recovery policy. No visual or physical-engine score is claimed.

The request spans 1,000+ lines including explicit mathematical and integration
contracts. It is delivered as the requested single PR; the user explicitly
assigned engine implementation/certification to a separate coordinator.

## 5. Boundary hits and verification commands

No boundary needed crossing. `E:\PythonChimera` was not accessible or altered.
The authorized cloud checkout is the only working copy used here.

Commands from repository root:

```bash
OPENBLAS_NUM_THREADS=1 python -u tools/gait_mirror.py
OPENBLAS_NUM_THREADS=1 python tools/gait_capture.py --self-test
OPENBLAS_NUM_THREADS=1 python -u tools/gait_capture.py --require-ready
```

The inherited mirror completed: diagnostic foot max/RMS 0.879205/0.572348 wu,
its own placement falsifier fired. Its diagnostic clock was not reused.
The capture self-test exits 0. The real-blob readiness run exits **2**, by
design, after printing all results: the integration gate is CLOSED.
`OPENBLAS_NUM_THREADS=1` limits thread overhead only; it is not a dependency
or required configuration. The normal `python tools/gait_capture.py` command
runs the same report and exits 0 on successful measurement, never on gait
certification. No live-engine suite was invoked for this offline-only task.
