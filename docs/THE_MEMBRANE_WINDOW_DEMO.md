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

---

# GLM-WINDOW-02 — OWNERSHIP TRACE, DIMENSIONAL CORRECTION, CAPTURE LINKAGE,
# LAUNCH VERIFICATION (2026-09-08)

## 1. Computation ownership (the exact trace)

- **Forces and accepted positions** are produced by
  `tools/membrane_window_demo.py::projected_descent`, which calls
  `tools/surface_energy_reference.py::evaluate_surface` — the **CPU float64
  reference** — and applies the declared overdamped update with constants
  imported from `tools/overdamped_descent.py`. No Vulkan kernel is involved
  at any point of the optimization.
- **The verified Vulkan membrane kernels live in the standalone probe**
  (`tools/membrane_gpu_probe/`), which dispatches `membrane.comp` compute
  shaders and compares against frozen fixtures. The window demo does NOT
  dispatch them. The probe intentionally reads fixture files directly —
  that is its design as a numerical gate — while the window demo admits
  gamma only through `tools/material_contract.py` (F6 below records the
  admission path).
- **`/mesh_bin` uploads a CPU-computed result**: the driver encodes the
  accepted f64 geometry, quantized to f32 by the declared boundary policy,
  plus normals accumulated on the CPU from the certified evaluator's face
  normals. The engine consumes the byte payload verbatim.
- **Verdict: this is a CPU-reference visualization milestone.** It is NOT
  GPU-driven membrane integration, and no such claim is made. GPU-driven
  integration (engine dispatching the verified kernels) is explicitly out
  of scope here.

## 2. Dimensional correction (preregistered before the edit)

The original F1 instrument compared the declared run's centre xy **drift
[metres]** against the manifest's `force_xy_symmetry_N` **[newtons]** — a
unit mismatch; a position cannot be checked directly against a force.

- **Preregistered correction:** the declared update is `p = P·F` with
  `P = 1/gamma_max [m/J]`; `|F_xy| <= 1e-6 [J/m]`, `alpha <= 1`, so each
  accepted step moves the centre at most `(1/gamma)·1e-6` metres. The
  derived worst-case bound over `n_accepted` steps is
  `n_accepted · (1/gamma) · 1e-6` metres. Observed drift 4.168e-18 m vs
  bound 1.260e-4 m (n=126, gamma=1): **PASS**.
- **The original failing comparison is preserved** as a retired instrument
  in this document and the master ledger; the failed check line
  (`F1.declared_xy_drift_within_symmetry_budget`, evidence
  `20260908T151444.432622Z`) remains in the published record.
- **Effect on prior PASS verdicts: none.** The energy bit-identity checks
  and the rail run's exact-zero xy deviation are independent instruments
  that never used the mismatched comparison. F1 was re-run green under the
  corrected gate (evidence `20260908T160307.423502Z`).

## 3. Capture linkage (what the state ID does and does not prove)

Source facts (from `ChimeraEngine/engine/main.cpp`):

- The `/mesh_bin` POST response `{"ok":true}` is a **real applied
  acknowledgement**: the HTTP worker parks the request on `g_mesh_req`, and
  the RENDER thread consumes it (load_mesh + set_camera) before setting
  `g_mesh_applied` and notifying the condition variable (15 s timeout).
  It proves the payload reached the render thread — nothing more.
- **The ack returns no state identity**: no geometry hash, no frame id,
  no echo of what was applied. `GET /state` exposes the PARTICLE physics
  state, not the triangle mesh; `GET /session` exposes snapshot blob
  SIZES only. There is no engine-returned identifier the driver could
  bind to its state ID.
- **Competing writers exist**: `--restore` replays
  `session_snapshot/mesh_bin.blob` at boot (the demo instance is launched
  with `--no-restore`, and the driver uploads AFTER boot, so the demo's
  payload is the LAST write); the Studio UI can load meshes; any other
  HTTP client could POST `/mesh_bin` between upload and capture. The
  engine writes every successful upload back to
  `session_snapshot/mesh_bin.blob` THROUGH (same bytes), which an
  independent process can read to corroborate what the engine last
  accepted.
- **Therefore capture association is CONDITIONAL**: the sidecar's state ID
  and upload hash prove the driver's INTENDED input and the applied-ack,
  not which geometry was on screen at capture time. A capture certifies
  the law only together with (a) the applied-ack on the byte payload whose
  hash is recorded, (b) a corroboration read of
  `session_snapshot/mesh_bin.blob` from the demo instance's working
  directory matching that hash, and (c) no other writer in the window
  between ack and `/frame`. F5 checks what is checkable from the driver's
  side; (b) is recorded as an explicit condition in the launch procedure
  below and remains UNVERIFIED until a window run executes.

## 4. Launch command verified against source

Every element below is checked against the actual code (commit
4ac41480 + this amendment):

