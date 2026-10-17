# Artificial proteins: AP01 executable research workflow

This is the first executable increment of GAME_PLAN_ACTION_RPG.md §11.20.
It uses the existing constant-gamma triangle law and Vulkan membrane shader.
Three seeded asymmetric fan recipes become measured rail-port responses, conservative
response tables, a two-piece coupled equilibrium, and one reduced pair reused in two
three-piece surroundings. An independent edge-altitude energy formula checks the
triangle implementation; a separate energy minimization checks assembled positions.

The supports are fixed and the central attachment has one scalar normal-rail DOF.
These are explicit fixture constraints. This does not implement general folding,
contact, mass, tissue, damage, dynamics or multiport matter. The current table is
learned from measurements by interpolation; no Noether/neural training is claimed.
A six-triangle example is useful for validating the interfaces, not demonstrating
that neural inference would accelerate a game. Native captures show measured single
patches. The current engine does not populate its rendered-byte hash, so full
render/state binding is explicitly unqualified; accepted uploaded positions and
forces are checked independently. The two hash fields have different schemas and
should not be compared for equality. In particular, coupled assemblies are currently qualified only in the research harness.

## Run from the project root

On this host, use PowerShell:

```powershell
$apPython = 'D:\Chimera-Maintenance\Runtime\local-ai\Strata\.venv\Scripts\python.exe'
cmake -S tools/artificial_proteins/native -B .tmp/artificial-proteins-build -A x64
cmake --build .tmp/artificial-proteins-build --config Release
& $apPython -B -m unittest tools.artificial_proteins.test_workflow -v
& $apPython -B -m tools.artificial_proteins.runner run --out .tmp/ap01-cpu-new
& $apPython -B 'D:\Chimera-Maintenance\Runtime\local-ai\run_gpu_job.py' --wait 30 -- $apPython -B -m tools.artificial_proteins.runner run --out .tmp/ap01-gpu-new --gpu-exe .tmp/artificial-proteins-build/Release/artificial_protein_batch.exe --engine-exe .tmp/body-engine/Release/chimera_engine.exe
& $apPython -B -m tools.artificial_proteins.runner check --out .tmp/ap01-gpu-new
```

Each new run needs a new output directory. The GPU command holds one existing
managed reservation for all 351 cases and optional renderer snapshots. A busy
model is not killed; the handoff returns a failure if it cannot acquire the GPU
within its wait budget. Model weights, context and quantization are untouched.
`--engine-exe` is optional; it starts/stops only a private engine on 8829 and refuses
an occupied port. It copies the binary/shaders into the evidence directory so it
cannot modify the running world. GPU and private-engine processes exit after the
batch; next inference uses the existing lazy reload mechanism.

To resume, repeat the exact run command and output directory with `--resume`.
Source/configuration differences are refused. A completed GPU checkpoint is reused
only if input, output, binary and shader hashes match; mathematical checks run again.
Partial native attempts remain in their original directories. Completed native
captures are reused only when their hashes and current engine/shaders match.
A source change needs a fresh directory; old failures and receipts stay intact.

## Artifacts and their meaning

- `identity.json`, `case-manifest.json`: source identities, deterministic candidates,
  normalized domain, 65 training heights per recipe and separate off-grid/scale checks.
- `measurements.json`, `gpu-raw.json`: scalar measurements and actual GPU areas/forces.
  GPU physics is compared against exact uploaded f32 coordinates promoted to f64.
- `ap01_*-table.json`: piecewise-linear reactions with exactly integrated energy;
  out-of-domain evaluation refuses. Each geometry has its own table; this is not
  generalization to unknown geometry. Physical scaling is limited to the tested law.
- `composite-table.json`, `assembly-comparison.json`: versioned child dependencies,
  shared-port balance and reuse of the same frozen composite in two surroundings.
  Composite rescaling is refused pending its own qualification.
- `function-cards.json`: compact measured functions, unsupported behavior and a next
  research question. This is a research archive, not an admitted gameplay catalog.
- `native-view.json` and `native*/ap01_*-native.png`: existing renderer captures plus
  native energy/force/state and executable/shader hashes; no replacement renderer.
- `receipt.json`: local numerical result, fixed limits, CPU scalar timings, GPU
  identity and resource snapshots. `failure.json` retains unsuccessful/interrupted
  runs. `check` recomputes physical checks instead of trusting a worker's PASS.

`PREREGISTRATION.md` fixes the physics scope, budgets and falsifiers. `verify.py`
is an independent mathematical formulation, not an independent release authority.
The controller/reviewer must still admit any runtime use. A worker with OS write
access can edit code; this package is not an operating-system security boundary.

## AP02: two independent ports and finite-area coupling (2026-10-14)

`core2.py`, `verify2.py`, `faa_port.py`, `runner2.py`, `test_workflow2.py` and
`PREREGISTRATION2.md` implement the next §11.20.10 direction: a second
independent port and a qualified finite-area attachment.

Two-port piece: the same asymmetric rim now carries two interior nodes, each on
its own z-rail, joined through one shared 8-triangle surface. The response is
(h_p,h_q) -> (R_p,R_q) and the ports are cross-coupled: the measured cross
stiffness dR_p/dh_q is 27-35% of the direct stiffness at every sampled state
(Hessian symmetric to 1e-11, detailed vs Heron agreement <=1.6e-7 normalized).
An independent Heron's-formula reference (3-D edge lengths) and a
conjugate-gradient minimizer check the detailed solve and the two-piece
equilibria. The quadratic reduced model is admitted only inside its measured
domain (0.02 normalized; 0.15 and 0.03 were measured against the frozen 5e-3
budget and rejected) and its equilibrium agrees with the detailed solve within
2e-4 m.

Finite-area coupling: two rigid carriers, each exactly welded to one AP01 fan
node, joined by one patch admitted through the reference module's own gates
(rank 6/6, couple stiffness ~25 N*m/rad, provenance-checked). A prescribed port
displacement transfers force to the far carrier (>=0.25*Kbar*delta) and a
prescribed port rotation transfers moment (>=0.25*lambda_min*phi) — the scalar
rail coupon had no moment path. Cross-joint wrench balance and carrier balance
hold to 1e-12 relative; the loaded-port Newton solve uses the reference
module's analytic wrenches and converges to ~1e-13.

Run: `& $apPython -B -m tools.artificial_proteins.runner2 run --out .tmp/ap02-cpu-N`
then `check --out` the same directory; `--resume` re-verifies without re-running.
CPU-only; no GPU batch, native capture or render binding is claimed here. The
far carrier is a rigid bolted fixture, not a second compliant piece; carriers
are massless quasistatic bodies. `check2` recomputes all physics independently.

## Next engineering direction

Repair/qualify render-state correspondence before live construction admission
(the AP01 rendered-byte hash is still zero), then replace the bolted far carrier
with a second qualified compliant piece so both ports carry measured responses.
Retain the detailed reference when a table becomes too large; only then compare
a small Noether model with the same accuracy and complete-cost requirements.
Prioritize composition, state ownership and reconstruction before generating a
large catalog.

General arbitrary geometry, learned multiport responses, saved mutable protein
instances, inspector/picking controls, gameplay fabrication and live dynamics remain
future work. This prototype changes none of the existing native world APIs.
