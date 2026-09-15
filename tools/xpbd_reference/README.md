# tools/xpbd_reference — the coupled XPBD volume solve, CPU reference model

B1x's deliverable for the A1_XPBD lane. The preregistration
(`docs/evidence/agent_fleet/SHIP/A1_XPBD/PREREG.md`) is the contract; the
measured table it was derived from is `DIAGNOSTIC.md` in the same directory.
This package is the READABLE BLUEPRINT the later engine appliance ports into
`membrane_tick` — clarity is a deliverable, and every construction is the
piston idealization A12 measured on the live world, with no invented physics.

Pure Python + numpy. No engine imports; the live server is never touched.

## Map

| file | holds |
|---|---|
| `measured.py` | CONSTANTS with provenance (V0, cut areas A, reduced masses mu, kappa, the Leibniz J, the predicted omega tables) + the derived XPBD discrete-frequency map (`predicted_bias`, `predicted_decay`, `N_FIDELITY_10PCT`). No model. |
| `model.py` | THREE constructions on ONE constraint machinery: `rig_single_piston` (per-cell omega bars), `ring_coupled` (the 1949 rad/s coupled bar), `SlabChain` (the full planar stack: volume block + pins + servo rows + contacts — the port blueprint's SHAPE). A `System` is q, v, diagonal M, and rows reporting (C, J, alpha) refreshed from current q. |
| `solver.py` | `xpbd_tick`/`xpbd_substep` — THE preregistered coupled solve ((J M^-1 J^T + Lambda/h_s^2) dlambda = −C − (Lambda/h_s^2) lambda, nonlinear-Jacobian refresh every iteration, consistent velocity update, P = lambda/h_s^2 recovery); `explicit_tick_ring`/`divergence_probe` — the explicit baseline the prereg indicts; the frequency instruments (AR(2) single-mode fit, energy window, FFT lobes). |
| `battery.py` | The falsifier battery: P1–P6 + negative controls, each an ATOMIC probe returning numbers; `parallel_task_list()` + `run_probe()` + `assemble()` for the parallel runner; `format_bar_table()` for the printed table. |
| `run_battery.py` | The PARALLEL runner (see below). |
| `xpbd_reference_tests.py` | The battery as pytest-style tests (runnable under pytest OR `python -m tools.xpbd_reference.xpbd_reference_tests`). |

## Running

```bash
python -m tools.xpbd_reference.run_battery --json battery_results.json
python -m tools.xpbd_reference.xpbd_reference_tests      # the test battery
```

## WHAT PARALLELIZES (operator's standing rule 2026-09-14)

* **Process-level:** the battery is 35 INDEPENDENT atomic probes
  (`battery.parallel_task_list()`), mapped over a `multiprocessing` spawn
  pool (`imap_unordered`). The four cells' frequency probes, all six P2
  boundary cells, the three ring modes, P4/P5/P6 and the controls run
  concurrently. Each probe builds fresh systems inside, so determinism does
  not depend on scheduling or worker count — parallel and serial runs return
  identical numbers. MEASURED on this box (32 cores, 32 workers): 8.5 s
  parallel vs 14.5 s serial for the same bars; and in the pre-fix world
  (one 314 s straggler probe) the pool held the wall at 327 s where the
  serial order would have summed past it — any future heavy probe joins the
  pool instead of the critical path.
* **I/O overlap:** the runner prints a progress line and rewrites the partial
  JSON after EVERY completed probe — computation and disk writes interleave,
  and a killed run leaves every finished probe on disk.
* **In-process:** the numpy core is vectorized (constraint stacking builds
  (n, ndof) Jacobians and solves dense systems through BLAS, which releases
  the GIL), but the systems here are 3x3 to 12x12 — thread-level parallelism
  inside a probe would cost more in BLAS overhead than it buys. The unit of
  parallelism is the PROBE, which is where the seconds are.
* **What stays serial:** final assembly + bar-table formatting
  (microseconds), and each probe's internal loop (inherently sequential
  time-stepping).

## Port notes for the appliance (DESIGN.md's consumer)

* The solver is EXACTLY the shape the engine will run: stack [volume | joint
  | servo | contact], one regularized solve, refresh, correct, consistent
  velocity update. `SolveReport` already carries the `/xpbd_state` fields
  (iterations, substeps, per-cell pressure, residual).
* The discrete-map datum: a converged XPBD substep biases a mode's measured
  frequency by `predicted_bias(omega, n)` (measured = derived to <0.05% in
  the battery). At the operating point n=4 the coupled 1949 rad/s mode reads
  ~-37%: that is the SCHEME, not the model (n=32 validates the model to <2%).
  The appliance's calibration must budget this bias or raise n.
* Iteration counts and CPU cost per tick: `port_datums()` in battery.py
  (also in BATTERY_RESULTS.md).

 (Agent: B1x-xpbd-reference)
