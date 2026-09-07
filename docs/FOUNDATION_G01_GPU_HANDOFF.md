# FOUNDATION_G01_GPU_HANDOFF — proposal, not implementation

Written by the G01 packet (2026-09-06 session, base
e0ea5a5635ef4bac2d1a2b46a604c04d68e9c8d7). Per the packet's isolation rule
this file IMPLEMENTS NOTHING: it is the layout + seam document the later
integrator builds against. The certified reference is
`tools/surface_energy_reference.py` (8/8); the certified contract is
`tools/material_contract.py` (10/10). Every number below is quoted from
those files' laws, not re-derived here.

**Status of the CPU implementation (G01-R correction):** the CPU numpy
implementation is the NUMERICAL REFERENCE — the certified statement of the
laws and the source of expected values. It is NOT a guaranteed bit-exact
oracle for any GPU transcription: float ordering, FMA contraction, and
precision tier all differ on device. Agreement between a GPU pass and this
reference is defined by the PROPOSED tolerances of §2.5, never by bit
equality.

## 1. Buffer layouts and units

### Storage (per frame, SSBO, std430)

| Buffer | Layout | Unit |
|---|---|---|
| `positions` | `vec3 pos[nV]` (stride 16 B) | world units (wu) |
| `faces` | `uvec3 idx[nF]` | vertex indices |
| `gamma` | `float gamma[nF]` | energy per unit area (E/area) |
| `face_forces` | `vec3 F_corner[3*nF]` face-major (f0c0,f0c1,f0c2,f1c0,...) | gamma × wu |
| `vertex_forces` | `vec3 F_vertex[nV]` | gamma × wu |
| `adj_offsets` | `uint offsets[nV+1]` (CSR) | — |
| `adj_corner_idx` | `uint corner_idx[3*nF]`, vertex-major corner rows | face*3+slot |
| `valid_mask` | `uint valid[nF]` | 1 = nondegenerate, 0 = masked |

Scalar `gamma` per face; vectors only where stated. **`corner_idx` is the
exact array the reference's `build_vertex_corner_adjacency` produces** — the
gather pass consumes it with `offsets` and MUST reduce rows in that order
(vertex-major), not face-major rows (the G01 gather bug is exactly this
swap, and F8 is its detector — see §4).

### Units conversion seam

The reference computes forces in units of `gamma × wu`. The engine's other
force sources (hinge pose, CA springs, frost) are also per-frame force
accumulations. The conversion to the integrator's units happens at ONE seam:
the accumulation into the shared force buffer, with a single documented
scale `k_energy_to_force`. Nothing in the kernel converts units internally.

## 2. The two passes

**Pass 1 — face forces.** One workgroup per face (or flat 3*nF threads).
Reads `positions[idx]`, `gamma[f]`; computes
`n = normalize(cross(b-a, c-a))`; writes face-corner forces
`-(gamma) * grad_a|b|c` with
`grad_a A = cross(b-c, n)/2` (cyclic), face-major layout.
Validity mask: `|cross|` exactly 0 → COLLAPSED (mask 0, no force);
`|cross| <= 64*e*max_edge^2` → NEAR_DEGENERATE (mask 0, no force, error
channel if the engine carries one). **Unsigned current area, current
normal** — the surface-energy law; do NOT port the rest-area law's signed
normal from ca_triangle.area_grads (different physics, different law).

**Pass 2 — vertex gather.** For vertex v: sum `face_forces[corner_idx[v]]`
over `offsets[v]..offsets[v+1)`. Determinism requirement: fixed iteration
order per vertex (the CSR order is the declared deterministic tier —
segments sorted by (face, slot) ascending). Face-major summation is NOT a
deterministic tier for this buffer (different reduction order → different
last-ulp results across runs; the house checks F8's 512*e allowance covers
algebra, not run-to-run nondeterminism).

Barrier between passes: `vkCmdPipelineBarrier` with
`COMPUTE→COMPUTE`, `SHADER_WRITE → SHADER_READ` on `face_forces` (same
discipline as the existing hinge pipeline at engine.cpp:7038).

## 2.5 Proposed GPU-vs-reference force tolerances (PROPOSAL — unverified on any device)

Derived from three measured quantities and the executing interpreter's
declared float precision — chosen by derivation, not to obtain a pass, and
NOT yet validated on any GPU:

