# THE MEMBRANE WINDOW DEMO — LUNA-WINDOW-01

The first material-driven membrane demonstration in the real Chimera engine
window. Registered under the Rule-0 membrane preregistered before
implementation (also recorded in `docs/THE_MASTER_LIST.md`).

## Preregistration

- **STATEMENT:** accepted iterations of the declared overdamped update
  satisfy the existing energy/geometry gates, and the renderer consumes
  that accepted geometry (no second visual pose).
- **PREDICTION:** positive gamma visibly reduces the B2 centre bump; zero
  gamma leaves geometry bit-unchanged; fixed-state gamma doubling doubles
  energy and force within the existing bounds.
- **FALSIFIER:** any accepted-state gate breach, separate visual geometry,
  failed zero/doubling control, or a capture whose record lacks a matching
  state ID.

## Derivation: the rail constraint

B2's centre vertex (index 6) is constrained to the **vertical rail** through
its initial position: x,y held at their initial values, z free. Rim vertices
0..5 are pinned exactly (as `run_descent` does).

The declared update is `p = P·F` with `P = 1/gamma_max`. On the constrained
subspace the admissible directions at the centre are `(0,0,dz)`; because the
constraint subspace is a **linear subspace**, the restricted gradient is
`(F·e_z)·e_z` — the x/y force components are orthogonal to it. So the
projected direction is `p_rail = P·F_cz·e_z` at the centre, `0` at the rim.

**All three force components are computed and recorded at every iteration
BEFORE projection** (the requirement). Only the *direction* is projected.
The acceptance rule is exactly the declared one:

- (a) Armijo: `U(x+) <= U(x) - c1·alpha·<F, p_rail>` with `c1 = ARMIJO_C1`;
  `<F, p_rail> = F_cz·p_rail_z` is the exact directional derivative along
  the rail;
- (b) geometry validity via `evaluate_surface`'s own named refusals,

with the same backtracking (`BACKTRACK_FACTOR`, `MAX_BACKTRACKS`), the same
step-scale guard (`GUARD_FRAC` over `min_edge`), the same stationarity scale
(`RESIDUAL_TOL_FRAC · mean_edge`, applied to the single free DOF), the same
stagnation scale (`STAGNATION_FRAC`), and the same five named terminal
states. Every constant is **imported** from `tools/overdamped_descent.py`;
none is re-declared here.

**Equivalence control:** B2's fixture is 6-fold symmetric, so the centre's
x/y force components are exactly zero at the fixture geometry (manifest
gamma1 `centre_force_N == [0, 0, -0.42857...]`). The projected run must
therefore match `run_descent(pos, faces, gamma, fixed_vertices=[0..5])` in
status, accepted-step count, and **bit-identical energies** —
`membrane_window_demo_checks.py` F1 falsifies the projection instrument if
that identity breaks.

**Resolved falsifier (2026-09-08, kept as correction history):** strict
*geometry-byte* identity between the two runs is FALSE at f64 noise: the f32
hexagon is symmetric only to ~1e-17, so the unconstrained declared run's
direction carries O(1e-17) xy components and its free centre drifts in xy by
~4e-18 while the rail run cannot. Energies remain bit-identical every
iteration. The checks therefore assert (i) per-iteration energy bit-identity,
(ii) the declared run's xy drift within the manifest's own preregistered
symmetry budget (`force_xy_symmetry_N = 1e-6`), and (iii) the rail run's xy
deviation exactly zero. No tolerance was widened; the instrument was
corrected to measure the right thing.

## gamma = 0

Forces are exactly zero (the reference's own D2 law); the run is STATIONARY
at iteration 0 and the geometry is bit-unchanged from the fixture upload.
Recorded as `zero_gamma_control` inside every run's `result.json` and
re-derived independently by F2.

## gamma doubling

At the FIXED accepted state, `U(2g) = 2·U(g)` and `F(2g) = 2·F(g)`
componentwise within the fixture's preregistered bounds (energy allowance
`9.36375259151094e-07 J`, force allowance `1e-6 N`). Doubling is a statement
about energy and force at fixed geometry; it does **not** imply twice-speed
relaxation. **Iterations are not time**: there is no `dt` anywhere in the
driver, and the accepted result is an optimization state, not inertial
dynamics.

## The material contract

gamma enters ONLY through the validated material contract
(`tools/material_contract.py`): a `MaterialProperty` named `gamma`, unit
`J/m^2` (family `energy_area`), nonnegative, with source locator, conditions,
and provenance. Anything else is refused with a named refusal at the door —
nothing is defaulted.

## State IDs

Every iteration and every capture carries a deterministic state ID:
`sha256` over `{commit, fixture, gamma_bits, iteration, geometry_sha256_f64le,
energy_bits}`. The same inputs always produce the same ID; the ID binds the
numerical state to the task's source commit. A capture without a matching
state record cannot certify the law — F5 refuses it.

## Rendering consumes the accepted geometry

The driver encodes the ACCEPTED positions (f32 quantization for the GPU
vertex format only, recorded as `upload_positions_f32le_sha256`) with
normals accumulated from the certified evaluator's current-geometry face
normals and a fixed neutral color — **no second visual law** — and uploads
via `POST /mesh_bin` to a separately launched engine instance, then `GET`s
`/frame` once with a FIXED camera (radius 6.0, theta 0.0, phi 0.3 — recorded
in the sidecar). Each capture writes `PNG + sidecar JSON` carrying the
final accepted iteration's state ID, energy, geometry hash, and upload hash.

The engine session this driver starts is the operator's to stop; the driver
never starts, stops, or replaces any engine unless asked (`--engine-url` is
opt-in). Default mode is numerical-only. The ordinary engine path is
unchanged when the demo is disabled — the demo adds no engine code at all;
it drives the EXISTING `/mesh_bin` + `/camera` + `/frame` HTTP surface.

## Exact launch procedure (separate demo instance)

```bash
# 1. Build the engine OUTSIDE the protected build directory (scratch):
cmake -S ChimeraEngine/engine -B .tmp/engine_demo_build \
      -G "Visual Studio 17 2022" -A x64
cmake --build .tmp/engine_demo_build --config Release

# 2. Launch a SEPARATE demo instance on its own port (8091), no state
#    restore, from the build output directory (shaders/ must be adjacent):
cd .tmp/engine_demo_build/Release
./chimera_engine.exe 8091 --no-restore
#    (this window is the operator's to close; it is NOT Alan's session)

# 3. Run the demo (numerical + upload + fixed-camera capture):
cd <checkout root>
python tools/membrane_window_demo.py --gamma 1 --engine-url http://localhost:8091

# 4. Verify the recorded evidence (numerical gates + capture certifiability):
python tools/membrane_window_demo_checks.py
```

Port 8091 is the demo's; the operator's engine (if any) is never contacted.
The engine HTTP API is localhost-bound; it is not exposed publicly.

## Status

- CPU/numerical verification: **PASS** (all F1–F4 checks; evidence
  `docs/evidence/membrane_window_demo/20260908T151444.432622Z/`, gamma 1;
  controls recorded for gamma 0 and gamma 2).
- GPU probe regression: unaffected (no probe source changed in this task).
- Window capture: **NOT TESTED** — requires the operator to build and launch
  the separate demo instance (commands above). Never labelled PASS without
  an executed capture with a matching state ID.
- DYAD: **NOT TESTED**.