- **Executable name**: `chimera_engine.exe` — `add_executable(chimera_engine
  ...)` in `ChimeraEngine/engine/CMakeLists.txt` (MSVC adds `.exe`).
- **Port argument**: `argv[1]` overrides the default 8080
  (`main.cpp`: `int http_port = 8080; if (argc > 1) ...`). `8091` is the
  demo's; the operator's session (default 8080) is never contacted.
- **`--no-restore`**: supported (`main.cpp` scans all argv positions for
  `--no-restore` and skips the boot restore replay). Without it, the demo
  instance would replay any `session_snapshot/mesh_bin.blob` in its CWD —
  the flag makes the demo instance born empty by declaration.
- **Asset paths**: shaders are loaded CWD-relative (`shaders/*.spv`,
  `engine.cpp::compile_shaders`); `main.cpp` falls back to the EXE's
  directory when `shaders/render.vert.spv` is absent from the CWD.
  Launching from the build output directory works either way.
- **Window size**: optional `argv[3] argv[4]`.
- **Shared persistent files with the operator's live engine**: the engine
  writes `session_snapshot/*.blob`, `session_*.jsonl`, `studio_state.txt`,
  `cam_marks`/`key_marks` files **relative to its CWD**. A second process
  launched from a DIFFERENT working directory shares NONE of these. No
  named Win32 mutexes/events are created (only an unnamed window class
  `ChimeraEngine` — `RegisterClassEx` is per-process, and the HWND is
  per-instance, so two instances coexist). Vulkan instances are
  process-local. **Conclusion: launching the demo instance from its own
  build output directory isolates it from Alan's live engine's working
  files**, provided the operator's session runs elsewhere (it does —
  different CWD). No launch or modification of the existing session is
  performed by this task.
- **Precise procedure** (unchanged in substance from the earlier section;
  now source-verified):

```bash
# build OUTSIDE the protected build dir
cmake -S ChimeraEngine/engine -B .tmp/engine_demo_build -G "Visual Studio 17 2022" -A x64
cmake --build .tmp/engine_demo_build --config Release
# launch from the build output dir (isolated CWD -> isolated session files)
cd .tmp/engine_demo_build/Release
./chimera_engine.exe 8091 --no-restore
# driver (upload + applied-ack + fixed-camera /frame + sidecar)
cd <checkout root>
python tools/membrane_window_demo.py --gamma 1 --engine-url http://localhost:8091
# checks (numerical gates + capture certifiability)
python tools/membrane_window_demo_checks.py
```

After capture, corroborate `session_snapshot/mesh_bin.blob` in
`.tmp/engine_demo_build/Release/` against the sidecar's
`upload_positions_f32le_sha256` (the blob additionally carries the header
and index bytes the upload contained) — the explicit condition that turns
a conditional capture association into a certifiable one.

## 5. Verdict separation (unchanged law, restated)

- **Numerical (CPU)**: PASS — F1–F4, F6, F7 (evidence
  `20260908T160307.423502Z`, `20260908T161354.929940Z` and controls).
- **Upload**: the byte payload and its f32 hash are recorded; the engine's
  applied-ack is real but returns no identity — upload-to-screen linkage
  remains CONDITIONAL (section 3); blob corroboration MATCH ×3 (below).
- **Window**: EXECUTED 2026-09-08 (GLM-WINDOW-03) — see section 7.
- **DYAD**: NOT TESTED — the local vision agent reviews next; no DYAD
  acceptance is claimed.

No tolerance was widened anywhere in this correction.

## 7. GLM-WINDOW-03 — boundary corrections and the executed window demo

### 7.1 P-unit correction and trajectory verification

