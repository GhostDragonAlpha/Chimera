# GPU_HANDOFF.md — taking the CPU-reference membrane law to the renderer's compute path

Status: PROPOSAL. The GPU stages here are NOT implemented. This document is the acceptance
contract ANY implementation must satisfy before it is allowed to replace (or claim to have
replaced) the CPU reference. Written 2026-09-08. Append-only: amend, never rewrite.

Source of truth (all three live, cited, and falsified):
- law derivation: `docs/evidence/elastic_foundation/DERIVATION.md` (esp. §11 Amendment — the
  sheet-level pullback frame; §12 Amendment — unit handling)
- falsifier registry: `docs/evidence/elastic_foundation/PREREGISTRATION.md`
- CPU implementation: `tools/elastic_foundation/law.py`, `geometry.py`, `materials.py`

## 1. Scope

Stage this in exactly three steps. A step is "done" only when the acceptance run in §5
passes for that step's outputs.

- **Stage A — per-face physics (mapped over faces, embarrassingly parallel):** given rest and
  current positions and the frozen material, compute per-face: strain tensors, Wbar, the three
  face-corner force vectors, and the face energy. No cross-face communication.
- **Stage B — CSR gather (one-thread-per-vertex):** sum the per-face corner forces into vertex
  forces using the FROZEN CSR layout from the fixture.