| Quantity | Value | Source |
|---|---|---|
| ε_f64 | 2.220446049250313e-16 | `sys.float_info.epsilon`, executing interpreter |
| ε_f32 | 1.1920928955078125e-07 | numpy float32 eps |
| S_max | 3.88 γ·wu | worst per-vertex force magnitude across the battery's fixtures (measured) |
| d_max | 6 corners/vertex | battery fixtures' max adjacency degree → accumulation depth 3·d = 18 float adds per force component |

Derived single-pass error bounds (worst-case aligned rounding, one gather):

- **f64 accumulation:** relative ≤ 3·d·ε_f64 ≈ **4.0e-15**; absolute ≤ 4.0e-15 · S_max ≈ **1.6e-14 γ·wu**
- **f32 accumulation:** relative ≤ 3·d·ε_f32 ≈ **2.1e-06**; absolute ≤ 2.1e-06 · S_max ≈ **8.3e-06 γ·wu**

PROPOSED acceptance for the GPU gather vs this reference, **per-vertex,
per-component**:

- **f64 tier:** max |ΔF| ≤ 1.6e-14 γ·wu absolute AND ≤ 4.0e-15 relative to
  the vertex force magnitude. Near-zero handling: where |F| is below the
  absolute term, the absolute bound governs (relative is undefined there).
- **f32 tier:** max |ΔF| ≤ 8.3e-06 γ·wu absolute AND ≤ 2.1e-06 relative.
- The integrator MUST declare its precision tier; an undeclared tier is a
  failed gate, not a default.

These are PROPOSALS: the algebraic worst case for one pass at declared
depth and precision, with zero device-measured headroom. The integrator
validates them against its own F8-equivalent dual-path check (§4) before
any engine integration, and records the measured margins alongside.

## 3. Mapping to the radial modifier (LightEngine/modifier.py)

The scalar radial modifier is `w(r) = 1 - smooth(r/r_max)` — a scalar
multiplier on a chosen per-vertex quantity. Mapping:

| Surface-energy quantity | Scalar-multiplier sufficient? |
|---|---|
| per-face γ scaling (paint γ spatially) | **YES** — γ_t ← γ_t · w(r): the law stays conservative per-face, energy weights change only |
| global force magnitude | **NO** — scaling F by (1-w) AFTER the gather breaks ΣF=0 (a uniform scale by k preserves it, a spatially-varying one does not) |
| per-vertex force gating (mask) | **YES** — but gating a VERTEX force is not conservative even when each face force was; a masked vertex force means real energy input at the mask seam |