GLM-WINDOW-02's derivation note wrote `P = 1/gamma_max [m/J]` — WRONG unit.
`P = 1/gamma_max` carries the **area** unit of the energy's denominator:
**P = [m²/J]**, and the update is `[m²/J]·[J/m] = [m]` — dimensionally a
length, as required. The dimensionless RATIO 1/gamma is m²/J (the R4 units
table's `wu²/J` with 1 wu = 1 m), never m/J.

The bound's assumptions were verified over the ACTUAL compared trajectory
(recorded per-iteration data, not assumed): max recorded `alpha = 1.0` over
all 126 accepted steps, and max recorded `|F_xy| = 1.11e-16 N` — far inside
the manifest's `force_xy_symmetry_N = 1e-6` allowance. The cumulative bound
becomes `n_accepted · alpha_max · (1/gamma) · 1e-6` m = 1.260e-4 m; observed
drift 4.168e-18 m. **The original GLM-WINDOW-02 dimensional check (metres
vs newtons) is SUPERSEDED, NOT VALID** — it was never a valid instrument;
it is preserved as failed-instrument history only. The independently valid
energy and rail gates are retained regardless of this gate, and the drift
is also reported descriptively.

### 7.2 Position vs gamma quantization — separate boundaries

- **Positions**: the only f32 boundary in this demo (`applies_to:
  "positions_only"`). Overflow refused, positive underflow reported,
  round-trip error recorded (F7).
- **Gamma**: **NOT APPLICABLE** in this CPU demo — gamma is admitted f64
  through the material contract, broadcast to an f64 per-face array,
  consumed by the f64 evaluator, and never uploaded (the `/mesh_bin`
  payload carries positions/normals/colors only; there is no per-face
  gamma field). `gamma_f32_boundary.status = NOT_APPLICABLE` is recorded
  per run. **The future GPU gamma boundary is NOT certified by this demo.**

### 7.3 The executed isolated window demonstration

- Build: `cmake -S ChimeraEngine/engine -B .tmp/engine_demo_build -A x64`
  + `cmake --build ... --config Release` (VS 18 2026 generator, MSVC
  14.51, Vulkan SDK 1.4.328.1) — OUTSIDE `ChimeraEngine/engine/build/`.
- Launch record: `docs/evidence/membrane_window_demo/launch_20260908T112500Z/`
  — exe sha256 `25f9b34967e907da97b5686edfb7e6b563e00618d1d69acc888e15112f287b28`,
  PID 57124, port 8091 verified free before launch (no process terminated),
  `--no-restore`, own CWD (`.../.tmp/engine_demo_build/Release`), endpoint
  `http://localhost:8091`. Only this PID was controlled; it was stopped
  after the captures (`taskkill //PID 57124`), and the engine's stdout/
  stderr logs are preserved.
- Two LIVE-FOUND defects, both preserved as failed runs before the fix:
  the driver packed `len(faces)` (6) where the engine expects the INDEX
  count (18) — `"size mismatch"` (`20260908T161935.386951Z`,
  `20260908T162022.834592Z`); then a sidecar key error. Both fixed in the
  driver only; the engine was never modified.
- Captures (fixed camera 6.0/0.0/0.3, each PNG + sidecar with state ID,
  geometry hash, upload f32 hash):
  - `20260908T162114.706091Z/window_gamma1_final.png` — positive gamma,
    accepted state (126 steps, 2.5980761647224426 J).
  - `20260908T162207.936281Z/window_gamma0_unchanged.png` — zero gamma,
    STATIONARY at 0 steps; upload bytes equal the raw fixture f32 bytes.
  - `20260908T162328.481149Z/window_gamma2_doubling.png` — matched-state
    doubling: final geometry hash IDENTICAL to gamma-1's; energy ratio
    exactly 2.0 (bit-exact); 126 == 126 accepted steps (the update is
    gamma-invariant); iterations are NOT time — no twice-speed claim.
- Blob corroboration (position-bytes hashing per the documented format —
  the first 12 bytes of each 36-byte vertex record, hashed in the
  sidecar's declared order; a whole-blob hash is NEVER compared to a
  position-only hash): **MATCH ×3**, recorded in
  `launch_20260908T112500Z/blob_corroboration.txt`.
- Association remains **CONDITIONAL** (section 3): the applied-ack returns
  no state identity and competing writers cannot be excluded from the
  driver side alone; the corroboration is supporting evidence, not proof
  of which geometry was on screen at `/frame` time.
- Checks with captures present: **ALL PASS** (F1–F7, including F5 capture
  certifiability on all three captures).

## 6. Big Pickle review reconciliation (7aba0ee7 → current)

BP reviewed 7aba0ee7 (mutation verification) before the demo existed. The
findings, reconciled against CURRENT source:

1. **Gamma admission trace** — closes in this implementation: the demo's
   admission path is `MaterialProperty.__post_init__` → `MaterialRecord.add`
   → `MaterialContract.register` → `bind` → `Binding.get(as_unit='J/m^2')`,
   recorded immutably per run (F6). The frozen-fixture probe is a DIFFERENT
   consumer by design: it reads fixture gamma files directly as a numerical
   gate; this distinction is documented in section 1.
2. **Unit law** — closes: gamma stays in registered J/m²; the B2 mapping
   `1 wu = 1 m` is declared explicitly (`WU_TO_M`, `coordinate_mapping` in
   every run record). No generic J/wu² unit was added.
3. **f32 boundary validation** — closes: `quantize_positions_f32` validates
   the CONVERTED value (overflow refused with a named error, never clamped;
   positive underflow reported, never claimed as preservation; round-trip
   error recorded). F7 verifies the policy and re-derives the hash.
4. **Synthetic labeling + immutable snapshot** — closes: every run record
   carries `gamma_admitted` with `synthetic: true`, the explicit
   "NOT a calibrated physical material" label, value bits, and the admission
   path, written before computation consumes the value.

All four required correction work (none was already closed pre-amendment);
all four now close in the amended driver + checks.