- **Stage C — acceptance:** compare GPU results against the fixture's CPU reference inside the
  float32 acceptance band (§5). Nothing downstream (the renderer's cloth solve, the gradient)
  is allowed to bypass Stage C — compare, THEN use.

Refusals must propagate on-device flags: nonfinite input, collapsed/near-degenerate current
triangle, nonfinite result. Do NOT silently clamp. The CPU reference refuses; the GPU must
refuse the same conditions (see §4 flags).

## 2. The math (float32 pipeline, deterministic)

Per face `f`, read the REST frame data from the fixtures (`rest_B_f32`, `rest_n`,
`rest_areas0_f32`, and `rest_t1`/`rest_t2` if needed for reconstruction). All tensor work in
float32. Exactly this sequence, from `law.py` lines 97–159:

    d1 = y[v1] - y[v0]                  # current edges (3,)
    d2 = y[v2] - y[v0]
    cross = cross(d1, d2)               # 3D cross product
    N   = [d1 d2]                       # (3,2) current edge matrix
    F   = N @ B_f                       # (3,2) in-plane deformation gradient
    C   = F^T F                         # (2,2) right Cauchy-Green  (F^T F, NOT F F^T)
    E   = 0.5 (C - I)                   # (2,2) Green-Lagrange      (NOT the linear strain)
    trE   = E[0,0] + E[1,1]
    trE2  = E[0,0]^2 + 2 E[0,1]^2 + E[1,1]^2
    Wbar  = 0.5 lam trE^2 + mu trE2     # energy per reference area
    S[0,0] = lam trE + 2 mu E[0,0]
    S[1,1] = lam trE + 2 mu E[1,1]
    S[0,1] = 2 mu E[0,1]   S[1,0] = S[0,1]
    P    = F @ S                        # (3,2) PK1 per reference area
    PBt  = P @ B_f^T                    # columns u1,u2 = dWbar/d(d1), dWbar/d(d2)
    u1 = PBt[:,0]   u2 = PBt[:,1]
    A0  = rest_areas0[f]
    f0  = A0 (u1 + u2)                  # force ON corner 0 = -dU/dy
    f1  = A0 (-u1)                      # force ON corner 1
    f2  = A0 (-u2)                      # force ON corner 2
    E_face = Wbar * A0

Invariance this law OWNS (already falsified on CPU): energy is a function of `C = F^T F`
(rotation-objective in world space), `E = (C - I)/2` (Green–Lagrange, quadratic strain), and
`U = A0 · Wbar`. Any GPU kernel that substitutes `C = F F^T` (eulerian/metric), linear strain,
or current-area weighting is implementing a DIFFERENT law and will fail the fixtures.

### Bare triangle convention

The law is tested against a single non-aligned triangle fixture (`trisingle_stretch.npz`). The
3D deformation gradient `F` has an out-of-plane column that is not needed: only the in-plane
2x2 part enters `C`; the frame supplies the plane. Do not try to invert the 3x2 rest edge
matrix yourself — the pullback `B` is frozen into the fixture (this dodges the gauge: a single
safe (Moore-Penrose) inverse is precomputed on the CPU using the sheet frame, rest-derived and
co-rotating, DERIVATION.md §11).

### Energy budget note

`Wbar` is per reference area; energy `E_face = A0 · Wbar`. `h` (thickness) appears ONLY in
`w_vol = Wbar/h` (diagnostic) and in the material moduli (plane-stress, implicit unit
thickness, DERIVATION.md §12). Do NOT multiply `E_face` by `h`.

## 3. Data layout (exactly the fixture arrays)

Read `fixtures/v1/<latest run>/`
- `rest_pos`  (nV,3) f32, `cur_pos` (nV,3) f32 — the ONLY position inputs (frozen)
- `faces_int32` (nF,3) i32 — corner vertex indices
- `rest_B_f32` (nF,3,2) f32 — rest pullback matrix (sheet frame), precomputed
- `rest_areas0_f32` (nF,) f32, `rest_n` (nF,3) f32, `rest_t1`/`rest_t2` (nF,3) f32 frame
- `lambda/mu` are YOUR material constants: use `E_f64`, `nu_f64` then form
  `lam = E·nu/(1-nu²)`, `mu = E/(2(1+nu))` in f32 (the precise double moduli are in the
  manifest; the reference answered with the doubles). Failing to convert per these formulas is
  a parameter-level deviation the fixtures will catch.
- `exp_energy_f64`, `exp_corner_f64`, `exp_vertex_f64` — CPU reference answers (from the
  float32 input stream, evaluated in float64), stored as float64 for exactness. Compare AFTER
  truncating them to float32 when the GPU is float32 (tolerance in §5).

Stage B then uses `csr_offsets_u32` (nV+1) and `csr_corners_u32` (3 nF,) — the FROZEN CSR
layout of corner forces at vertex indices. The CPU gather is `np.add.reduceat(flat[csr_corners],
offsets[:-1])`; the GPU must reproduce it as an atomic-less segmented reduction (vertex owning
threads, order-independent sum; float32 atomic order varies, so a per-vertex fixed accumulation
order matching CPU is strongly preferred for deterministic comparisons).

## 4. Flags (never silent)

Mirror the CPU named refusals in `law.py` `DeformationReason`:
```
WRONG_VERTEX_COUNT     y has != nV rows
NONFINITE_POSITIONS    any position inf/nan
COLLAPSED_TRIANGLE     |cross(d1,d2)| <= floor
NEAR_DEGENERATE_TRIANGLE  |cross| <= floor but > 0
NONFINITE_RESULT       any tensor out non-finite
```
Degeneracy floor (geometry.py): `floor = DEGENERACY_FLOOR_FACTOR * EPS64 * max_edge^2` with
`DEGENERACY_FLOOR_FACTOR` and `EPS64` from `geometry.py` (make the constants compile-time).

## 5. Acceptance (Stage C) — the ONLY way to call a GPU kernel done

Run against BOTH fixtures (`trisingle_stretch`, `patch_8x4_shear`) in the latest frozen run.
Accept iff, for each fixture, with `TOL = 2.0 u1p f32` (≈ 2.384e-7 relative):

```
|E_gpu - E_ref|             <= TOL * E_ref
|vertex_forces_gpu - f_ref| <= TOL * max(|f_ref|)      (max over vertices, per component abs)
corner_forces_gpu           consistent: each per-face corner force re-gathers to the
                            vertex forces via the CSR layout (self-check on device)
flags == CPU flags          (no refusal enumeration mismatch)
     # AND the existing CPU battery still passes after the GPU change:
python -m tools.elastic_foundation.run_falsify --suffix gpu_accept_<date>
```

`patch_8x4_shear` covers the CSR gather path and a multi-vertex sheet; `trisingle_stretch`
covers the bare triangle path. Do not ship a kernel that passes the triangle and not the patch —
the gather is the easy place to get determinism wrong.

## 6. Recommended kernel sketch (informational, not binding)

- Stage A: 1 thread per face. Vectorize the 3x2/2x2 ops as f32x4 where the layout allows.
- Stage B: 1 thread per vertex; iterate its corners (the CSR is contiguous per vertex), sum in
  FIXED corner order (the order `csr_corners` lists them). Prefer fixed-order over atomics.
- Stage C: a single kernel or CPU-side check script comparing the two float32 arrays; the
  tolerances above.

## 7. What is deliberately NOT in the handoff yet

- bending energy, per-vertex normals, higher-order elements
- a GPU solver (gradient descent / conjugate-gradient, `optimizers.py`), gravity/viscosity
  coupling, collision
- per-vertex material variation, anisotropy

All of the above are `WHAT_COMES_NEXT.md` items and MUST re-run the Stage C acceptance against a
NEW fixture set (the current fixtures freeze only this law's nominal inputs).