Where a scalar multiplier is insufficient, the extension must be stated as
a new law with its own falsifier — the natural one is spatially-varying γ
(P-6's equal-area machinery already detects when "same area, different
energy" is misreported), NOT a post-hoc force edit.

## 4. The seam between face and vertex (the bug the battery caught)

The one implementation trap this packet can already name from evidence:
**the gather order must match the offsets**. The reference shipped with
face-major rows reduced by vertex-major offsets — O(1) wrong forces, total
force preserved (so balance checks pass), single-triangle meshes blind to
it. F1 (FD vs analytic) and F8 (gather vs independent scatter) caught it
independently. The GPU gather must either consume the reference's CSR
exactly, or ship with its own F8-equivalent check before integration.

**Per-vertex comparison requirement (the F8 lesson, made law for this
handoff): every acceptance test above is per-vertex, per-component.
Total-force balance (ΣF = 0) is necessary but DEMONSTRABLY insufficient —
the gather bug shipped perfect balance while every per-vertex force was
O(1) wrong. No aggregate (total force, total energy, COM) may stand in for
a per-vertex check anywhere in this document's gates.**

## 5. Binding material state to a membrane (task 18)

The contract's law: a `MaterialRecord` is a SHARED store of sourced
properties; a `Binding` references it by name and dereferences at call
time — mutations propagate to every geometry (P-8h, certified). Shaping
one material into different objects:

```
contract.register(build_white_oak_record())          # the sourced store
bind(contract, "white_oak", "membrane:creature")     # the bear's shell
bind(contract, "white_oak", "membrane:branch")       # a prop from the same wood
```

Separation of concerns (each a different field with a different source):

| Quantity | Where it lives | Source class |
|---|---|---|
| material stiffness (E_L, ratios) | the record | researched (Handbook tables) |
| failure strength (MOR, tens_perp, shear_par) | the record | researched (same tables) |
| geometry-dependent load capacity | NOT in the record — computed from geometry + stiffness at load time (a beam's capacity is its geometry, not its wood) | derived-at-use |
| interface adhesion (γ) | per-face attribute, NOT a material property — two surfaces meet at a face, one material doesn't own it | law input, spatially paintable |

Consequences, each already demonstrated by a certified check:

- **wood**: white_oak carries E_L, ratios, MOR, SG. It refuses G_LT
  absolutes and Poisson's ratios BY NAME (P-8b) — the Handbook doesn't
  publish them; no default is invented.
- **a named alloy, unsupported example**: 6061-T6 aluminum has NO table in
  the ingested sources (matter_data has no metals store). The contract's
  verdict on `get("alu_6061_t6", "E")` is `missing_input` naming the
  material — the capability limitation, not a placeholder value. When a
  source is ingested (e.g. MMPDS), the record gains RESEARCHED entries and
  the refusal disappears. Nothing else changes.
- **liquid surface**: a liquid's interfacial energy γ is the surface-energy
  law's OWN input (per-face `gamma` buffer), not a stiffness — the law of
  record is Young-Laplace convergence, certified by F5 (2γ/R, 8 faces →
  20480 faces, monotone, ≤1% at level 4). A water membrane binds NO
  stiffness record at all; the refusal for its E is correct physics, not a
  gap: liquids have no shear modulus.
- **knee composition**: a knee is a BINDING GRAPH, not a material — bone
  record on the membrane regions adjacent to the joint, cartilage record
  (unsupported in sources today → named refusal) on the contact faces,
  γ on the interface faces. The rig's existing joint anchor/axis state
  (28-joint pack) indexes which membrane region gets which binding; the
  load capacity is computed at the joint from geometry + the bound
  stiffness, never stored as a property.

## 6. Proposed verification ladder (task 19 — proposal ONLY)

**No captures were manufactured. No visual or human PASS is recorded or
claimed in this packet.** The integrator owns the run. The ladder is
ordered: **Tier A (camera-independent numerical) gates Tier B (pixel/DYAD)
— a pixel test never substitutes for a numerical one.**

### 6.0 Integrator assumptions (G01-R2 correction — declared BEFORE the tests)

Three corrections ASTRA's review imposed, stated here as the assumptions
the ladder's expectations silently depended on:

1. **No rest shape.** Constant-γ surface energy `U = Σ γ·A(current)` has NO
   remembered rest configuration — it depends only on current geometry.
   The energy field cannot promise restoration to the imported pose, and
   no test below claims it. (The earlier draft's case 3 did; that was a
   false promise and is rewritten.)
2. **Boundary-only forces are a PLANAR-PATCH result.** Interior vertices of
   a constant-γ PLANAR region feel zero net force (the flat case's
   gradient vanishes in the interior). On CURVED constant-γ regions,
   interior forces are generically nonzero — that is the physics (the
   surface shrinks; F5's 2γ/R is the aggregate signature). Case 2's
   expectation is restated with the planar assumption declared.
3. **Dynamics are integrator-dependent.** "Monotone area reduction" and
   "motion aligned with the instantaneous force" are NOT general guarantees
   of inertial dynamics — an underdamped system overshoots, oscillates, and
   can transiently gain area. They ARE the expected behavior of the
   declared quasi-static scheme below. The ladder claims nothing for
   undeclared schemes.

**The declared scheme for cases A2/2/3 (and the only scheme these
expectations are valid for):** quasi-static, overdamped update
`x⁺ = x + s·m·(−∇U(x))` — no inertia, no velocity state, no other force
sources (hinge/CA/frost disabled), γ held fixed at its painted values,
starting from the stated initial condition per case.

**G01-R3 correction (D7) — the update is a MOBILITY law, and descent comes
from an ACCEPTANCE TEST, not from the displacement bound.** Force is not
velocity: `Δt·F` is meaningless until a mobility maps force to motion. The
concrete law (derived, units carried, implemented and certified in
`tools/overdamped_descent.py`):

- **Preconditioner** `P = 1/γ_max` with units **wu²/J** (so `P·F` is a
  length). **G01-R4 correction (2026-09-07, adopting ASTRA's audit):** the
  R3 text here said `m = min_edge²/γ_max` and called it wu²/J — that
  expression is actually **wu⁴/J** (the error was numerically masked at
  unit scale; the R3 batteries could not see it). The dimensionally exact
  inverse energy density is `1/γ_max`; γ_max = 0 is handled before any
  division (γ ≡ 0 ⇒ F ≡ 0 ⇒ stationary with zero steps). The step
  parameter α is dimensionless (`x⁺ = x + α·P·F`); iterations are
  ITERATIONS, never elapsed simulation time. Any constant positive P
  reaches the same stationary point (P only rescales the
  parameterization); the residual/stagnation/step-limit/no-descent/
  invalid five-state stopping taxonomy of R4 replaces R3's single
  `converged`, and stationarity is assessed on FREE degrees of freedom
  only, with pin reaction forces reported separately.
- **Acceptance (verified every step, never assumed):** a trial
  `x⁺ = x + s·m·F(x)` is accepted iff (a) Armijo sufficient decrease
  `U(x⁺) ≤ U(x) − c₁·s·⟨F, m·F⟩`, c₁ = 10⁻⁴, AND (b) the trial geometry is
  VALID under the reference's own named-refusal floor (64·e·max_edge²).
  Rejected trials backtrack s ← s/2 (budget 50); exhaustion is the named
  refusal `no_descent_step` with geometry returned unchanged.
- **The old bound is DEMOTED:** `Δt·max‖F‖ ≤ 10⁻³·min_edge` survives ONLY
  as the initial trial-scale guard inside the backtracking search. It does
  NOT imply monotone descent — a bound on how far a step moves says
  nothing about which way it moves. The guarantee of descent is the
  acceptance test (a)+(b).
- **Termination (all named):** `converged` (displacement ≤ 10⁻¹²·scene_scale
  OR actual step decrease ≤ 8·e·max(U,1) — machine-precision stagnation),
  `step_limit_reached`, `no_descent_step`, `invalid_surface` (the
  reference's own reason, passed through).
- **Scope separation:** this is an OPTIMIZATION experiment on
  U = Σ γₜAₜ. It predicts NOTHING about inertial dynamics — correction 3
  above stands unchanged.

The falsifier battery for this law is
`tools/overdamped_descent_checks.py` — 13 checks (G01-R4, 2026-09-07):
planar-patch stationarity, monotone descent to the discrete Plateau
minimum with area in [A_flat − 512·e, A_initial], zero-γ exact
stationarity, bit-exact pins, unsafe-trial rejection by the reference's
own reason, budget-exhaustion refusal, evidence-preservation regression
against the real runner, two-unit equivalence (wu vs cm, explicit
conversion), residual-based stationary recognition with reaction-force
reporting, zero-γ safe return, tiny-step-never-stationary,
backtracking-exhaustion geometry invariance, and post-hoc Armijo
verification of the full step trail. Certified 13/13 (R4 run;
7/7 in the R3 run it superseded). Results in the R3/R4 raw records.
**Initial conditions are stated per case.** For an inertial or
multi-force integrator, these tests are INVALID as written and must be
re-derived — no monotonicity or alignment claim transfers.

### Tier A — camera-independent numerical checks (run first)

Instruments: engine state readback only. **CAPABILITY GAP, named
honestly:** the engine currently exposes `/scene` (counts), `/cameras`,
`/camera`, `/frame` — it does NOT expose vertex-position or vertex-force
readback. Tier A requires the integrator to add a read-only position dump
(+ optionally per-vertex force readback) endpoint. Without it, Tier A is
BLOCKED — and Tier B must not then be claimed as verification. (Proposed
new read-only endpoint only; no engine change is made in this packet.)

**A1. Zero-γ identity in the engine.** With the surface-energy mode
enabled and γ ≡ 0 on every face, the reference's forces are EXACTLY zero
(F2-certified zero-γ law — not small, zero). **Falsifier (justified
bound): any per-vertex displacement from the captured rest state over 60
frames.** The bound is exact-zero because the forcing is exact-zero — any
motion falsifies the zero path (a force leaks) and needs no precision
budget to distinguish from rest. This replaces the earlier draft's "any
drift > 1 px" pixel bound, which measured the camera, not the physics.
(The earlier draft's case-1 premise — uniform γ producing "no motion" —
is also corrected: uniform γ on a curved closed surface genuinely
contracts it toward smaller area; only γ ≡ 0 is a rest state.)

**A2. Uniform-γ contraction, per-vertex direction (UNDER THE DECLARED
SCHEME, §6.0).** With uniform γ on the closed creature mesh, every vertex
ABOVE the A3 floor must move with a nonnegative component along its CPU
reference force at the captured position (the law is attractive — F5's
2γ/R is the aggregate signature), and total surface area (computed from
positions — no camera) must decrease on each step. **Scope: these are
quasi-static expectations only; an inertial integrator is neither bound by
nor claimed to satisfy them (§6.0 item 3).** Falsifier: any above-floor
vertex moving against its reference force, or any step increasing area.

**A3. Near-zero force rule (direction is undefined there).** A vertex
whose reference force satisfies ‖F‖ ≤ 3·d·ε_f64·S_max ≈ 4.0e-15 γ·wu
(the f64 single-pass accumulation bound, §2.5) is EXCLUDED from all
direction assertions; only its position consistency is checked. The
floor is precision-derived — not "any nonzero force" — because below it
the direction is rounding noise, and a direction test on rounding noise
is a random verdict generator.

### Tier B — pixel-based visual tests (only after Tier A passes)

**State identifiers** (all read-only instruments the engine already
exposes):

- `GET /scene` — rows `body` (tris count), `show` (t=), `joints` (28)
- `GET /cameras` — bookmark state (the fit bookmark is the framing control)
- `POST /cameras {"op":"fit"}` — camera-only motion control (no sim state)
- `POST /camera {"cam_radius","cam_theta","cam_phi"}` — the ingest the
  G01-CAMERA arc clamped (CAM_PHI_BAND); the experiment must respect the
  band (phi ∈ [−1.5533, 1.5533]) and must not POST phi outside it
- `GET /frame` — ordered capture instrument

**Expected behavior to look for** (per law, each falsifiable):

1. **Echo of A1** (zero-γ): no visible motion between frames. Falsifier:
   any visible inter-frame deformation. (Justified by A1's exact-zero
   forcing; the pixel test is an accessibility echo of the numerical
   gate, never its substitute.)
2. **Paint boundary** (spatial γ: 0 inside a disk, γ₀ outside, ON A
   PLANAR PATCH — the declared assumption, §6.0 item 2): forces appear
   ONLY at the paint boundary — interior surfaces of a planar constant-γ
   region have no energy gradient. **On curved regions this expectation
   does NOT hold: interior forces are generically nonzero there.**
   Falsifier (numerical, Tier A form): interior vertices of the PLANAR
   patch displace; (pixel echo): visible interior deformation on the
   planar patch.
3. **Restoring pull** (single outward vertex displacement via the
   skinning path; initial condition = rest pose plus that one
   displacement, zero velocity — quasi-static, §6.0): under the declared
   scheme the displaced vertex steps in the area-DESCENT direction — its
   first-step displacement has a positive component along −grad U
   (equivalently, along the reference force) at its position, and total
   area decreases on the first step. **NO claim of return to the imported
   pose: constant-γ energy has no rest shape (§6.0 item 1) — the surface
   shrinks toward smaller area, it does not remember where it was.**
   Direction test near-zero rule: vertices (or frames) whose reference
   force magnitude is below the A3 floor are excluded — direction is
   undefined there. Falsifier (above the floor): first-step direction
   deviates > 5° from the precomputed arrow, or the first step increases
   area.

**Controls**: run each case with γ = 0 (must be exactly no-op), with the
mode disabled (no-op), and with the reference CPU evaluation run on the
captured live positions as the expected-value generator.

**Camera-only motion rule**: the only POSTs that move anything are camera
ingests; pose/γ state changes are POSTs to their own endpoints and each
case restores prior state (the probe-temp-bookmark pattern from the G01
session is the model: save → act → restore → delete).

**Ordered captures**: case 0 baseline, case 1 rest identity (3 frames,
60 frames apart), case 2 paint boundary (2 frames at paint on/off), case 3
restoring pull (6 frames across the pull). Each capture names the case,
frame index, and the state hash of `/scene` at grab time.

**Questions for the local DYAD** (one picture per report, the standing
law): "Does the surface deform between frame A and frame B?" (case 1: the
correct answer is NO); "Where does motion appear — boundary or interior?"
(case 2: boundary only); "Does the marked vertex move toward or against
the drawn arrow?" (case 3: toward). The DYAD's verdicts are recorded
verbatim; they are visual evidence, distinct from the numerical evidence
preserved in `agent_logs/glm_foundation_g01/` (review copies:
`docs/evidence/g01/`).

## 7. What this handoff does NOT claim

- No engine integration was performed (isolation rule).
- No GPU code was written (task 17 is a layout document).
- No visual/DYAD verification exists or is claimed (task 19 is a proposal).
- The CPU implementation is the NUMERICAL REFERENCE (§1 correction), not a
  bit-exact oracle: bit equality with any GPU pass is neither proposed nor
  required; agreement is by the tier-declared §2.5 tolerances.
- The §2.5 tolerances and the §6 ladder bounds are PROPOSALS — unverified
  on any device; the integrator measures and records actual margins.
- The numerical certification (8/8 + 10/10) is CPU-numpy truth about the
  reference and the contract; it certifies the LAWS, not any future GPU
  transcription of them. The F8 lesson is recorded for exactly that risk.
